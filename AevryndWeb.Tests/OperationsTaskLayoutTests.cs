using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsTaskLayoutTests
{
    [Fact]
    public void ShippedRemoteNodesKeepActiveEcdsaPublicKeysWithoutDisclosingContents()
    {
        var root = new DirectoryInfo(AppContext.BaseDirectory);
        while (root is not null && !File.Exists(Path.Combine(root.FullName, "AevryndWeb.slnx"))) root = root.Parent;
        Assert.NotNull(root);
        using var settings = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(root.FullName, "AevryndWeb", "appsettings.json")));
        var nodes = settings.RootElement.GetProperty("Operations").GetProperty("RemoteTelemetry").GetProperty("Nodes");
        foreach (var id in new[] { "taichung", "taoyuan" })
        {
            var node = nodes.GetProperty(id);
            Assert.True(node.GetProperty("AuthenticationMode").GetString() == "EcdsaP256", id + " must use EcdsaP256.");
            Assert.True(node.GetProperty("Keys").EnumerateObject().Any(key =>
                key.Value.TryGetProperty("Revoked", out var revoked) && revoked.ValueKind == System.Text.Json.JsonValueKind.False &&
                key.Value.TryGetProperty("PublicKey", out var value) && value.ValueKind == System.Text.Json.JsonValueKind.String &&
                !string.IsNullOrWhiteSpace(value.GetString())), id + " requires a non-revoked public key.");
        }
    }
    [Fact]
    public void HostCardsHaveIndependentBoundedKeyboardScrollableTaskLists()
    {
        var root = new DirectoryInfo(AppContext.BaseDirectory);
        while (root is not null && !File.Exists(Path.Combine(root.FullName, "AevryndWeb.slnx"))) root = root.Parent;
        Assert.NotNull(root);
        var css = File.ReadAllText(Path.Combine(root.FullName, "AevryndWeb", "wwwroot", "css", "site.css"));
        var view = File.ReadAllText(Path.Combine(root.FullName, "AevryndWeb", "Views", "Operations", "Index.cshtml"));
        Assert.Contains(".operations-schedule-grid{align-items:start}", css);
        Assert.Contains("max-height:min(34rem,65vh)", css);
        Assert.Contains("overflow-y:auto", css);
        Assert.Contains("max-height:min(28rem,55dvh)", css);
        Assert.Contains("scrollbar-gutter:stable", css);
        Assert.Contains("data-schedule-scroll-hint", view);
        Assert.Contains("tabindex=\"0\"", view);
        Assert.Contains("aria-describedby=\"task-scroll-@node.Id\"", view);
        Assert.Contains("全部 @tasks.Length 筆", view);
        Assert.True(view.IndexOf("operations-schedule-summary", StringComparison.Ordinal) < view.IndexOf("data-schedule-list", StringComparison.Ordinal));
        Assert.DoesNotContain("tasks.Take(", view);
    }
}
