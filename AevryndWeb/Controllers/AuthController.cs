using System.Security.Claims;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[ApiController]
public sealed class AuthController(IOtpService otp, IEmailSender emailSender, IAntiforgery antiforgery, IPortalSessionStore sessions, IRemoteControlGrantService remoteGrants, IRemoteControlLeaseRegistry leases) : ControllerBase
{
    [HttpGet("/api/auth/csrf"), AllowAnonymous, IgnoreAntiforgeryToken]
    public object Csrf() => new { token = antiforgery.GetAndStoreTokens(HttpContext).RequestToken };

    [HttpPost("/api/auth/request-code"), AllowAnonymous]
    public async Task<IActionResult> RequestCode([FromBody] EmailRequest request, CancellationToken cancellationToken)
    {
        try { await otp.RequestAsync(request.Email ?? string.Empty, ClientKey(), cancellationToken); } catch (OtpRejectedException) { } catch (InvalidOperationException) { }
        return Ok(new { message = "若此信箱可使用，驗證碼將會寄出。", retryAfterSeconds = 60 });
    }

    [HttpPost("/api/auth/verify"), AllowAnonymous]
    public async Task<IActionResult> Verify([FromBody] VerifyRequest request)
    {
        if (!otp.Verify(request.Email ?? string.Empty, request.Code ?? string.Empty, ClientKey())) return Unauthorized(new { message = "驗證資訊不正確或已失效。" });
        var now = DateTimeOffset.UtcNow;
        var email = request.Email?.Trim().ToLowerInvariant() ?? string.Empty;
        var role = PortalIdentity.RoleFor(email);
        if (role is null) return Unauthorized(new { message = "驗證資訊不正確或已失效。" });
        var session = sessions.Create(email, now);
        var identity = new ClaimsIdentity(
        [
            new Claim(ClaimTypes.NameIdentifier, email),
            new Claim(ClaimTypes.Email, email),
            new Claim(ClaimTypes.Role, role),
            new Claim(PortalClaimTypes.SessionId, session.Id),
            new Claim(PortalClaimTypes.SecurityStamp, session.SecurityStamp),
            new Claim(PortalClaimTypes.AuthenticationTime, now.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture))
        ], CookieAuthenticationDefaults.AuthenticationScheme);
        await HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, new ClaimsPrincipal(identity), new AuthenticationProperties { ExpiresUtc = session.ExpiresAt, AllowRefresh = false, IsPersistent = false });
        return Ok(new { redirect = "/Home/Portal" });
    }

    [HttpPost("/api/auth/logout"), Authorize]
    public async Task<IActionResult> Logout()
    {
        var sessionId = User.FindFirstValue(PortalClaimTypes.SessionId);
        if (sessionId is not null) leases.Release(sessionId);
        remoteGrants.Revoke(sessionId);
        sessions.Revoke(sessionId);
        await HttpContext.SignOutAsync();
        return Ok();
    }
    [HttpGet("/health/ready"), AllowAnonymous, IgnoreAntiforgeryToken]
    public IActionResult Ready() => Ok(new { status = "ok", emailReady = emailSender.IsReady });
    private string ClientKey() => HttpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown";
    public sealed record EmailRequest(string? Email);
    public sealed record VerifyRequest(string? Email, string? Code);
}
