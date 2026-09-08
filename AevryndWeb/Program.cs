using AevryndWeb.Data;
using Microsoft.AspNetCore.StaticFiles;

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    Args = args,
    ContentRootPath = AppContext.BaseDirectory,
    WebRootPath = Path.Combine(AppContext.BaseDirectory, "wwwroot")
});

builder.Services.AddControllersWithViews();
builder.Services.AddSingleton<ISiteStatisticsStore, SqlSiteStatisticsStore>();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["X-Frame-Options"] = "DENY";
    context.Response.Headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
    context.Response.Headers["Content-Security-Policy"] =
        "default-src 'self'; style-src 'self' https://fonts.googleapis.com; " +
        "font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self' blob:; " +
        "img-src 'self' data: blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'";
    await next();
});

if (builder.Configuration.GetValue("Hosting:UseHttpsRedirection", false))
{
    app.UseHttpsRedirection();
}

var contentTypes = new FileExtensionContentTypeProvider();
contentTypes.Mappings[".glb"] = "model/gltf-binary";
app.UseStaticFiles(new StaticFileOptions
{
    ContentTypeProvider = contentTypes,
    OnPrepareResponse = context =>
        context.Context.Response.Headers.CacheControl = "public,max-age=3600"
});

app.UseRouting();
app.MapControllers();
app.MapControllerRoute("default", "{controller=Home}/{action=Index}/{id?}");

await using (var scope = app.Services.CreateAsyncScope())
{
    await scope.ServiceProvider.GetRequiredService<ISiteStatisticsStore>()
        .InitializeAsync();
}

app.Run();

public partial class Program;
