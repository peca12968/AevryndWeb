using System.Net;
using System.Net.Http.Json;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class AuthenticationContractTests
{
    [Fact]
    public async Task ExactNormalizedOwnerLoginCreatesServerValidatedPortalSession()
    {
        using var factory = new LoginFactory(); using var client = factory.CreateClient(Options());
        var token = await Csrf(client);
        using var request = VerifyRequest("  SLIME12968@GMAIL.COM  ", token);
        var response = await client.SendAsync(request);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains(response.Headers.GetValues("Set-Cookie"), value => value.StartsWith("__Host-AevryndSession=", StringComparison.Ordinal));
        Assert.Equal(HttpStatusCode.OK, (await client.GetAsync("/Home/Portal")).StatusCode);
        var remoteConsole = await client.GetAsync("/RemoteConsole");
        Assert.Equal(HttpStatusCode.OK, remoteConsole.StatusCode);
        Assert.Contains("建立短效控制授權", await remoteConsole.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task DifferentEmailCannotCreatePortalSession()
    {
        using var factory = new LoginFactory(); using var client = factory.CreateClient(Options());
        var token = await Csrf(client);
        var response = await client.SendAsync(VerifyRequest("other@example.com", token));
        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
        Assert.Equal(HttpStatusCode.Redirect, (await client.GetAsync("/Home/Portal")).StatusCode);
    }

    private static WebApplicationFactoryClientOptions Options() => new() { BaseAddress = new Uri("https://console.test"), AllowAutoRedirect = false, HandleCookies = true };
    private static async Task<string> Csrf(HttpClient client) => (await (await client.GetAsync("/api/auth/csrf")).Content.ReadFromJsonAsync<CsrfPayload>())!.Token;
    private static HttpRequestMessage VerifyRequest(string email, string token)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/api/auth/verify") { Content = JsonContent.Create(new { email, code = "TESTCODE" }) };
        request.Headers.Add("Origin", "https://console.test"); request.Headers.Add("X-CSRF-TOKEN", token); return request;
    }
    private sealed record CsrfPayload(string Token);
}

public sealed class LoginFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
        builder.ConfigureAppConfiguration((_, configuration) => configuration.AddInMemoryCollection(new Dictionary<string, string?> { ["AllowedHosts"] = "console.test", ["RemoteConsole:PublicOrigin"] = "https://console.test" }));
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<IOtpService>(); services.AddSingleton<IOtpService, ExactOwnerOtp>();
            services.RemoveAll<IEmailSender>(); services.AddSingleton<IEmailSender, TestEmailSender>();
            services.RemoveAll<IRemoteConsoleGuard>(); services.AddSingleton<IRemoteConsoleGuard, FakeGuard>();
            services.RemoveAll<IRemoteDesktopService>(); services.AddSingleton<IRemoteDesktopService, FakeDesktop>();
            services.RemoveAll<IRemoteControlGrantService>(); services.AddSingleton<IRemoteControlGrantService, FakeGrants>();
            services.RemoveAll<IRemoteControlLeaseRegistry>(); services.AddSingleton<IRemoteControlLeaseRegistry, AlwaysActiveLeaseRegistry>();
        });
    }
    private sealed class ExactOwnerOtp : IOtpService
    {
        public Task RequestAsync(string email, string clientKey, CancellationToken cancellationToken) => Task.CompletedTask;
        public bool Verify(string email, string code, string clientKey) => email.Trim().Equals(PortalIdentity.AllowedEmail, StringComparison.OrdinalIgnoreCase) && code == "TESTCODE";
    }
    private sealed class TestEmailSender : IEmailSender
    {
        public bool IsReady => true;
        public Task SendAsync(string recipient, string code, CancellationToken cancellationToken) => Task.CompletedTask;
    }
}
