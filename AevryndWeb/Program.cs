using System.Net;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Authorization;

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    Args = args,
    ContentRootPath = AppContext.BaseDirectory,
    WebRootPath = Path.Combine(AppContext.BaseDirectory, "wwwroot")
});
// 必須在任何畫面或視窗 API 前固定程序 DPI 模式；測試環境只使用可注入 seam，不變更測試執行器程序。
IRemoteDpiBootstrap remoteDpiBootstrap = builder.Environment.IsEnvironment("Testing")
    ? new RemoteDpiBootstrap(false, "Native DPI bootstrap is disabled in the test host.")
    : RemoteDpiBootstrap.Initialize(new WindowsRemoteDpiNative());
builder.WebHost.UseUrls(builder.Configuration["Hosting:Url"] ?? "http://127.0.0.1:8792");
builder.Services.AddControllersWithViews(options => options.Filters.Add(new AutoValidateAntiforgeryTokenAttribute()));
builder.Services.AddAntiforgery(options => { options.HeaderName = "X-CSRF-TOKEN"; options.Cookie.Name = "__Host-AevryndCsrf"; options.Cookie.SecurePolicy = CookieSecurePolicy.Always; options.Cookie.SameSite = SameSiteMode.Strict; });
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme).AddCookie(options =>
{
    options.Cookie.Name = "__Host-AevryndSession";
    options.Cookie.HttpOnly = true;
    options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.ExpireTimeSpan = TimeSpan.FromHours(8);
    options.SlidingExpiration = false;
    options.LoginPath = "/";
});
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy(PortalIdentity.PortalOwnerPolicy, policy => policy
        .RequireAuthenticatedUser()
        .RequireClaim(System.Security.Claims.ClaimTypes.Email, PortalIdentity.AllowedEmail)
        .AddRequirements(new PortalOwnerRequirement()));
    foreach (var capability in Enum.GetValues<RemoteCapability>())
        options.AddPolicy(PortalIdentity.CapabilityPolicy(capability), policy => policy
            .RequireAuthenticatedUser()
            .RequireClaim(System.Security.Claims.ClaimTypes.Email, PortalIdentity.AllowedEmail)
            .AddRequirements(new RemoteControlRequirement(capability)));
});
builder.Services.AddMemoryCache();
builder.Services.AddDataProtection().PersistKeysToFileSystem(new DirectoryInfo(builder.Configuration["DataProtection:KeyPath"] ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AevryndWeb", "keys")));
builder.Services.AddSingleton<IOtpService, OtpService>();
builder.Services.AddSingleton<IEmailSender, GmailEmailSender>();
builder.Services.AddSingleton<IPortalSessionStore, PortalSessionStore>();
builder.Services.AddSingleton<IRemoteControlGrantService, RemoteControlGrantService>();
builder.Services.AddSingleton<IRemoteConsoleGuard, RemoteConsoleGuard>();
builder.Services.AddSingleton<IAuthorizationHandler, PortalOwnerAuthorizationHandler>();
builder.Services.AddSingleton<IAuthorizationHandler, RemoteControlAuthorizationHandler>();
builder.Services.AddSingleton<IRemoteDesktopService, WindowsRemoteDesktopService>();
builder.Services.AddSingleton(remoteDpiBootstrap);
builder.Services.AddSingleton<IRemoteShellBroker, UnavailableRemoteShellBroker>();
builder.Services.AddSingleton<IRemoteConsoleRateLimiter, RemoteConsoleRateLimiter>();
builder.Services.AddSingleton<IRemoteControlLeaseRegistry, RemoteControlLeaseRegistry>();
builder.Services.AddHostedService<RemoteControlStartupReset>();
builder.Services.AddHostedService<RemoteControlRevocationMonitor>();
builder.Services.Configure<ForwardedHeadersOptions>(options => { options.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto; options.KnownProxies.Add(IPAddress.Loopback); options.KnownProxies.Add(IPAddress.IPv6Loopback); });

var app = builder.Build();
if (!remoteDpiBootstrap.Ready) app.Logger.LogWarning("Remote Console DPI bootstrap unavailable. Reason={Reason}", remoteDpiBootstrap.Reason);
else app.Logger.LogInformation("Remote Console DPI bootstrap verified as Per-Monitor-V2.");
app.UseForwardedHeaders();
if (!app.Environment.IsDevelopment()) { app.UseExceptionHandler("/Home/Error"); app.UseHsts(); }
app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["X-Frame-Options"] = "DENY";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    context.Response.Headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data: blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'";
    context.Response.Headers["Cache-Control"] = "no-store";
    if (HttpMethods.IsPost(context.Request.Method) && context.Request.Headers.Origin.Count > 0)
    {
        // 公開來源固定由本機設定決定，不信任可由請求者提供的 Host 標頭。
        var configuredOrigin = builder.Configuration["RemoteConsole:PublicOrigin"]?.TrimEnd('/');
        if (!Uri.TryCreate(configuredOrigin, UriKind.Absolute, out var expected) || expected.Scheme != Uri.UriSchemeHttps ||
            !StringComparer.Ordinal.Equals(context.Request.Headers.Origin.ToString().TrimEnd('/'), expected.GetLeftPart(UriPartial.Authority)))
        { context.Response.StatusCode = StatusCodes.Status403Forbidden; return; }
    }
    await next();
});
app.UseHttpsRedirection();
app.UseStaticFiles(new StaticFileOptions { OnPrepareResponse = ctx => { ctx.Context.Response.Headers["X-Content-Type-Options"] = "nosniff"; ctx.Context.Response.Headers["Cache-Control"] = "public,max-age=3600"; } });
app.UseRouting(); app.UseAuthentication(); app.UseAuthorization();
app.MapControllerRoute("default", "{controller=Home}/{action=Index}/{id?}");
app.Run();

public partial class Program;
