using System.Collections.Concurrent;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authorization;

namespace AevryndWeb.Security;

public static class PortalClaimTypes
{
    public const string SessionId = "aevrynd:session_id";
    public const string SecurityStamp = "aevrynd:security_stamp";
    public const string AuthenticationTime = "auth_time";
    public const string RemoteControl = "remote_control";
    public const string RemoteNonce = "aevrynd:remote_nonce";
    public const string RemoteAuthenticationTime = "aevrynd:remote_auth_time";
}

public interface IPortalSessionStore
{
    PortalSession Create(string email, DateTimeOffset now);
    bool Validate(ClaimsPrincipal user, DateTimeOffset now);
    void Revoke(string? sessionId);
}

public sealed record PortalSession(string Id, string SecurityStamp, string Email, DateTimeOffset AuthenticatedAt, DateTimeOffset ExpiresAt);

public sealed class PortalSessionStore : IPortalSessionStore
{
    private static readonly TimeSpan Lifetime = TimeSpan.FromHours(8);
    private readonly ConcurrentDictionary<string, PortalSession> sessions = new();

    public PortalSession Create(string email, DateTimeOffset now)
    {
        now = DateTimeOffset.FromUnixTimeSeconds(now.ToUnixTimeSeconds());
        Prune(now);
        var session = new PortalSession(Token(24), Token(32), email, now, now.Add(Lifetime));
        sessions[session.Id] = session;
        return session;
    }

    public bool Validate(ClaimsPrincipal user, DateTimeOffset now)
    {
        var id = user.FindFirstValue(PortalClaimTypes.SessionId);
        var stamp = user.FindFirstValue(PortalClaimTypes.SecurityStamp);
        var email = user.FindFirstValue(ClaimTypes.Email);
        var authTime = user.FindFirstValue(PortalClaimTypes.AuthenticationTime);
        if (id is null || stamp is null || email is null || authTime is null || !sessions.TryGetValue(id, out var session)) return false;
        if (session.ExpiresAt <= now) { sessions.TryRemove(id, out _); return false; }
        return Exact(email, session.Email) && Exact(stamp, session.SecurityStamp) &&
            long.TryParse(authTime, out var seconds) && seconds is >= -62135596800 and <= 253402300799 && DateTimeOffset.FromUnixTimeSeconds(seconds) == session.AuthenticatedAt;
    }

    public void Revoke(string? sessionId)
    {
        if (!string.IsNullOrEmpty(sessionId)) sessions.TryRemove(sessionId, out _);
    }

    private void Prune(DateTimeOffset now)
    {
        foreach (var item in sessions)
            if (item.Value.ExpiresAt <= now) sessions.TryRemove(item.Key, out _);
    }

    private static bool Exact(string left, string right) => CryptographicOperations.FixedTimeEquals(Encoding.UTF8.GetBytes(left), Encoding.UTF8.GetBytes(right));
    private static string Token(int bytes) => Convert.ToHexString(RandomNumberGenerator.GetBytes(bytes));
}

public sealed class PortalOwnerRequirement : IAuthorizationRequirement;

public sealed class PortalOwnerAuthorizationHandler(IPortalSessionStore sessions) : AuthorizationHandler<PortalOwnerRequirement>
{
    protected override Task HandleRequirementAsync(AuthorizationHandlerContext context, PortalOwnerRequirement requirement)
    {
        if (context.User.Identity?.IsAuthenticated == true && sessions.Validate(context.User, DateTimeOffset.UtcNow)) context.Succeed(requirement);
        return Task.CompletedTask;
    }
}
