using System.Security.Claims;
using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class SecurityStateTests
{
    [Fact]
    public void PortalSessionRequiresExactEmailStampAndAuthenticationTime()
    {
        var store = new PortalSessionStore(); var now = DateTimeOffset.FromUnixTimeSeconds(1_800_000_000); var session = store.Create(PortalIdentity.AllowedEmail, now);
        var valid = Principal(session.Id, session.SecurityStamp, PortalIdentity.AllowedEmail, now);
        Assert.True(store.Validate(valid, now.AddMinutes(1)));
        Assert.False(store.Validate(Principal(session.Id, "wrong", PortalIdentity.AllowedEmail, now), now));
        Assert.False(store.Validate(Principal(session.Id, session.SecurityStamp, "other@example.com", now), now));
        Assert.False(store.Validate(Principal(session.Id, session.SecurityStamp, PortalIdentity.AllowedEmail, now.AddSeconds(1)), now));
        store.Revoke(session.Id); Assert.False(store.Validate(valid, now));
    }

    [Fact]
    public async Task RemoteGrantIsOneTimeCapabilityBoundAndIdleLimited()
    {
        var sender = new CapturingEmailSender(); var guard = new GrantGuard(); var desktop = new FakeDesktop(); var service = new RemoteControlGrantService(sender, guard, desktop, new RemoteControlLeaseRegistry());
        var now = DateTimeOffset.FromUnixTimeSeconds(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        await service.RequestAsync("session", "pair-once", CancellationToken.None);
        var grant = service.VerifyAndActivate("session", sender.Code!, now);
        Assert.NotNull(grant); Assert.True(guard.Consumed); Assert.Contains(RemoteCapability.Screen, grant!.Capabilities);
        Assert.Equal(now.AddHours(8), grant.ExpiresAt);
        var principal = RemotePrincipal(grant);
        Assert.True(service.Validate(principal, RemoteCapability.Screen, now.AddMinutes(1)));
        Assert.False(service.Validate(principal, RemoteCapability.Keyboard, now.AddMinutes(1)));
        Assert.True(service.TouchSuccessfulAction(principal, now.AddMinutes(1)));
        Assert.True(service.Validate(principal, RemoteCapability.Screen, now.AddMinutes(30)));
        Assert.False(service.Validate(principal, RemoteCapability.Screen, now.AddMinutes(31).AddSeconds(1)));
        Assert.Contains("session", desktop.ReleasedSessions);
        await Assert.ThrowsAsync<OtpRejectedException>(() => service.RequestAsync("another", "pair-once", CancellationToken.None));
    }

    [Fact]
    public async Task LeaseHeartbeatDoesNotExtendIdleDeadline()
    {
        var sender = new CapturingEmailSender(); var service = new RemoteControlGrantService(sender, new GrantGuard(), new FakeDesktop(), new RemoteControlLeaseRegistry());
        var now = DateTimeOffset.FromUnixTimeSeconds(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        await service.RequestAsync("session", "pair-once", CancellationToken.None);
        var grant = service.VerifyAndActivate("session", sender.Code!, now)!;
        var principal = RemotePrincipal(grant);

        Assert.True(service.ValidateLease(principal, now.AddMinutes(29).AddSeconds(59)));
        Assert.True(service.Validate(principal, RemoteCapability.Screen, now.AddMinutes(29).AddSeconds(59)));
        Assert.False(service.ValidateLease(principal, now.AddMinutes(30).AddSeconds(1)));
    }

    [Fact]
    public void FrameLimitIsGlobalAcrossSessions()
    {
        var limiter = new RemoteConsoleRateLimiter(); var now = DateTimeOffset.UtcNow;
        Assert.True(limiter.AllowFrame("session-a", now, out _));
        Assert.False(limiter.AllowFrame("session-b", now, out var retryAfter));
        Assert.True(retryAfter >= TimeSpan.FromMilliseconds(1490));
    }

    [Fact]
    public void ControlLeaseAllowsOnlyOneLiveConnectionGlobally()
    {
        var leases = new RemoteControlLeaseRegistry();
        Assert.True(leases.TryAcquire("session")); Assert.False(leases.TryAcquire("session")); Assert.False(leases.TryAcquire("other-session"));
        Assert.True(leases.IsActive("session")); Assert.False(leases.IsActive("other-session"));
        leases.Release("session"); Assert.False(leases.IsActive("session"));
    }

    private static ClaimsPrincipal Principal(string id, string stamp, string email, DateTimeOffset authTime) => new(new ClaimsIdentity([
        new Claim(ClaimTypes.Email, email), new Claim(PortalClaimTypes.SessionId, id), new Claim(PortalClaimTypes.SecurityStamp, stamp),
        new Claim(PortalClaimTypes.AuthenticationTime, authTime.ToUnixTimeSeconds().ToString())], "Test"));
    private static ClaimsPrincipal RemotePrincipal(RemoteControlGrant grant) => new(new ClaimsIdentity([
        new Claim(PortalClaimTypes.SessionId, grant.SessionId), new Claim(PortalClaimTypes.RemoteControl, "true"),
        new Claim(PortalClaimTypes.RemoteNonce, grant.Nonce), new Claim(PortalClaimTypes.RemoteAuthenticationTime, grant.AuthenticatedAt.ToUnixTimeSeconds().ToString())], "Test"));

    private sealed class CapturingEmailSender : IEmailSender
    {
        public bool IsReady => true; public string? Code { get; private set; }
        public Task SendAsync(string recipient, string code, CancellationToken cancellationToken) { Code = code; return Task.CompletedTask; }
    }
    private sealed class GrantGuard : IRemoteConsoleGuard
    {
        public bool Consumed { get; private set; }
        private readonly RemoteConsoleEnablement state = new(new string('B', 64), DateTimeOffset.UtcNow.AddHours(9), new HashSet<RemoteCapability> { RemoteCapability.Screen, RemoteCapability.Text }, new string('0', 64), false);
        public bool TryRead(DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = state; return true; }
        public bool VerifyPairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = state; return !Consumed && nonce == "pair-once"; }
        public bool ConsumePairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = state; if (Consumed || nonce != "pair-once") return false; Consumed = true; return true; }
        public void ResetOnStartup() { }
    }
}
