using System.Globalization;
using System.Security.Claims;
using System.Text;
using AevryndWeb.Models;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[Authorize(Policy = PortalIdentity.AdminPolicy)]
[Route("RemoteConsole")]
public sealed class RemoteConsoleController(
    IRemoteDesktopService desktop,
    IRemoteControlGrantService grants,
    IRemoteConsoleGuard guard,
    IRemoteConsoleRateLimiter rateLimiter,
    IRemoteControlLeaseRegistry leaseRegistry,
    IRemoteShellBroker shellBroker,
    IConfiguration configuration,
    ILogger<RemoteConsoleController> logger) : Controller
{
    private const int MaximumTextRunes = 256;
    private const int MaximumTextBytes = 1024;

    [HttpGet("")]
    public IActionResult Index()
    {
        var enabled = guard.TryRead(DateTimeOffset.UtcNow, out var enablement);
        var status = enabled ? grants.GetStatus(User, DateTimeOffset.UtcNow) : null;
        var active = status is not null;
        return View(new RemoteConsoleViewModel(enabled, active, enabled ? enablement.EnabledUntilUtc : null, status?.ExpiresAt,
            enabled ? enablement.Capabilities.Select(CapabilityName).ToArray() : [],
            enabled ? desktop.GetAvailability() : new(false, "本機遠端控制開關目前為關閉。")));
    }

    [HttpPost("request-code"), RequestSizeLimit(4096)]
    public async Task<IActionResult> RequestCode([FromBody] PairingRequest? request, CancellationToken cancellationToken)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        var sessionId = User.FindFirstValue(PortalClaimTypes.SessionId);
        if (sessionId is null) return Forbid();
        try { await grants.RequestAsync(sessionId, request?.PairingNonce ?? string.Empty, cancellationToken); }
        catch (Exception exception) when (exception is OtpRejectedException or InvalidOperationException) { }
        return Ok(new { message = "若本機配對有效，控制驗證碼將會寄出。" });
    }

    [HttpPost("verify-code"), RequestSizeLimit(4096)]
    public async Task<IActionResult> VerifyCode([FromBody] ControlVerifyRequest? request)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        var sessionId = User.FindFirstValue(PortalClaimTypes.SessionId);
        if (sessionId is null) return Forbid();
        var grant = grants.VerifyAndActivate(sessionId, request?.Code ?? string.Empty, DateTimeOffset.UtcNow);
        if (grant is null) return Unauthorized(new { message = "控制驗證資訊不正確、已失效或本機開關已關閉。" });
        var claims = User.Claims.Where(claim => claim.Type is not PortalClaimTypes.RemoteControl and not PortalClaimTypes.RemoteNonce and not PortalClaimTypes.RemoteAuthenticationTime).ToList();
        claims.Add(new Claim(PortalClaimTypes.RemoteControl, "true"));
        claims.Add(new Claim(PortalClaimTypes.RemoteNonce, grant.Nonce));
        claims.Add(new Claim(PortalClaimTypes.RemoteAuthenticationTime, grant.AuthenticatedAt.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture)));
        var authentication = await HttpContext.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        var properties = authentication.Properties ?? new AuthenticationProperties();
        properties.AllowRefresh = false;
        properties.IsPersistent = false;
        await HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, new ClaimsPrincipal(new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme)), properties);
        return Ok(new { message = "短效遠端控制授權已啟用。", expiresAt = grant.ExpiresAt, capabilities = grant.Capabilities.Select(CapabilityName) });
    }

    [HttpGet("frame"), Authorize(Policy = "RemoteConsole:Screen")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public async Task<IActionResult> Frame(CancellationToken cancellationToken)
    {
        SetNoCacheHeaders();
        if (!leaseRegistry.IsActive(ClientKey())) return StatusCode(409, new { message = "遠端工作階段連線不存在。" });
        if (!rateLimiter.AllowFrame(ClientKey(), DateTimeOffset.UtcNow, out var retryAfter)) return RateLimited(retryAfter);
        try
        {
            var result = await desktop.CaptureJpegAsync(cancellationToken);
            if (result.Jpeg.Length > 1_572_864) return StatusCode(503, new { message = "畫面目前無法使用。" });
            Response.Headers["X-Aevrynd-Frame-Generation"] = result.Generation.ToString(CultureInfo.InvariantCulture);
            Response.Headers["X-Aevrynd-Frame-Width"] = result.Width.ToString(CultureInfo.InvariantCulture);
            Response.Headers["X-Aevrynd-Frame-Height"] = result.Height.ToString(CultureInfo.InvariantCulture);
            logger.LogInformation("Remote screen capture accepted. TraceId={TraceId} Bytes={Bytes}", HttpContext.TraceIdentifier, result.Jpeg.Length);
            return File(result.Jpeg, "image/jpeg");
        }
        catch (RemoteDesktopUnavailableException)
        {
            logger.LogWarning("Remote screen capture unavailable. TraceId={TraceId}", HttpContext.TraceIdentifier);
            return StatusCode(503, new { message = "畫面目前無法使用。" });
        }
    }

    [HttpGet("lease")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public async Task Lease(CancellationToken cancellationToken)
    {
        SetNoCacheHeaders();
        var sessionId = ClientKey();
        if (!leaseRegistry.TryAcquire(sessionId)) { Response.StatusCode = StatusCodes.Status409Conflict; return; }
        try
        {
            if (!grants.ValidateLease(User, DateTimeOffset.UtcNow)) { Response.StatusCode = StatusCodes.Status403Forbidden; return; }
            Response.ContentType = "text/event-stream"; Response.Headers["X-Accel-Buffering"] = "no";
            while (!cancellationToken.IsCancellationRequested && grants.ValidateLease(User, DateTimeOffset.UtcNow))
            {
                await Response.WriteAsync("data: lease\n\n", cancellationToken);
                await Response.Body.FlushAsync(cancellationToken);
                await Task.Delay(TimeSpan.FromSeconds(15), cancellationToken);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { }
        finally { leaseRegistry.Release(sessionId); grants.Revoke(sessionId); }
    }

    [HttpPost("keyboard"), Authorize(Policy = "RemoteConsole:Keyboard"), RequestSizeLimit(4096)]
    public async Task<IActionResult> Keyboard([FromBody] KeyboardRequest? request, CancellationToken cancellationToken)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        if (!leaseRegistry.IsActive(ClientKey())) return StatusCode(409, new { message = "遠端工作階段連線不存在。" });
        if (request?.Strokes is null || request.Strokes.Count is < 1 or > 12) return BadRequest(new { message = "按鍵批次大小不正確。" });
        if (!rateLimiter.AllowInteraction(ClientKey(), DateTimeOffset.UtcNow, out var retryAfter)) return RateLimited(retryAfter);
        try { await desktop.SendKeyboardAsync(ClientKey(), request.Strokes, cancellationToken); if (!grants.TouchSuccessfulAction(User, DateTimeOffset.UtcNow)) return Forbid(); logger.LogInformation("Remote keyboard input accepted. TraceId={TraceId} Count={Count}", HttpContext.TraceIdentifier, request.Strokes.Count); return Ok(new { message = "按鍵已送出。" }); }
        catch (RemoteDesktopUnavailableException) { logger.LogWarning("Remote keyboard input unavailable. TraceId={TraceId}", HttpContext.TraceIdentifier); return StatusCode(503, new { message = "鍵盤輸入目前無法使用。" }); }
    }

    [HttpPost("mouse"), Authorize(Policy = "RemoteConsole:Mouse"), RequestSizeLimit(4096)]
    public async Task<IActionResult> Mouse([FromBody] RemoteMouseAction? request, CancellationToken cancellationToken)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        if (!leaseRegistry.IsActive(ClientKey())) return StatusCode(409, new { message = "遠端工作階段連線不存在。" });
        if (request is null) return BadRequest(new { message = "滑鼠要求格式不正確。" });
        if (!rateLimiter.AllowInteraction(ClientKey(), DateTimeOffset.UtcNow, out var retryAfter)) return RateLimited(retryAfter);
        try { await desktop.SendMouseAsync(ClientKey(), request, cancellationToken); if (!grants.TouchSuccessfulAction(User, DateTimeOffset.UtcNow)) return Forbid(); logger.LogInformation("Remote mouse input accepted. TraceId={TraceId} Generation={Generation}", HttpContext.TraceIdentifier, request.FrameGeneration); return Ok(new { message = "滑鼠操作已送出。" }); }
        catch (RemoteDesktopUnavailableException) { logger.LogWarning("Remote mouse input unavailable. TraceId={TraceId}", HttpContext.TraceIdentifier); return StatusCode(409, new { message = "畫面已變更或滑鼠操作目前無法使用。" }); }
    }

    [HttpPost("shell"), Authorize(Policy = "RemoteConsole:Shell"), RequestSizeLimit(4096)]
    public async Task<IActionResult> Shell([FromBody] ShellRequest? request, CancellationToken cancellationToken)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        if (!leaseRegistry.IsActive(ClientKey())) return StatusCode(409, new { message = "遠端工作階段連線不存在。" });
        var command = request?.Command ?? string.Empty;
        if (command.Length is < 1 or > 2048 || command.Contains('\0')) return BadRequest(new { message = "Shell 要求大小不正確。" });
        if (!rateLimiter.AllowShell(ClientKey(), DateTimeOffset.UtcNow, out var retryAfter)) return RateLimited(retryAfter);
        try { var result = await shellBroker.ExecuteAsync(ClientKey(), command, cancellationToken); if (!grants.TouchSuccessfulAction(User, DateTimeOffset.UtcNow)) return Forbid(); logger.LogInformation("Remote shell broker completed. TraceId={TraceId} ExitCode={ExitCode} Truncated={Truncated}", HttpContext.TraceIdentifier, result.ExitCode, result.Truncated); return Ok(result); }
        catch (RemoteDesktopUnavailableException) { logger.LogWarning("Remote shell broker unavailable. TraceId={TraceId}", HttpContext.TraceIdentifier); return StatusCode(503, new { message = "獨立低權限 Shell broker 尚未完成安全驗證。" }); }
    }

    [HttpPost("revoke"), RequestSizeLimit(4096)]
    public IActionResult Revoke()
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        var sessionId = ClientKey(); leaseRegistry.Release(sessionId); grants.Revoke(sessionId);
        logger.LogInformation("Remote control grant revoked. TraceId={TraceId}", HttpContext.TraceIdentifier);
        return Ok(new { message = "此網站控制授權已撤銷。" });
    }

    [HttpPost("text"), Authorize(Policy = "RemoteConsole:Text"), RequestSizeLimit(4096)]
    public async Task<IActionResult> Text([FromBody] RemoteTextRequest? request, CancellationToken cancellationToken)
    {
        if (!HasExactOrigin() || Request.ContentLength > 4096) return Forbid();
        if (!leaseRegistry.IsActive(ClientKey())) return StatusCode(409, new { message = "遠端工作階段連線不存在。" });
        if (!TryValidateText(request?.Text, out var text, out var message)) return BadRequest(new { message });
        if (!rateLimiter.AllowText(ClientKey(), DateTimeOffset.UtcNow, out var retryAfter)) return RateLimited(retryAfter);
        try
        {
            await desktop.SendTextAsync(ClientKey(), text, cancellationToken);
            if (!grants.TouchSuccessfulAction(User, DateTimeOffset.UtcNow)) return Forbid();
            // 不記錄文字內容、視窗標題、帳號或來源位址。
            logger.LogInformation("Remote text accepted. TraceId={TraceId} RuneCount={RuneCount}", HttpContext.TraceIdentifier, text.EnumerateRunes().Count());
            return Ok(new { message = "文字已送至目前的前景視窗。" });
        }
        catch (RemoteDesktopUnavailableException)
        {
            logger.LogWarning("Remote text unavailable. TraceId={TraceId}", HttpContext.TraceIdentifier);
            return StatusCode(503, new { message = "文字輸入目前無法使用。" });
        }
    }

    private bool HasExactOrigin()
    {
        var configured = configuration["RemoteConsole:PublicOrigin"]?.TrimEnd('/');
        var origin = Request.Headers.Origin.ToString().TrimEnd('/');
        return Uri.TryCreate(configured, UriKind.Absolute, out var expected) && expected.Scheme == Uri.UriSchemeHttps &&
            StringComparer.Ordinal.Equals(origin, expected.GetLeftPart(UriPartial.Authority));
    }

    internal static bool TryValidateText(string? value, out string text, out string message)
    {
        var source = value ?? string.Empty;
        for (var index = 0; index < source.Length; index++)
        {
            if (!char.IsSurrogate(source[index])) continue;
            if (!char.IsHighSurrogate(source[index]) || index + 1 >= source.Length || !char.IsLowSurrogate(source[index + 1]))
            { text = string.Empty; message = "文字含有不完整的 Unicode 字元。"; return false; }
            index++;
        }
        text = source.Normalize(NormalizationForm.FormC);
        message = string.Empty;
        if (text.Length == 0) { message = "請輸入要傳送的文字。"; return false; }
        if (Encoding.UTF8.GetByteCount(text) > MaximumTextBytes) { message = $"文字的 UTF-8 大小不得超過 {MaximumTextBytes} 位元組。"; return false; }
        var runeCount = 0;
        foreach (var rune in text.EnumerateRunes())
        {
            if (++runeCount > MaximumTextRunes) { message = $"每次最多傳送 {MaximumTextRunes} 個字元。"; return false; }
            var number = rune.Value;
            var category = Rune.GetUnicodeCategory(rune);
            var noncharacter = (number & 0xFFFE) == 0xFFFE || number is >= 0xFDD0 and <= 0xFDEF;
            var c1 = number is >= 0x80 and <= 0x9F;
            var bidiControl = number is 0x061C or 0x200E or 0x200F or >= 0x202A and <= 0x202E or >= 0x2066 and <= 0x2069;
            if (noncharacter || c1 || bidiControl || category is UnicodeCategory.Control or UnicodeCategory.Format or UnicodeCategory.Surrogate or UnicodeCategory.OtherNotAssigned or UnicodeCategory.LineSeparator or UnicodeCategory.ParagraphSeparator)
            { message = "文字含有不允許的控制、方向或隱藏字元。"; return false; }
        }
        return true;
    }

    private static string CapabilityName(RemoteCapability capability) => capability switch
    {
        RemoteCapability.Screen => "screen.read", RemoteCapability.Text => "input.text",
        RemoteCapability.Keyboard => "keyboard.write", RemoteCapability.Mouse => "mouse.write",
        RemoteCapability.BrowserInput => "browser.input",
        RemoteCapability.Shell => "shell.execute", _ => "unknown"
    };
    private string ClientKey() => User.FindFirstValue(PortalClaimTypes.SessionId) ?? "unknown";
    private ObjectResult RateLimited(TimeSpan retryAfter) { Response.Headers.RetryAfter = Math.Max(1, (int)Math.Ceiling(retryAfter.TotalSeconds)).ToString(CultureInfo.InvariantCulture); return StatusCode(429, new { message = "請降低操作頻率後再試。" }); }
    private void SetNoCacheHeaders() { Response.Headers.CacheControl = "no-store, no-cache, max-age=0"; Response.Headers.Pragma = "no-cache"; Response.Headers.Expires = "0"; Response.Headers.Remove("ETag"); }
    public sealed record PairingRequest(string? PairingNonce);
    public sealed record ControlVerifyRequest(string? Code);
    public sealed record RemoteTextRequest(string? Text);
    public sealed record KeyboardRequest(IReadOnlyList<RemoteKeyStroke>? Strokes);
    public sealed record ShellRequest(string? Command);
}
