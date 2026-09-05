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
    private static object Comment(long id, string body, string at = "2026-09-05T07:00:00Z", string login = OperationsDispatchProjection.OwnerLogin) =>
        new { id, body, created_at = at, issue_url = OperationsDispatchProjection.IssueUrl, author_association = "OWNER", user = new { login, id = OperationsDispatchProjection.OwnerId } };
    private static string Command(string id, string extra = "", string node = "TAICHUNG") =>
        $"[AEVRYND-BRIDGE]\n[MAIN_COMMAND]\nCOMMAND_ID: {id}\nTARGET: {node}\nTASK: 驗證派工快照校正\n{extra}\n[/MAIN_COMMAND]\n[/AEVRYND-BRIDGE]";
    private static string Report(string id, string status, string node = "TAICHUNG") =>
        $"[AEVRYND-BRIDGE]\nNODE: {node}\nCOMMAND_ID: {id}\nSTATUS: {status}\n[/AEVRYND-BRIDGE]";
    private static string ArchivedCommand(string id, string node = "TAICHUNG", string extra = "") =>
        $"[AEVRYND-ARCHIVED-BRIDGE]\n[ARCHIVED_COMMAND]\nCOMMAND_ID: {id}\nTARGET: {node}\n{extra}\n[/ARCHIVED_COMMAND]\n[/AEVRYND-ARCHIVED-BRIDGE]";
    private static string ProjectComments(string? previous, params object[] comments) =>
        OperationsDispatchProjection.BuildJson(JsonSerializer.Serialize(comments), previous, Now);

    [Fact]
    public void SourceVerificationDoesNotRefreshEventOrPromoteAcknowledgement()
    {
        var state = State(Task("WORK-01", "acknowledged"));
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.False(model.Schedule.Stale); Assert.Equal(Now, model.Schedule.VerifiedAt);
        Assert.Empty(model.Schedule.Tasks); Assert.Empty(model.History);
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
        var state = State(Task("WORK-01", "unconfirmed"), Task("WORK-02", "acknowledged", ["WORK-01"]) with { CommandCommentId = 3, LeaseExpiresAt = Now.AddMinutes(5) });
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

    [Fact]
    public void LiveScheduleExcludesReviewReportsAndKeepsOnlyLatestGeneration()
    {
        var state = State(
            Task("OLD-REPORT", "unconfirmed"),
            Task("WAITING-REVIEW", "blocked") with { CommandCommentId = 2 },
            Task("WORK-G1", "queued") with { CommandCommentId = 3, WorkKey = "SAME-WORK", AckDeadline = Now.AddMinutes(5) },
            Task("WORK-G2", "queued") with { CommandCommentId = 4, WorkKey = "SAME-WORK", Generation = 2, AssignedAt = Now.AddMinutes(-1), UpdatedAt = Now.AddMinutes(-1), AckDeadline = Now.AddMinutes(5), AcknowledgedAt = null, LeaseExpiresAt = null });

        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);

        var task = Assert.Single(model.Schedule.Tasks);
        Assert.Equal("WORK-G2", task.Id);
        Assert.Equal("queued", task.State);
        Assert.Contains(model.Schedule.Catalog, item => item.Id == "OLD-REPORT");
        Assert.Contains(model.Schedule.Catalog, item => item.Id == "WAITING-REVIEW");
    }

    [Fact]
    public void ArchiveCutoffSupersedesOnlyOldNonTerminalTasksOnSameNode()
    {
        var state = ProjectComments(null,
            Comment(8, Command("ALREADY-DONE")),
            Comment(9, Report("ALREADY-DONE", "COMPLETED"), "2026-09-05T07:01:00Z"),
            Comment(10, Command("OLDER"), "2026-09-05T07:02:00Z"),
            Comment(11, Command("AT-CUTOFF"), "2026-09-05T07:03:00Z"),
            Comment(12, Command("OTHER-NODE", node: "TAOYUAN"), "2026-09-05T07:04:00Z"),
            Comment(13, Command("NEWER"), "2026-09-05T07:05:00Z"),
            Comment(20, Command("SNAPSHOT-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 11"), "2026-09-05T07:06:00Z"));
        var document = OperationsDispatchProjection.ReadDocument(state);

        Assert.Equal("completed", document.Tasks.Single(task => task.Id == "ALREADY-DONE").State);
        foreach (var id in new[] { "OLDER", "AT-CUTOFF" })
        {
            var archived = document.Tasks.Single(task => task.Id == id);
            Assert.Equal("superseded", archived.State);
            Assert.NotNull(archived.EndedAt);
            Assert.Contains("MAIN_COMMAND 20", archived.Evidence);
        }
        Assert.Equal("queued", document.Tasks.Single(task => task.Id == "OTHER-NODE").State);
        Assert.Equal("queued", document.Tasks.Single(task => task.Id == "NEWER").State);

        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.DoesNotContain(model.Schedule.Tasks, task => task.Id is "OLDER" or "AT-CUTOFF");
        Assert.Contains(model.Schedule.Catalog, task => task.Id == "OLDER" && task.State == "superseded" && task.Evidence.Contains("MAIN_COMMAND 20", StringComparison.Ordinal));
        Assert.Contains(model.History, task => task.Name == "ALREADY-DONE" && task.Status == "completed");
    }

    [Theory]
    [InlineData("0")]
    [InlineData("-1")]
    [InlineData("20")]
    [InlineData("21")]
    [InlineData("not-a-number")]
    public void InvalidArchiveCutoffRejectsWholeTrustedCommand(string cutoff)
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, Command("OLDER")),
            Comment(20, Command("INVALID-CORRECTION", $"ARCHIVE_THROUGH_COMMENT_ID: {cutoff}"), "2026-09-05T07:01:00Z")));

        Assert.Equal("queued", Assert.Single(document.Tasks).State);
        Assert.Equal(1, document.RejectedEvents);
    }

    [Fact]
    public void UntrustedArchiveEnvelopeCannotChangeExistingTask()
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, Command("OLDER")),
            Comment(20, Command("UNTRUSTED-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z", "other")));

        Assert.Equal("queued", Assert.Single(document.Tasks).State);
    }

    [Fact]
    public void ArchiveFieldOutsideMainCommandIsRejected()
    {
        var hostileReport = "[AEVRYND-BRIDGE]\nNODE: TAICHUNG\nCOMMAND_ID: OLDER\nSTATUS: ACK\nARCHIVE_THROUGH_COMMENT_ID: 10\n[/AEVRYND-BRIDGE]";
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, Command("OLDER")), Comment(20, hostileReport, "2026-09-05T07:01:00Z")));

        Assert.Equal("queued", Assert.Single(document.Tasks).State);
        Assert.Equal(1, document.RejectedEvents);
    }

    [Fact]
    public void ArchiveCutoffIsReappliedAfterPreviousSnapshotMerge()
    {
        var old = Task("OLD-SNAPSHOT", "queued") with
        {
            CommandCommentId = 10, AssignedAt = Now.AddMinutes(-10), UpdatedAt = Now.AddMinutes(-5),
            AcknowledgedAt = null, EndedAt = null
        };
        var priorTerminal = Task("PRIOR-TERMINAL", "failed") with { CommandCommentId = 11 };
        var previous = State(old, priorTerminal);
        var state = ProjectComments(previous,
            Comment(20, Command("SNAPSHOT-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 11"), "2026-09-05T08:06:00Z"));
        var document = OperationsDispatchProjection.ReadDocument(state);

        var archived = document.Tasks.Single(task => task.Id == "OLD-SNAPSHOT");
        Assert.Equal("superseded", archived.State);
        Assert.Equal(20, archived.EventCommentId);
        Assert.NotNull(archived.EndedAt);
        Assert.Equal("failed", document.Tasks.Single(task => task.Id == "PRIOR-TERMINAL").State);
    }

    [Fact]
    public void RejectionHorizonRequiresBothNodesAndKeepsEventsAfterMinimumCutoff()
    {
        const string malformed = "[MAIN_COMMAND]\nCOMMAND_ID: MALFORMED";
        var both = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(5, malformed),
            Comment(9, malformed),
            Comment(11, malformed),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 8", "TAOYUAN"), "2026-09-05T07:02:00Z")));

        // 全球 horizon 採兩節點最新 cutoff 的較小值 8：5 被封存，9 與 11 仍屬當前拒絕事件。
        Assert.Equal(2, both.RejectedEvents);

        var oneNode = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(5, malformed),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z")));
        Assert.Equal(1, oneNode.RejectedEvents);
    }

    [Fact]
    public void CompleteDualNodeHorizonCanClearOnlyHistoricalRejections()
    {
        const string malformed = "[MAIN_COMMAND]\nCOMMAND_ID: MALFORMED";
        var state = ProjectComments(null,
            Comment(5, malformed),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"));
        var document = OperationsDispatchProjection.ReadDocument(state);

        Assert.Equal(0, document.RejectedEvents);
        var model = OperationsDispatchProvider.Project(state, Health(state, verified: Now), Now, Empty);
        Assert.False(model.Schedule.Stale);
        Assert.Equal("遠端派工來源已完成核對。", model.Schedule.DisplayDiagnostic);
    }

    [Fact]
    public void InvalidArchiveCommandCannotHideItselfBehindDualNodeHorizon()
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(9, Command("INVALID-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 9")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z")));

        Assert.Equal(1, document.RejectedEvents);
        Assert.DoesNotContain(document.Tasks, task => task.Id == "INVALID-CORRECTION");
    }

    [Fact]
    public void LateReportForExactTrustedArchivedCommandIsIgnored()
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));

        Assert.Equal(0, document.RejectedEvents);
        Assert.DoesNotContain(document.Tasks, task => task.Id == "HISTORICAL-WORK");
    }

    [Theory]
    [InlineData("UNKNOWN", "TAICHUNG")]
    [InlineData("HISTORICAL-WORK", "TAOYUAN")]
    public void UnknownOrWrongNodeLateReportRemainsRejected(string commandId, string node)
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report(commandId, "NEEDS_MAIN_DECISION", node), "2026-09-05T07:03:00Z")));

        Assert.Equal(1, document.RejectedEvents);
    }

    [Fact]
    public void UntrustedArchiveOrMalformedLateReplyRemainsRejected()
    {
        var untrusted = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, ArchivedCommand("HISTORICAL-WORK"), login: "other"),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));
        Assert.Equal(1, untrusted.RejectedEvents);

        var missingStatus = "[AEVRYND-BRIDGE]\nNODE: TAICHUNG\nCOMMAND_ID: HISTORICAL-WORK\n[/AEVRYND-BRIDGE]";
        var malformed = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, missingStatus, "2026-09-05T07:03:00Z")));
        Assert.Equal(1, malformed.RejectedEvents);
    }

    [Fact]
    public void FakeOrDuplicateArchivedWrapperCannotAuthorizeLateReport()
    {
        var duplicate = ArchivedCommand("HISTORICAL-WORK", extra: "COMMAND_ID: HISTORICAL-WORK");
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, duplicate),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));

        Assert.Equal(2, document.RejectedEvents);

        var fake = ArchivedCommand("HISTORICAL-WORK").Replace("[/AEVRYND-ARCHIVED-BRIDGE]", "[/FAKE]");
        document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, fake),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));
        Assert.Equal(2, document.RejectedEvents);
    }

    [Fact]
    public void DuplicateArchivedCommandIdentityCannotAuthorizeLateReport()
    {
        var document = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(9, ArchivedCommand("HISTORICAL-WORK")),
            Comment(10, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));

        Assert.Equal(1, document.RejectedEvents);
    }

    [Fact]
    public void ArchivedCommandAfterCutoffOrMissingNodeDirectiveFailsClosed()
    {
        var afterCutoff = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(11, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(21, Command("TY-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10", "TAOYUAN"), "2026-09-05T07:02:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));
        Assert.Equal(1, afterCutoff.RejectedEvents);

        var missingNode = OperationsDispatchProjection.ReadDocument(ProjectComments(null,
            Comment(10, ArchivedCommand("HISTORICAL-WORK")),
            Comment(20, Command("TC-CORRECTION", "ARCHIVE_THROUGH_COMMENT_ID: 10"), "2026-09-05T07:01:00Z"),
            Comment(22, Report("HISTORICAL-WORK", "NEEDS_MAIN_DECISION"), "2026-09-05T07:03:00Z")));
        Assert.Equal(1, missingNode.RejectedEvents);
    }

    [Fact]
    public void StaleLocalScheduleCannotMixWithFreshRemoteDispatch()
    {
        var localScheduleJson = JsonSerializer.Serialize(new
        {
            schemaVersion = 2, observedAt = Now.AddMinutes(-10), verifiedAt = Now.AddMinutes(-8),
            tasks = new[] { new
            {
                id = "OLD-LOCAL", nodeId = "local", title = "本機舊工作", description = "等待排程來源更新。",
                state = "running", reason = "舊快照仍標為執行。", dependsOn = Array.Empty<string>(),
                assignedAt = Now.AddMinutes(-20), updatedAt = Now.AddMinutes(-10), evidence = "舊排程快照。"
            } }
        });
        var oldLocal = new OperationsWorkView("OLD-LOCAL", "codex", "本機", Now.AddMinutes(-20), Now.AddMinutes(-9), null, "working", "舊遙測", true);
        var baseModel = Empty with { ActiveWork = [oldLocal] };
        var localSchedule = OperationsScheduleProvider.Parse(localScheduleJson, Now, baseModel);
        Assert.True(localSchedule.LocalScheduleStale); Assert.Empty(localSchedule.Tasks);

        var remoteState = State(Task("FRESH-REMOTE", "queued") with
        {
            CommandCommentId = 30, AssignedAt = Now.AddMinutes(-1), UpdatedAt = Now.AddMinutes(-1),
            AcknowledgedAt = null, EndedAt = null, AckDeadline = Now.AddMinutes(5), LeaseExpiresAt = null
        });
        var mixed = OperationsDispatchProvider.Project(remoteState, Health(remoteState, verified: Now), Now, baseModel with { Schedule = localSchedule });

        Assert.True(mixed.Schedule.LocalScheduleStale);
        Assert.DoesNotContain(mixed.Schedule.Tasks, task => task.NodeId == "local");
        Assert.Contains(mixed.Schedule.Tasks, task => task.Id == "FRESH-REMOTE" && task.NodeId == "taichung");
        Assert.Contains(mixed.Schedule.Catalog, task => task.Id == "OLD-LOCAL");
        Assert.DoesNotContain(mixed.ActiveWork, work => work.Name == "OLD-LOCAL" && !work.Stale);
    }
}
