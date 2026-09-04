using System.Net;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Text.Encodings.Web;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class RemoteConsoleContractTests : IDisposable
{
    private readonly RemoteConsoleFactory factory = new();
    public void Dispose() => factory.Dispose();

    [Theory]
    [InlineData(null, HttpStatusCode.Unauthorized)]
    [InlineData("wrong", HttpStatusCode.Forbidden)]
    [InlineData("owner-none", HttpStatusCode.Forbidden)]
    public async Task FrameRejectsMissingWrongOrUngrantedIdentity(string? identity, HttpStatusCode expected)
    {
        using var client = CreateClient();
        using var request = new HttpRequestMessage(HttpMethod.Get, "/RemoteConsole/frame");
        if (identity is not null) request.Headers.Add("X-Test-Identity", identity);
        Assert.Equal(expected, (await client.SendAsync(request)).StatusCode);
    }

    [Fact]
    public async Task PortalPageAllowsOwnerButRemoteFrameRequiresCapability()
    {
        using var client = CreateClient();
        var portal = await SendAsync(client, HttpMethod.Get, "/RemoteConsole", "owner-none");
        var frame = await SendAsync(client, HttpMethod.Get, "/RemoteConsole/frame", "owner-screen");
        Assert.Equal(HttpStatusCode.OK, portal.StatusCode);
        Assert.Equal(HttpStatusCode.OK, frame.StatusCode);
        Assert.Equal("image/jpeg", frame.Content.Headers.ContentType?.MediaType);
        Assert.True(frame.Headers.CacheControl?.NoStore);
        Assert.True(frame.Headers.CacheControl?.NoCache);
        Assert.False(frame.Headers.Contains("ETag"));
        Assert.Equal("42", frame.Headers.GetValues("X-Aevrynd-Frame-Generation").Single());
    }

    [Fact]
    public async Task FrameRateLimitRejectsImmediateSecondCapture()
    {
        using var client = CreateClient();
        Assert.Equal(HttpStatusCode.OK, (await SendAsync(client, HttpMethod.Get, "/RemoteConsole/frame", "owner-screen")).StatusCode);
        var second = await SendAsync(client, HttpMethod.Get, "/RemoteConsole/frame", "owner-screen");
        Assert.Equal(HttpStatusCode.TooManyRequests, second.StatusCode);
        Assert.True(second.Headers.Contains("Retry-After"));
    }

    [Fact]
    public async Task LocalKillSwitchImmediatelyBlocksGrantedCapability()
    {
        using var client = CreateClient(); factory.Guard.Enabled = false;
        var response = await SendAsync(client, HttpMethod.Get, "/RemoteConsole/frame", "owner-screen");
        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
        Assert.Equal(0, factory.Desktop.CaptureCount);
    }

    [Fact]
    public async Task TextRequiresAntiforgeryAndFixedOrigin()
    {
        using var client = CreateClient();
        var missingCsrf = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = "測試" }, null);
        Assert.Equal(HttpStatusCode.BadRequest, missingCsrf.StatusCode);
        var token = await GetCsrfAsync(client, "owner-text");
        var wrongOrigin = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://evil.test", new { text = "測試" }, token);
        Assert.Equal(HttpStatusCode.Forbidden, wrongOrigin.StatusCode);
        using var forgedHost = new HttpRequestMessage(HttpMethod.Post, "/RemoteConsole/text") { Content = JsonContent.Create(new { text = "測試" }) };
        forgedHost.Headers.Host = "evil.test"; forgedHost.Headers.Add("X-Test-Identity", "owner-text"); forgedHost.Headers.Add("Origin", "https://evil.test"); forgedHost.Headers.Add("X-CSRF-TOKEN", token);
        Assert.Contains((await client.SendAsync(forgedHost)).StatusCode, new[] { HttpStatusCode.BadRequest, HttpStatusCode.Forbidden });
        var valid = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = "Ａé🙂" }, token);
        Assert.Equal(HttpStatusCode.OK, valid.StatusCode);
        Assert.Equal("Ａé🙂", factory.Desktop.LastText);
    }

    [Theory]
    [InlineData("line\nbreak")]
    [InlineData("tab\tvalue")]
    [InlineData("bidirectional\u202Etext")]
    [InlineData("format\u200Dtext")]
    [InlineData("noncharacter\uFDD0")]
    [InlineData("terminal\uFFFF")]
    public async Task TextRejectsControlAndHiddenCharacters(string value)
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-text");
        var response = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = value }, token);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task TextRejectsUnpairedSurrogateJsonEscape()
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-text");
        using var request = new HttpRequestMessage(HttpMethod.Post, "/RemoteConsole/text") { Content = new StringContent("{\"text\":\"\\uD800\"}", System.Text.Encoding.UTF8, "application/json") };
        request.Headers.Add("X-Test-Identity", "owner-text"); request.Headers.Add("Origin", "https://console.test"); request.Headers.Add("X-CSRF-TOKEN", token);
        Assert.Equal(HttpStatusCode.BadRequest, (await client.SendAsync(request)).StatusCode);
    }

    [Fact]
    public async Task TextRejectsMoreThan256ScalarsAndBodyOver4KiB()
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-text");
        Assert.Equal(HttpStatusCode.BadRequest, (await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = new string('a', 257) }, token)).StatusCode);
        var oversized = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = new string('a', 5000) }, token);
        Assert.Contains(oversized.StatusCode, new[] { HttpStatusCode.BadRequest, HttpStatusCode.RequestEntityTooLarge, HttpStatusCode.Forbidden });
    }

    [Fact]
    public async Task CapabilityPoliciesDoNotImplyEachOther()
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-text");
        var keyboard = await PostAsync(client, "/RemoteConsole/keyboard", "owner-text", "https://console.test", new { strokes = new[] { new { code = "KeyA", action = "press" } } }, token);
        var mouse = await PostAsync(client, "/RemoteConsole/mouse", "owner-text", "https://console.test", new { frameGeneration = 42, x = .5, y = .5, action = "leftClick", delta = 0 }, token);
        var shell = await PostAsync(client, "/RemoteConsole/shell", "owner-text", "https://console.test", new { command = "whoami" }, token);
        Assert.Equal(HttpStatusCode.Forbidden, keyboard.StatusCode);
        Assert.Equal(HttpStatusCode.Forbidden, mouse.StatusCode);
        Assert.Equal(HttpStatusCode.Forbidden, shell.StatusCode);
    }

    [Fact]
    public async Task AuthorizedKeyboardAndMouseUseOnlyFakeSeam()
    {
        using var keyboardClient = CreateClient(); var keyboardToken = await GetCsrfAsync(keyboardClient, "owner-keyboard");
        var keyboard = await PostAsync(keyboardClient, "/RemoteConsole/keyboard", "owner-keyboard", "https://console.test", new { strokes = new[] { new { code = "KeyA", action = "press" } } }, keyboardToken);
        using var mouseClient = CreateClient(); var mouseToken = await GetCsrfAsync(mouseClient, "owner-mouse");
        var mouse = await PostAsync(mouseClient, "/RemoteConsole/mouse", "owner-mouse", "https://console.test", new { frameGeneration = 42, x = .5, y = .5, action = "leftClick", delta = 0 }, mouseToken);
        Assert.Equal(HttpStatusCode.OK, keyboard.StatusCode); Assert.Equal(HttpStatusCode.OK, mouse.StatusCode);
    }

    [Fact]
    public async Task ShellCapabilityRemainsUnavailableWithoutBroker()
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-shell");
        var response = await PostAsync(client, "/RemoteConsole/shell", "owner-shell", "https://console.test", new { command = "whoami" }, token);
        Assert.Equal(HttpStatusCode.ServiceUnavailable, response.StatusCode);
    }

    [Fact]
    public async Task TextRateLimitRejectsThirtyFirstRequest()
    {
        using var client = CreateClient(); var token = await GetCsrfAsync(client, "owner-text"); HttpResponseMessage? response = null;
        for (var index = 0; index < 31; index++) response = await PostAsync(client, "/RemoteConsole/text", "owner-text", "https://console.test", new { text = "a" }, token);
        Assert.Equal(HttpStatusCode.TooManyRequests, response!.StatusCode);
    }

    private HttpClient CreateClient() { var client = factory.CreateClient(new WebApplicationFactoryClientOptions { BaseAddress = new Uri("https://console.test"), AllowAutoRedirect = false, HandleCookies = true }); client.DefaultRequestHeaders.Add("X-Test-Instance", Guid.NewGuid().ToString("N")); return client; }
    private static async Task<HttpResponseMessage> SendAsync(HttpClient client, HttpMethod method, string path, string identity)
    { var request = new HttpRequestMessage(method, path); request.Headers.Add("X-Test-Identity", identity); return await client.SendAsync(request); }
    private static async Task<string> GetCsrfAsync(HttpClient client, string identity)
    { var response = await SendAsync(client, HttpMethod.Get, "/api/auth/csrf", identity); return (await response.Content.ReadFromJsonAsync<CsrfResponse>())!.Token; }
    private static async Task<HttpResponseMessage> PostAsync(HttpClient client, string path, string identity, string origin, object body, string? token)
    { var request = new HttpRequestMessage(HttpMethod.Post, path) { Content = JsonContent.Create(body) }; request.Headers.Add("X-Test-Identity", identity); request.Headers.Add("Origin", origin); if (token is not null) request.Headers.Add("X-CSRF-TOKEN", token); return await client.SendAsync(request); }
    private sealed record CsrfResponse(string Token);
}

public sealed class RemoteConsoleFactory : WebApplicationFactory<Program>
{
    public FakeDesktop Desktop { get; } = new();
    public FakeGuard Guard { get; } = new();
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Development");
        builder.ConfigureAppConfiguration((_, configuration) => configuration.AddInMemoryCollection(new Dictionary<string, string?> { ["RemoteConsole:PublicOrigin"] = "https://console.test", ["AllowedHosts"] = "console.test" }));
        builder.ConfigureTestServices(services =>
        {
            services.AddAuthentication(options => { options.DefaultAuthenticateScheme = "Test"; options.DefaultChallengeScheme = "Test"; options.DefaultForbidScheme = "Test"; }).AddScheme<AuthenticationSchemeOptions, TestAuthenticationHandler>("Test", _ => { });
            services.RemoveAll<IPortalSessionStore>(); services.AddSingleton<IPortalSessionStore, FakePortalSessions>();
            services.RemoveAll<IRemoteControlGrantService>(); services.AddSingleton<IRemoteControlGrantService, FakeGrants>();
            services.RemoveAll<IRemoteConsoleGuard>(); services.AddSingleton<IRemoteConsoleGuard>(Guard);
            services.RemoveAll<IRemoteDesktopService>(); services.AddSingleton<IRemoteDesktopService>(Desktop);
            services.RemoveAll<IRemoteControlLeaseRegistry>(); services.AddSingleton<IRemoteControlLeaseRegistry, AlwaysActiveLeaseRegistry>();
        });
    }
}

public sealed class TestAuthenticationHandler(IOptionsMonitor<AuthenticationSchemeOptions> options, ILoggerFactory logger, UrlEncoder encoder) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        var value = Request.Headers["X-Test-Identity"].ToString(); if (value.Length == 0) return Task.FromResult(AuthenticateResult.NoResult());
        var email = value == "wrong" ? "other@example.com" : PortalIdentity.AllowedEmail;
        var session = Request.Headers["X-Test-Instance"].ToString();
        var claims = new List<Claim> { new(ClaimTypes.NameIdentifier, "portal-owner"), new(ClaimTypes.Email, email), new(PortalClaimTypes.SessionId, session.Length == 0 ? "test-session" : session), new(PortalClaimTypes.SecurityStamp, "stamp"), new(PortalClaimTypes.AuthenticationTime, "0") };
        if (value.StartsWith("owner-", StringComparison.Ordinal) && value != "owner-none") claims.Add(new Claim("test-cap", value[6..]));
        return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(new ClaimsIdentity(claims, Scheme.Name)), Scheme.Name)));
    }
}

public sealed class FakePortalSessions : IPortalSessionStore
{
    public PortalSession Create(string email, DateTimeOffset now) => throw new NotSupportedException();
    public bool Validate(ClaimsPrincipal user, DateTimeOffset now) => user.FindFirstValue(ClaimTypes.Email) == PortalIdentity.AllowedEmail;
    public void Revoke(string? sessionId) { }
}
public sealed class FakeGuard : IRemoteConsoleGuard
{
    public bool Enabled { get; set; } = true;
    private static readonly RemoteConsoleEnablement State = new(new string('A', 64), DateTimeOffset.UtcNow.AddHours(1), new HashSet<RemoteCapability>(Enum.GetValues<RemoteCapability>()), "00", false);
    public bool TryRead(DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = State; return Enabled; }
    public bool VerifyPairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = State; return Enabled; }
    public bool ConsumePairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement) { enablement = State; return Enabled; }
    public void ResetOnStartup() { }
}
public sealed class FakeGrants : IRemoteControlGrantService
{
    public Task RequestAsync(string sessionId, string pairingNonce, CancellationToken cancellationToken) => Task.CompletedTask;
    public RemoteControlGrant? VerifyAndActivate(string sessionId, string code, DateTimeOffset now) => null;
    public bool Validate(ClaimsPrincipal user, RemoteCapability capability, DateTimeOffset now) => user.HasClaim("test-cap", capability.ToString().ToLowerInvariant());
    public bool IsActive(ClaimsPrincipal user, DateTimeOffset now) => false;
    public RemoteControlGrantStatus? GetStatus(ClaimsPrincipal user, DateTimeOffset now) => null;
    public bool ValidateLease(ClaimsPrincipal user, DateTimeOffset now) => user.HasClaim(claim => claim.Type == "test-cap");
    public bool TouchSuccessfulAction(ClaimsPrincipal user, DateTimeOffset now) => user.HasClaim(claim => claim.Type == "test-cap");
    public void Revoke(string? sessionId) { }
    public void RevokeAll() { }
    public IReadOnlyList<string> RevokeExpired(DateTimeOffset now) => [];
}
public sealed class FakeDesktop : IRemoteDesktopService
{
    public string? LastText { get; private set; }
    public int CaptureCount { get; private set; }
    public List<string> ReleasedSessions { get; } = [];
    public RemoteDesktopAvailability GetAvailability() => new(true, string.Empty);
    public Task<RemoteDesktopFrame> CaptureJpegAsync(CancellationToken cancellationToken) { CaptureCount++; return Task.FromResult(new RemoteDesktopFrame([0xFF, 0xD8, 0xFF, 0xD9], 42, DateTimeOffset.UtcNow, 2, 2)); }
    public Task SendTextAsync(string sessionId, string text, CancellationToken cancellationToken) { LastText = text; return Task.CompletedTask; }
    public Task SendKeyboardAsync(string sessionId, IReadOnlyList<RemoteKeyStroke> strokes, CancellationToken cancellationToken) => Task.CompletedTask;
    public Task SendMouseAsync(string sessionId, RemoteMouseAction action, CancellationToken cancellationToken) => Task.CompletedTask;
    public void ReleaseInjectedModifiers(string? sessionId) { if (sessionId is not null) ReleasedSessions.Add(sessionId); }
    public void ReleaseAllInjectedModifiers() { }
    public void RetryPendingReleases() { }
}
public sealed class AlwaysActiveLeaseRegistry : IRemoteControlLeaseRegistry
{
    public bool TryAcquire(string sessionId) => true;
    public bool IsActive(string sessionId) => true;
    public void Release(string sessionId) { }
    public void ReleaseAll() { }
}
