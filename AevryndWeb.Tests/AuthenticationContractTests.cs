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
    public async Task ShowcaseIsPublicAndPreservesReleaseTruth()
    {
        using var factory = new LoginFactory(); using var client = factory.CreateClient(Options());
        var response = await client.GetAsync("/Showcase"); var html = await response.Content.ReadAsStringAsync();
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("34 / 100", html); Assert.Contains("v1.4 未發布", html);
        Assert.DoesNotContain("DLSS 未實作", html); Assert.Contains("DLSS 深度語意切片已驗證", html);
        Assert.Contains("Bloom slice 已提交", html); Assert.Contains("1186b60", html);
        Assert.Contains("gameplay-evolution.mp4", html); Assert.Contains("engine-evolution.mp4", html);
        Assert.Contains("非連續遊玩錄影", html); Assert.Contains("GPT-6 Astra", html);
        Assert.DoesNotContain("GPT-5.6 sol", html);
        Assert.Contains("主機開發，副機按需提供測試資源", html);
        Assert.Contains("名詞中文對照", html);
        Assert.Contains("權威視覺分數維持 34 / 100", html);
        Assert.DoesNotContain(">40 / 100<", html);
        Assert.Contains("commit 5bcc1e3", html);
        Assert.Contains("FACE V4 · NO-GO", html);
        Assert.Contains("HAIR V5 → V6 · BOTH NO-GO", html);
        Assert.Contains("character-hair-v6-native-profile.png", html);
        Assert.Contains("Qwen3.8-27B：有條件降低重複工作成本", html);
        Assert.Contains("網站可操作的捏臉／身材技術預覽", html);
        Assert.Contains("data-gpu-shape-frame=\"10\"", html);
        Assert.Contains("進入開發展示前，請先確認已成年", html);
        Assert.Contains("可能出現未完成服裝、人體模型、局部裸露", html);
        Assert.Contains("data-age-confirm", html);
        Assert.Contains("MASK", html);
        Assert.Contains("ENGINE ARCHITECTURE", html); Assert.Contains("TRACEABLE RELEASES", html);
        Assert.Contains("data-release-filter", html); Assert.Contains("data-stage-filter", html);
        Assert.Contains("data-map-zoom", html); Assert.Contains("/js/showcase.js", html);
        Assert.Equal("default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data: blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'", response.Headers.GetValues("Content-Security-Policy").Single());
        var dataTables = SourceFile("wwwroot", "lib", "datatables", "datatables.min.js");
        var metadata = SourceFile("wwwroot", "lib", "datatables", "package.core.json");
        var styleMetadata = SourceFile("wwwroot", "lib", "datatables", "package.style.json");
        var license = SourceFile("wwwroot", "lib", "datatables", "LICENSE.core.txt");
        var styleLicense = SourceFile("wwwroot", "lib", "datatables", "LICENSE.style.txt");
        Assert.Contains("DataTables 3.0.3", dataTables); Assert.Contains("\"version\": \"3.0.3\"", metadata); Assert.Contains("\"version\": \"3.0.3\"", styleMetadata);
        Assert.Contains("\"license\": \"MIT\"", metadata); Assert.Contains("\"license\": \"MIT\"", styleMetadata); Assert.Contains("MIT License", license); Assert.Contains("MIT License", styleLicense);
    }

    [Theory]
    [InlineData("slime12968@gmail.com")]
    [InlineData("peca12968@gmail.com")]
    public async Task AdminLoginCreatesServerValidatedFullAccessSession(string email)
    {
        using var factory = new LoginFactory(); using var client = factory.CreateClient(Options());
        var token = await Csrf(client);
        using var request = VerifyRequest($"  {email.ToUpperInvariant()}  ", token);
        var response = await client.SendAsync(request);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains(response.Headers.GetValues("Set-Cookie"), value => value.StartsWith("__Host-AevryndSession=", StringComparison.Ordinal));
        Assert.Equal(HttpStatusCode.OK, (await client.GetAsync("/Home/Portal")).StatusCode);
        var remoteConsole = await client.GetAsync("/RemoteConsole");
        Assert.Equal(HttpStatusCode.OK, remoteConsole.StatusCode);
        Assert.Contains("建立短效控制授權", await remoteConsole.Content.ReadAsStringAsync());
        Assert.Equal(HttpStatusCode.OK, (await client.GetAsync("/Operations")).StatusCode);
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

    [Theory]
    [InlineData("en531@livemail.tw")]
    [InlineData("tokkinjoey@gmail.com")]
    [InlineData("geminjjj@gmail.com")]
    public async Task EveryUserRoleCanOnlyEnterOperationsWhileShowcaseRemainsPublic(string email)
    {
        using var factory = new LoginFactory(); using var client = factory.CreateClient(Options());
        var token = await Csrf(client);
        var response = await client.SendAsync(VerifyRequest(email, token));
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("/Operations", await response.Content.ReadAsStringAsync(), StringComparison.Ordinal);
        var operations = await client.GetAsync("/Operations");
        Assert.Equal(HttpStatusCode.OK, operations.StatusCode);
        var operationsHtml = await operations.Content.ReadAsStringAsync();
        Assert.Contains("data-operations-root", operationsHtml); Assert.Contains("/Operations/snapshot", operationsHtml);
        Assert.DoesNotContain("window.setTimeout", operationsHtml, StringComparison.Ordinal);
        var snapshot = await client.GetAsync("/Operations/snapshot");
        Assert.Equal(HttpStatusCode.OK, snapshot.StatusCode);
        Assert.Contains("\"nodes\"", await snapshot.Content.ReadAsStringAsync(), StringComparison.Ordinal);
        Assert.Contains("no-store", snapshot.Headers.CacheControl!.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Equal(HttpStatusCode.Forbidden, (await client.GetAsync("/Home/Portal")).StatusCode);
        Assert.Equal(HttpStatusCode.Forbidden, (await client.GetAsync("/RemoteConsole")).StatusCode);
        Assert.Equal(HttpStatusCode.OK, (await client.GetAsync("/Showcase")).StatusCode);
        var script = SourceFile("wwwroot", "js", "site.js");
        Assert.Contains("保留最後一次已驗證資料", script);
        var parsePosition = script.IndexOf("model = await response.json()", StringComparison.Ordinal);
        var validatePosition = script.IndexOf("if (!validModel(model))", StringComparison.Ordinal);
        var renderPosition = script.IndexOf("render(model);", StringComparison.Ordinal);
        Assert.True(parsePosition >= 0 && validatePosition > parsePosition && renderPosition > validatePosition);
        Assert.Contains("historyDataTable?.search()", script); Assert.Contains("historyDataTable?.page()", script);
        Assert.Contains("historyDataTable.row.add(row)", script); Assert.Equal(1, script.Split("new window.DataTable", StringSplitOptions.None).Length - 1);
    }

    private static WebApplicationFactoryClientOptions Options() => new() { BaseAddress = new Uri("https://console.test"), AllowAutoRedirect = false, HandleCookies = true };
    private static async Task<string> Csrf(HttpClient client) => (await (await client.GetAsync("/api/auth/csrf")).Content.ReadFromJsonAsync<CsrfPayload>())!.Token;
    private static HttpRequestMessage VerifyRequest(string email, string token)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/api/auth/verify") { Content = JsonContent.Create(new { email, code = "TESTCODE" }) };
        request.Headers.Add("Origin", "https://console.test"); request.Headers.Add("X-CSRF-TOKEN", token); return request;
    }
    private static string SourceFile(params string[] parts)
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var project = Path.Combine(directory.FullName, "AevryndWeb", "AevryndWeb.csproj");
            if (File.Exists(project)) return File.ReadAllText(Path.Combine(new[] { Path.GetDirectoryName(project)! }.Concat(parts).ToArray()));
            directory = directory.Parent;
        }
        throw new DirectoryNotFoundException("AevryndWeb source was not found.");
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
        public bool Verify(string email, string code, string clientKey) => PortalIdentity.IsAllowed(email) && code == "TESTCODE";
    }
    private sealed class TestEmailSender : IEmailSender
    {
        public bool IsReady => true;
        public Task SendAsync(string recipient, string code, CancellationToken cancellationToken) => Task.CompletedTask;
    }
}
