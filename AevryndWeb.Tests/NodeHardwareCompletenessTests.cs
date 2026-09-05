using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class NodeHardwareCompletenessTests
{
    [Fact]
    public void CompleteTrustedLocalHardwareRemainsVerified()
    {
        Assert.Equal("verified", NodeHardwareCatalog.ResolveHardwareStatus("verified", "CPU", "RAM", "GPU", "Board", "Windows", ["SSD"]));
    }

    [Theory]
    [InlineData("CPU", "RAM", "GPU", null, null, "partial")]
    [InlineData("CPU", "RAM", "GPU", "Board", null, "partial")]
    public void PartialRemoteHardwareCannotRemainVerified(string cpu, string ram, string gpu, string? motherboard, string? os, string expected)
    {
        Assert.Equal(expected, NodeHardwareCatalog.ResolveHardwareStatus("verified", cpu, ram, gpu, motherboard, os, ["SSD"]));
    }

    [Fact]
    public void EmptyHardwareIsPendingEvenWhenDeclaredVerified()
    {
        Assert.Equal("pending", NodeHardwareCatalog.ResolveHardwareStatus("verified", null, null, null, null, null, []));
    }

    [Theory]
    [InlineData("pending")]
    [InlineData("unknown")]
    public void UntrustedDeclaredStatusCannotBeUpgradedByCompleteFields(string declaredStatus)
    {
        Assert.Equal("pending", NodeHardwareCatalog.ResolveHardwareStatus(declaredStatus, "CPU", "RAM", "GPU", "Board", "Windows", ["SSD"]));
    }

    [Fact]
    public void OperationsSsrAndRefreshUseChineseCompletenessLabelsAndSameContract()
    {
        var root = FindRepositoryRoot();
        var view = File.ReadAllText(Path.Combine(root, "AevryndWeb", "Views", "Operations", "Index.cshtml"));
        var script = File.ReadAllText(Path.Combine(root, "AevryndWeb", "wwwroot", "js", "site.js"));
        Assert.Contains("已驗證", view); Assert.Contains("部分已驗證", view); Assert.Contains("待採樣", view);
        Assert.Contains("hardwareStatus", script); Assert.Contains("部分已驗證", script); Assert.Contains("待採樣", script);
        Assert.Contains("item.hardwareStatus !==", script);
        Assert.DoesNotContain("顯示 pending", view);
        Assert.Contains("data-hardware-status", view);
    }

    private static string FindRepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "AevryndWeb.slnx"))) return directory.FullName;
            directory = directory.Parent;
        }
        throw new DirectoryNotFoundException("Repository root was not found.");
    }
}
