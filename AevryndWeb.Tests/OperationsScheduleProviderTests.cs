using System.Text.Json.Nodes;
using AevryndWeb.Models;
using AevryndWeb.Security;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsScheduleProviderTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 5, 4, 0, 0, TimeSpan.Zero);
    private static OperationsViewModel Snapshot => new([], [], [], Now, true, "current", []);
    private static JsonObject Document() => JsonNode.Parse("""
        {"schemaVersion":1,"observedAt":"2026-09-05T04:00:00Z","tasks":[
        {"id":"HLOD-TEST-01","nodeId":"taichung","title":"驗證遠近景切換","description":"確認畫面與測試結果正確。",
        "state":"queued","reason":"等待接單。","dependsOn":[],"assignedAt":"2026-09-05T03:00:00Z","updatedAt":"2026-09-05T03:00:00Z","evidence":"已發布正式命令。"}]}
        """)!.AsObject();

    [Theory]
    [InlineData("queued")][InlineData("acknowledged")][InlineData("running")][InlineData("blocked")][InlineData("unconfirmed")]
    public void ValidStatesArePreservedWithoutGuessingExecution(string state)
    {
        var document = Document(); document["tasks"]![0]!["state"] = state;
        var model = OperationsScheduleProvider.Parse(document.ToJsonString(), Now, Snapshot);
        Assert.True(model.SourceAvailable); Assert.False(model.Stale);
        Assert.Equal(state, Assert.Single(model.Tasks).State);
        Assert.Equal("驗證遠近景切換", model.Tasks[0].Title);
    }

    [Fact]
    public void StaleCatalogRetainsTaskAndOriginalTime()
    {
        var model = OperationsScheduleProvider.Parse(Document().ToJsonString(), Now.AddMinutes(3), Snapshot);
        Assert.True(model.Stale); Assert.True(model.LocalScheduleStale); Assert.Empty(model.Tasks);
        Assert.Equal(Now.AddHours(-1), Assert.Single(model.Catalog).UpdatedAt);
    }

    [Fact]
    public void FreshLocalScheduleRemainsVisible()
    {
        var document = Document(); document["tasks"]![0]!["nodeId"] = "local";
        var model = OperationsScheduleProvider.Parse(document.ToJsonString(), Now, Snapshot);
        Assert.False(model.LocalScheduleStale);
        Assert.Equal("local", Assert.Single(model.Tasks).NodeId);
    }

    [Fact]
    public void UnknownScheduleDiagnosticHasNeutralFailClosedDisplayText()
    {
        var schedule = new OperationsScheduleView(true, false, Now, []) { Diagnostic = "INTERNAL_UNKNOWN_DETAIL secret=value" };
        Assert.Equal("來源狀態待核對；目前僅顯示可驗證資料。", schedule.DisplayDiagnostic);
        Assert.DoesNotContain("INTERNAL", schedule.DisplayDiagnostic);
    }

    [Theory]
    [InlineData("missing")][InlineData("extra")][InlineData("duplicate")][InlineData("node")]
    [InlineData("state")][InlineData("future")][InlineData("null")][InlineData("private")][InlineData("self")]
    public void MalformedCatalogFailsClosed(string mutation)
    {
        var document = Document(); var task = document["tasks"]![0]!.AsObject();
        switch(mutation)
        {
            case "missing": task.Remove("title"); break;
            case "extra": task["shell"]="whoami"; break;
            case "duplicate": document["tasks"]!.AsArray().Add(task.DeepClone()); break;
            case "node": task["nodeId"]="unknown"; break;
            case "state": task["state"]="completed"; break;
            case "future": task["updatedAt"]="2026-09-06T00:00:00Z"; break;
            case "null": task["description"]=null; break;
            case "private": task["evidence"]="C:\\private\\output.log"; break;
            case "self": task["dependsOn"]!.AsArray().Add("HLOD-TEST-01"); break;
        }
        var model = OperationsScheduleProvider.Parse(document.ToJsonString(),Now,Snapshot);
        Assert.False(model.SourceAvailable); Assert.Empty(model.Tasks);
    }

    [Fact]
    public void TerminalOfSameNodeRemovesTaskButDifferentNodeCannot()
    {
        var terminal = new OperationsWorkView("HLOD-TEST-01","codex","桃園",Now.AddMinutes(-50),Now,Now,"completed","明確終態報告",false);
        Assert.Single(OperationsScheduleProvider.Parse(Document().ToJsonString(),Now,Snapshot with {History=[terminal]}).Tasks);
        Assert.Empty(OperationsScheduleProvider.Parse(Document().ToJsonString(),Now,Snapshot with {History=[terminal with {Host="台中"}]}).Tasks);
        Assert.Single(OperationsScheduleProvider.Parse(Document().ToJsonString(),Now,Snapshot with {History=[terminal with {Host="台中",Status="cancelled",EvidenceSummary="工作摘要停止更新；來源未提供結束原因。"}]}).Tasks);
    }

    [Fact]
    public void RemoteWorkingDeclarationIsAcknowledgedNotProcessProof()
    {
        var active = new OperationsWorkView("HLOD-TEST-01","codex","台中",Now.AddMinutes(-50),Now,null,"working",null,false);
        var model = OperationsScheduleProvider.Parse(Document().ToJsonString(),Now,Snapshot with {ActiveWork=[active]});
        Assert.Equal("acknowledged",Assert.Single(model.Tasks).State);
        Assert.Equal(Now,model.Tasks[0].UpdatedAt);
    }

    [Fact]
    public void MissingFileIsUnavailableNotEmptyIdleFleet()
    {
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string,string?>{["Operations:SchedulePath"]=Path.Combine(Path.GetTempPath(),Guid.NewGuid()+".json")}).Build();
        Assert.False(new OperationsScheduleProvider(config).Read(Now,Snapshot).SourceAvailable);
    }

    [Fact]
    public void TerminalFromPreviousGenerationCannotRemoveNewAssignment()
    {
        var previous = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddHours(-2), Now, Now, "completed", "明確終態報告", false);
        Assert.Single(OperationsScheduleProvider.Parse(Document().ToJsonString(), Now, Snapshot with { History = [previous] }).Tasks);
    }

    [Fact]
    public void PreviousGenerationActiveCannotAdvanceNewAssignment()
    {
        var previous = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddHours(-2), Now, null, "working", null, false);
        var result = OperationsScheduleProvider.Parse(Document().ToJsonString(), Now, Snapshot with { ActiveWork = [previous] });
        Assert.Equal("queued", Assert.Single(result.Tasks).State);
        Assert.Equal(Now.AddHours(-1), result.Tasks[0].UpdatedAt);
    }

    [Fact]
    public void AnOlderTerminalDoesNotHideAConfirmedLaterGeneration()
    {
        var terminal = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddMinutes(-50), Now.AddMinutes(-40), Now.AddMinutes(-40), "completed", "明確終態報告", false);
        var active = terminal with { StartedAt = Now.AddMinutes(-30), UpdatedAt = Now, EndedAt = null, Status = "working", EvidenceSummary = null };
        var result = OperationsScheduleProvider.Parse(Document().ToJsonString(), Now, Snapshot with { ActiveWork = [active], History = [terminal] });
        Assert.Equal("acknowledged", Assert.Single(result.Tasks).State);
    }

    [Theory]
    [InlineData("completed")][InlineData("failed")][InlineData("cancelled")]
    public void TerminalCatalogPreservesChineseTitleAndCannotBeRevivedByActiveTelemetry(string state)
    {
        var document = Document(); document["schemaVersion"] = 2; document["tasks"]![0]!["state"] = state;
        var active = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddMinutes(-50), Now, null, "working", null, false);
        var result = OperationsScheduleProvider.Parse(document.ToJsonString(), Now.AddMinutes(3), Snapshot with { ActiveWork = [active] });
        Assert.True(result.Stale); Assert.Empty(result.Tasks); Assert.Single(result.Catalog);
        Assert.Equal("驗證遠近景切換", result.WorkTitle(active));
        Assert.Equal(active.Name, result.WorkTitle(active with { Host = "桃園" }));
        Assert.Equal(active.Name, result.WorkTitle(active with { StartedAt = Now.AddHours(-2) }));
    }

    [Fact]
    public void OnlyMatchingExplicitTerminalExcludesActiveInstance()
    {
        var active = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddMinutes(-50), Now, null, "working", null, false);
        var terminal = active with { EndedAt = Now, Status = "completed", EvidenceSummary = "明確終態報告" };
        Assert.Empty(OperationsScheduleProvider.ReconcileWork(Snapshot with { ActiveWork = [active], History = [terminal] }).ActiveWork);
        foreach (var different in new[] { terminal with { Host = "桃園" }, terminal with { Name = "OTHER" }, terminal with { StartedAt = active.StartedAt.AddMinutes(-1) }, terminal with { EvidenceSummary = "工作摘要停止更新；來源未提供結束原因。" } })
            Assert.Single(OperationsScheduleProvider.ReconcileWork(Snapshot with { ActiveWork = [active], History = [different] }).ActiveWork);
        Assert.Single(OperationsScheduleProvider.ReconcileWork(Snapshot with { SourceAvailable = false, ActiveWork = [active], History = [terminal] }).ActiveWork);
    }

    [Fact]
    public void AuthoritativePendingMainValidationIsNotOverriddenBySameTimeTelemetryTerminal()
    {
        var document = Document(); document["schemaVersion"] = 2;
        document["tasks"]![0]!["state"] = "blocked"; document["tasks"]![0]!["updatedAt"] = "2026-09-05T04:00:00Z";
        var terminal = new OperationsWorkView("HLOD-TEST-01", "codex", "台中", Now.AddMinutes(-50), Now, Now, "failed", "節點回報等待主機驗收", false);
        var result = OperationsScheduleProvider.Parse(document.ToJsonString(), Now, Snapshot with { History = [terminal] });
        Assert.Equal("unconfirmed", Assert.Single(result.Tasks).State);
        Assert.Contains("來源狀態衝突", result.Tasks[0].Reason);
        Assert.Equal(Now, result.Tasks[0].UpdatedAt);
        Assert.Equal("failed", terminal.Status);
    }

    [Fact]
    public void VerifiedSourceTimeDoesNotRewriteTaskEventTime()
    {
        var document = Document(); document["schemaVersion"] = 2;
        document["verifiedAt"] = "2026-09-05T04:03:00Z";
        var result = OperationsScheduleProvider.Parse(document.ToJsonString(), Now.AddMinutes(3), Snapshot);
        Assert.False(result.Stale); Assert.Equal(Now, result.ObservedAt);
        Assert.Equal(Now.AddHours(-1), Assert.Single(result.Tasks).UpdatedAt);
        Assert.True(OperationsScheduleProvider.Parse(document.ToJsonString(), Now.AddMinutes(6), Snapshot).Stale);
    }
}
