using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsSchedulePageTests
{
    [Fact]
    public void OperationsPageContainsReadOnlyThreeNodeScheduleContract()
    {
        var root = FindRepositoryRoot();
        var view = File.ReadAllText(Path.Combine(root, "AevryndWeb", "Views", "Operations", "Index.cshtml"));
        var script = File.ReadAllText(Path.Combine(root, "AevryndWeb", "wwwroot", "js", "site.js"));
        var style = File.ReadAllText(Path.Combine(root, "AevryndWeb", "wwwroot", "css", "site.css"));

        Assert.Contains("data-schedule-grid", view);
        Assert.Contains("local", view);
        Assert.Contains("taichung", view);
        Assert.Contains("taoyuan", view);
        Assert.Contains("Model.Schedule.Tasks", view);
        Assert.Contains("本機排程資料待更新", view);
        Assert.Contains("DisplayDiagnostic", view);
        Assert.DoesNotContain("DISPATCH_SOURCE_CURRENT", view);
        Assert.Contains("等待中", view);
        Assert.Contains("先前任務", view);
        Assert.Contains("renderSchedule", script);
        Assert.Contains("model.schedule", script);
        Assert.Contains("openIds", script);
        Assert.Contains("schedule?.observedAt", script);
        Assert.Contains("operations-schedule-grid", style);
        Assert.DoesNotContain("fetch(", view);
    }

    private static string FindRepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "AevryndWeb.slnx"))) return directory.FullName;
            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("AevryndWeb repository root was not found.");
    }
}
