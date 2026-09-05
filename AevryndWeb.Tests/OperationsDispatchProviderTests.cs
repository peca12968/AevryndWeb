using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AevryndWeb.Models;
using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsDispatchProviderTests
{
    private static readonly DateTimeOffset Now = DateTimeOffset.Parse("2026-09-05T08:10:00Z");
    private static OperationsViewModel Empty => new([], [], [], Now, true, "current", []);
    private static OperationsDispatchTask Task(string id, string state, string[]? dependencies = null) => new(id, "taichung", 1, id, 1,
        "中文測試任務", "真實事件", state, "接單不等於執行。", dependencies ?? [], null, Now.AddMinutes(-10), Now.AddMinutes(-5),
        Now.AddMinutes(-8), state is "completed" or "failed" ? Now.AddMinutes(-5) : null, Now.AddMinutes(-9), Now.AddMinutes(-1), 2, "OWNER NODE_REPORT 2");
    private static string State(params OperationsDispatchTask[] tasks) => JsonSerializer.Serialize(new OperationsDispatchDocument(1, tasks.Max(task => task.UpdatedAt), tasks, 0), OperationsDispatchProjection.JsonOptions);
    private static string Health(string state, string status = "current", DateTimeOffset? verified = null) => JsonSerializer.Serialize(new
    {
        schemaVersion = 1, stateSha256 = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(state))), status, lastSuccessAt = verified
    });

    [Fact]
    public void SourceVerificationDoesNotRefreshEventOrPromoteAcknowledgement()
    {
        var state = State(Task("WORK-01", "acknowledged"));
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.False(model.Schedule.Stale); Assert.Equal(Now, model.Schedule.VerifiedAt);
        var task = Assert.Single(model.Schedule.Tasks); Assert.Equal("unconfirmed", task.State);
        Assert.Equal(Now.AddMinutes(-5), task.UpdatedAt); Assert.Empty(model.History);
    }

    [Fact]
    public void OfflineOrHashMismatchCannotClaimConnectedSource()
    {
        var state = State(Task("WORK-01", "queued"));
        Assert.True(OperationsDispatchProvider.Project(state, Health(state, "offline", Now), Now, Empty).Schedule.Stale);
        Assert.Throws<JsonException>(() => OperationsDispatchProvider.Project(state, Health("other", verified: Now), Now, Empty));
    }

    [Fact]
    public void ExplicitTerminalOnlyInPastTasksAndDependencyNeedsVerifiedEnd()
    {
        var state = State(Task("WORK-01", "unconfirmed"), Task("WORK-02", "acknowledged", ["WORK-01"]) with { CommandCommentId = 3 });
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.Equal("blocked", model.Schedule.Tasks.Single(task => task.Id == "WORK-02").State); Assert.Empty(model.History);
        state = State(Task("WORK-01", "failed"));
        model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.Empty(model.Schedule.Tasks); Assert.Equal("failed", Assert.Single(model.History).Status);
    }

    [Fact]
    public void ActiveSourceJoinsSingleTaskAndKeepsActualUpdate()
    {
        var state = State(Task("WORK-01", "acknowledged"));
        var work = new OperationsWorkView("WORK-01", "codex", "台中", Now.AddMinutes(-9), Now, null, "running", "目前驗證進度", false);
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty with { ActiveWork = [work] });
        var task = Assert.Single(model.Schedule.Tasks); Assert.Equal("running", task.State); Assert.Equal(Now, task.UpdatedAt);
        Assert.Contains("目前驗證進度", task.Reason);
        model = OperationsDispatchProvider.Unify(Empty with { History = [work with { Status = "blocked", EndedAt = Now }, work with { Status = "completed", EndedAt = Now }] });
        Assert.Equal("completed", Assert.Single(model.History).Status);
    }

    [Fact]
    public void OldTerminalDoesNotHideReusedIdentifierNewGeneration()
    {
        var state = State(Task("WORK-01", "completed"), Task("WORK-01", "queued") with { CommandCommentId = 3, Generation = 2, AssignedAt = Now.AddMinutes(-2), UpdatedAt = Now.AddMinutes(-2), AcknowledgedAt = null, EndedAt = null });
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty with
        { ActiveWork = [new("WORK-01", "codex", "台中", Now.AddMinutes(-1), Now, null, "running", null, false)] });
        Assert.Equal("running", Assert.Single(model.Schedule.Tasks).State); Assert.Single(model.History);
    }
}
