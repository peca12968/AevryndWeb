using System.Text.Json;
using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsDispatchProjectionTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 5, 8, 10, 0, TimeSpan.Zero);
    private static object Comment(long id, string body, string at = "2026-09-05T07:00:00Z", string login = OperationsDispatchProjection.OwnerLogin) =>
        new { id, body, created_at = at, issue_url = OperationsDispatchProjection.IssueUrl, author_association = "OWNER", user = new { login, id = OperationsDispatchProjection.OwnerId } };
    private static string Command(string id, string extra = "", string node = "TAICHUNG") =>
        $"[AEVRYND-BRIDGE]\n[MAIN_COMMAND]\nCOMMAND_ID: {id}\nTARGET: {node}\nTASK: 驗證合法派遣來源\n{extra}\n[/MAIN_COMMAND]\n[/AEVRYND-BRIDGE]";
    private static string Reply(string id, string status, string extra = "", string node = "TAICHUNG") =>
        $"[AEVRYND-BRIDGE]\nNODE: {node}\nCOMMAND_ID: {id}\nSTATUS: {status}\n{extra}\n[/AEVRYND-BRIDGE]";
    private static OperationsDispatchDocument Parse(params object[] comments) => OperationsDispatchProjection.ReadDocument(
        OperationsDispatchProjection.BuildJson(JsonSerializer.Serialize(comments), null, Now));

    [Fact]
    public void BareBridgeAcknowledgementAndReportPreserveEventTimes()
    {
        var result = Parse(Comment(1, Command("WORK-01")), Comment(2, Reply("WORK-01", "ACK", "COMMENT_ID: 1"), "2026-09-05T07:01:00Z"),
            Comment(3, Reply("WORK-01", "NEEDS_MAIN_DECISION"), "2026-09-05T07:02:00Z"));
        var task = Assert.Single(result.Tasks);
        Assert.Equal("unconfirmed", task.State); Assert.Equal(Now.AddMinutes(-69), task.AcknowledgedAt);
        Assert.Equal(Now.AddMinutes(-68), task.UpdatedAt); Assert.Null(task.EndedAt);
        Assert.Contains("NEEDS_MAIN_DECISION", task.Reason); Assert.Equal("驗證合法派遣來源", task.Title);
    }

    [Fact]
    public void GenerationTwoSupersedesCrossNodeWithoutCompletingOldProcess()
    {
        var result = Parse(Comment(1, Command("TC-01", "WORK_KEY: WORK\nGENERATION: 1\nACK_DEADLINE_SECONDS: 300")),
            Comment(2, Command("TY-02", "WORK_KEY: WORK\nGENERATION: 2\nSUPERSEDES_COMMAND_ID: TC-01\nDEPENDS_ON_COMMAND_ID: GPU-01", "TAOYUAN"), "2026-09-05T07:06:00Z"));
        Assert.Equal("superseded", result.Tasks.Single(task => task.Id == "TC-01").State);
        Assert.Equal("queued", result.Tasks.Single(task => task.Id == "TY-02").State);
        Assert.Equal("GPU-01", Assert.Single(result.Tasks.Single(task => task.Id == "TY-02").DependsOn));
    }

    [Fact]
    public void TimeoutAndLateAcknowledgementDoNotInventCompletionOrReviveTerminal()
    {
        var result = Parse(Comment(1, Command("WORK-01", "ACK_DEADLINE_SECONDS: 300")),
            Comment(2, Reply("WORK-01", "COMPLETED"), "2026-09-05T07:01:00Z"),
            Comment(3, Reply("WORK-01", "ACK", "COMMENT_ID: 1"), "2026-09-05T07:02:00Z"));
        Assert.Equal("completed", Assert.Single(result.Tasks).State);
        var queued = Parse(Comment(1, Command("WAIT-01", "ACK_DEADLINE_SECONDS: 300")));
        Assert.Equal("queued", Assert.Single(queued.Tasks).State); Assert.Null(queued.Tasks[0].EndedAt);
    }

    [Fact]
    public void AmbiguousReusedCommandRequiresExplicitCommandReferenceOrGeneration()
    {
        var result = Parse(Comment(1, Command("WORK-01", "GENERATION: 1")),
            Comment(2, Command("WORK-01", "GENERATION: 2"), "2026-09-05T07:01:00Z"),
            Comment(3, Reply("WORK-01", "FAILED"), "2026-09-05T07:02:00Z"),
            Comment(4, Reply("WORK-01", "ACK", "COMMENT_ID: 2\nGENERATION: 2"), "2026-09-05T07:03:00Z"));
        Assert.Equal("queued", result.Tasks.Single(task => task.Generation == 1).State);
        Assert.Equal("acknowledged", result.Tasks.Single(task => task.Generation == 2).State);
        Assert.Equal(1, result.RejectedEvents);
    }

    [Theory]
    [InlineData("STATUS: ACK\nSTATUS: FAILED")]
    [InlineData("status: ACK")]
    public void MalformedFieldsDoNotAdvanceWork(string status)
    {
        var reply = "[AEVRYND-BRIDGE]\nNODE: TAICHUNG\nCOMMAND_ID: WORK-01\n" + status + "\n[/AEVRYND-BRIDGE]";
        var result = Parse(Comment(1, Command("WORK-01")), Comment(2, reply, "2026-09-05T07:01:00Z"));
        Assert.Equal("queued", Assert.Single(result.Tasks).State); Assert.Equal(1, result.RejectedEvents);
    }

    [Fact]
    public void UntrustedOrIncompleteWrapperCannotDeclareWork()
    {
        Assert.Empty(Parse(Comment(1, Command("WORK-01"), login: "other")).Tasks);
        Assert.Empty(Parse(Comment(1, Command("WORK-01").Replace("[/AEVRYND-BRIDGE]", ""))).Tasks);
    }

    [Fact]
    public void CompleteMainFixtureIncludesLatestTasksAndRealFailover()
    {
        var path = Environment.GetEnvironmentVariable("AEVRYND_DISPATCH_FIXTURE");
        Assert.False(string.IsNullOrEmpty(path), "AEVRYND_DISPATCH_FIXTURE is required for the recorded 520-comment integration fixture.");
        Assert.Equal("F4CE34049212168F4F8D8C30E2694D918803EB120566F26B44A15E4D22003E4B",
            Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(path!))));
        var result = OperationsDispatchProjection.ReadDocument(OperationsDispatchProjection.BuildJson(File.ReadAllText(path), null, Now));
        Assert.Contains(result.Tasks, task => task.Id == "HLOD-HOOKS-ON-GPU-GATES-TAOYUAN-20260905-12" && task.State == "unconfirmed" && task.EventCommentId == 5550432812);
        Assert.Contains(result.Tasks, task => task.Id == "GAMEPLAY-HLOD-TRANSITION-FOCUSED-TAICHUNG-20260905-21" && task.State == "superseded");
        Assert.Contains(result.Tasks, task => task.Id == "GAMEPLAY-HLOD-TRANSITION-FOCUSED-TAOYUAN-20260905-21-G2" && task.Generation == 2);
        Assert.Contains(result.Tasks, task => task.Id == "HLOD-SELECTOR-PERF-REPEAT-TAOYUAN-20260905-11");
    }
}
