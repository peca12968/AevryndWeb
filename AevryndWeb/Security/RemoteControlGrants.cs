using System.Collections.Concurrent;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authorization;

namespace AevryndWeb.Security;

public interface IRemoteControlGrantService
{
    Task RequestAsync(string sessionId, string pairingNonce, CancellationToken cancellationToken);
    RemoteControlGrant? VerifyAndActivate(string sessionId, string code, DateTimeOffset now);
    bool Validate(ClaimsPrincipal user, RemoteCapability capability, DateTimeOffset now);
    bool IsActive(ClaimsPrincipal user, DateTimeOffset now);
    RemoteControlGrantStatus? GetStatus(ClaimsPrincipal user, DateTimeOffset now);
    bool ValidateLease(ClaimsPrincipal user, DateTimeOffset now);
    bool TouchSuccessfulAction(ClaimsPrincipal user, DateTimeOffset now);
    void Revoke(string? sessionId);
    void RevokeAll();
    IReadOnlyList<string> RevokeExpired(DateTimeOffset now);
}

public sealed record RemoteControlGrant(string SessionId, string Nonce, string ActivationId, DateTimeOffset AuthenticatedAt, DateTimeOffset ExpiresAt, IReadOnlySet<RemoteCapability> Capabilities);
public sealed record RemoteControlGrantStatus(DateTimeOffset ExpiresAt, DateTimeOffset IdleExpiresAt, IReadOnlySet<RemoteCapability> Capabilities);

public sealed class RemoteControlGrantService(IEmailSender sender, IRemoteConsoleGuard guard, IRemoteDesktopService desktop, IRemoteControlLeaseRegistry leases) : IRemoteControlGrantService
{
    private static readonly TimeSpan ChallengeLifetime = TimeSpan.FromMinutes(5);
    private static readonly TimeSpan GrantLifetime = TimeSpan.FromMinutes(10);
    private static readonly TimeSpan IdleLifetime = TimeSpan.FromMinutes(2);
    private const string Alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    private readonly ConcurrentDictionary<string, Challenge> challenges = new();
    private readonly ConcurrentDictionary<string, ActiveGrant> grants = new();
    private readonly ConcurrentDictionary<string, DateTimeOffset> cooldowns = new();
    private readonly object activationLock = new();

    public async Task RequestAsync(string sessionId, string pairingNonce, CancellationToken cancellationToken)
    {
        var now = DateTimeOffset.UtcNow;
        if (!guard.VerifyPairingNonce(pairingNonce, now, out _)) throw new OtpRejectedException();
        if (cooldowns.TryGetValue(sessionId, out var next) && next > now) throw new OtpRejectedException();
        cooldowns[sessionId] = now.AddSeconds(60);
        var code = string.Create(8, 0, (span, _) => { for (var index = 0; index < span.Length; index++) span[index] = Alphabet[RandomNumberGenerator.GetInt32(Alphabet.Length)]; });
        var salt = RandomNumberGenerator.GetBytes(16);
        challenges[sessionId] = new Challenge(salt, Rfc2898DeriveBytes.Pbkdf2(code, salt, 120_000, HashAlgorithmName.SHA256, 32), now.Add(ChallengeLifetime), 0, pairingNonce);
        try { await sender.SendAsync(PortalIdentity.AllowedEmail, code, cancellationToken); }
        catch { challenges.TryRemove(sessionId, out _); throw; }
    }

    public RemoteControlGrant? VerifyAndActivate(string sessionId, string code, DateTimeOffset now)
    {
        now = DateTimeOffset.FromUnixTimeSeconds(now.ToUnixTimeSeconds());
        if (code.Length != 8 || !challenges.TryGetValue(sessionId, out var challenge)) return null;
        if (challenge.ExpiresAt <= now || challenge.Attempts >= 5) { challenges.TryRemove(sessionId, out _); return null; }
        var actual = Rfc2898DeriveBytes.Pbkdf2(code.ToUpperInvariant(), challenge.Salt, 120_000, HashAlgorithmName.SHA256, 32);
        if (!CryptographicOperations.FixedTimeEquals(actual, challenge.Hash))
        {
            var updated = challenge with { Attempts = challenge.Attempts + 1 };
            if (updated.Attempts >= 5) challenges.TryRemove(sessionId, out _); else challenges[sessionId] = updated;
            return null;
        }

        if (!challenges.TryRemove(sessionId, out _) || !guard.ConsumePairingNonce(challenge.PairingNonce, now, out var enablement)) return null;
        var grant = new RemoteControlGrant(sessionId, Convert.ToHexString(RandomNumberGenerator.GetBytes(32)), enablement.ActivationId, now,
            Min(now.Add(GrantLifetime), enablement.EnabledUntilUtc), enablement.Capabilities);
        lock (activationLock)
        {
            foreach (var existing in grants.Keys)
                if (grants.TryRemove(existing, out _)) { leases.Release(existing); desktop.ReleaseInjectedModifiers(existing); }
            grants[sessionId] = new ActiveGrant(grant, now.Add(IdleLifetime));
            return grant;
        }
    }

    public bool Validate(ClaimsPrincipal user, RemoteCapability capability, DateTimeOffset now)
    {
        if (!TryValidate(user, now, out var sessionId, out var active)) return false;
        if (!guard.TryRead(now, out var enablement) || !Exact(active.Grant.ActivationId, enablement.ActivationId)) { Revoke(sessionId); return false; }
        if (!active.Grant.Capabilities.Contains(capability)) return false;
        if (capability == RemoteCapability.Shell && now - active.Grant.AuthenticatedAt > TimeSpan.FromMinutes(5)) return false;
        return true;
    }

    public bool IsActive(ClaimsPrincipal user, DateTimeOffset now)
    {
        if (!TryValidate(user, now, out var sessionId, out var active)) return false;
        if (!guard.TryRead(now, out var enablement) || !Exact(active.Grant.ActivationId, enablement.ActivationId)) { Revoke(sessionId); return false; }
        return true;
    }

    public RemoteControlGrantStatus? GetStatus(ClaimsPrincipal user, DateTimeOffset now)
    {
        if (!IsActive(user, now) || !TryValidate(user, now, out _, out var active)) return null;
        return new(active.Grant.ExpiresAt, active.IdleExpiresAt, active.Grant.Capabilities);
    }

    public bool ValidateLease(ClaimsPrincipal user, DateTimeOffset now)
    {
        if (!TryValidate(user, now, out var sessionId, out var active)) return false;
        if (!guard.TryRead(now, out var enablement) || !Exact(active.Grant.ActivationId, enablement.ActivationId)) { Revoke(sessionId); return false; }
        return true;
    }

    public bool TouchSuccessfulAction(ClaimsPrincipal user, DateTimeOffset now)
    {
        if (!TryValidate(user, now, out var sessionId, out var active)) return false;
        if (!guard.TryRead(now, out var enablement) || !Exact(active.Grant.ActivationId, enablement.ActivationId)) { Revoke(sessionId); return false; }
        return grants.TryUpdate(sessionId, active with { IdleExpiresAt = Min(active.Grant.ExpiresAt, now.Add(IdleLifetime)) }, active);
    }

    public void Revoke(string? sessionId)
    {
        if (string.IsNullOrEmpty(sessionId)) return;
        challenges.TryRemove(sessionId, out _);
        if (grants.TryRemove(sessionId, out _)) { leases.Release(sessionId); desktop.ReleaseInjectedModifiers(sessionId); }
        cooldowns.TryRemove(sessionId, out _);
    }

    public void RevokeAll()
    {
        foreach (var sessionId in grants.Keys) Revoke(sessionId);
        challenges.Clear(); cooldowns.Clear();
    }

    public IReadOnlyList<string> RevokeExpired(DateTimeOffset now)
    {
        var revoked = new List<string>();
        foreach (var item in grants)
            if ((item.Value.Grant.ExpiresAt <= now || item.Value.IdleExpiresAt <= now) && grants.TryRemove(item.Key, out _)) { revoked.Add(item.Key); desktop.ReleaseInjectedModifiers(item.Key); }
        foreach (var item in challenges)
            if (item.Value.ExpiresAt <= now) challenges.TryRemove(item.Key, out _);
        return revoked;
    }

    private bool TryValidate(ClaimsPrincipal user, DateTimeOffset now, out string sessionId, out ActiveGrant active)
    {
        active = null!;
        sessionId = user.FindFirstValue(PortalClaimTypes.SessionId) ?? string.Empty;
        var nonce = user.FindFirstValue(PortalClaimTypes.RemoteNonce);
        var grantClaim = user.FindFirstValue(PortalClaimTypes.RemoteControl);
        var authTime = user.FindFirstValue(PortalClaimTypes.RemoteAuthenticationTime);
        if (sessionId.Length == 0 || nonce is null || grantClaim != "true" || authTime is null || !grants.TryGetValue(sessionId, out var found)) return false;
        active = found;
        if (active.Grant.ExpiresAt <= now || active.IdleExpiresAt <= now) { Revoke(sessionId); return false; }
        return Exact(nonce, active.Grant.Nonce) && long.TryParse(authTime, out var seconds) && seconds is >= -62135596800 and <= 253402300799 && DateTimeOffset.FromUnixTimeSeconds(seconds) == active.Grant.AuthenticatedAt;
    }

    private static DateTimeOffset Min(DateTimeOffset left, DateTimeOffset right) => left <= right ? left : right;
    private static bool Exact(string left, string right) => CryptographicOperations.FixedTimeEquals(Encoding.UTF8.GetBytes(left), Encoding.UTF8.GetBytes(right));
    private sealed record Challenge(byte[] Salt, byte[] Hash, DateTimeOffset ExpiresAt, int Attempts, string PairingNonce);
    private sealed record ActiveGrant(RemoteControlGrant Grant, DateTimeOffset IdleExpiresAt);
}

public sealed record RemoteControlRequirement(RemoteCapability Capability) : IAuthorizationRequirement;

public sealed class RemoteControlAuthorizationHandler(
    IPortalSessionStore sessions,
    IRemoteControlGrantService grants,
    IRemoteConsoleGuard guard) : AuthorizationHandler<RemoteControlRequirement>
{
    protected override Task HandleRequirementAsync(AuthorizationHandlerContext context, RemoteControlRequirement requirement)
    {
        if (context.User.Identity?.IsAuthenticated == true && sessions.Validate(context.User, DateTimeOffset.UtcNow) &&
            guard.TryRead(DateTimeOffset.UtcNow, out var enablement) && enablement.Capabilities.Contains(requirement.Capability) &&
            grants.Validate(context.User, requirement.Capability, DateTimeOffset.UtcNow)) context.Succeed(requirement);
        return Task.CompletedTask;
    }
}

public sealed class RemoteControlRevocationMonitor(
    IRemoteConsoleGuard guard,
    IRemoteControlGrantService grants,
    IRemoteDesktopService desktop,
    IRemoteControlLeaseRegistry leases) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            if (!guard.TryRead(DateTimeOffset.UtcNow, out _)) { grants.RevokeAll(); leases.ReleaseAll(); desktop.ReleaseAllInjectedModifiers(); }
            foreach (var sessionId in grants.RevokeExpired(DateTimeOffset.UtcNow)) leases.Release(sessionId);
            desktop.RetryPendingReleases();
            await Task.Delay(TimeSpan.FromMilliseconds(500), stoppingToken);
        }
    }
}

public sealed class RemoteControlStartupReset(IRemoteConsoleGuard guard) : IHostedService
{
    public Task StartAsync(CancellationToken cancellationToken) { guard.ResetOnStartup(); return Task.CompletedTask; }
    public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;
}
