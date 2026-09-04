using AevryndWeb.Security;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging.Abstractions;
using System.Reflection;
using System.Runtime.Versioning;
using System.Text.Json;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsSnapshotTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 4, 8, 0, 0, TimeSpan.Zero);

    [Fact]
    public void ValidSnapshotPreservesMeasuredValuesAndMarksMissingNodesUnavailable()
    {
        var document = ValidDocument();
        Assert.True(OperationsSnapshotSchema.TryNormalize(document, Now, out var model));
        Assert.True(model.SourceAvailable);
        Assert.Equal(3, model.Nodes.Count);
        Assert.Equal(27.4, model.Nodes.Single(node => node.Id == "local").CpuPercent);
        Assert.Null(model.Nodes.Single(node => node.Id == "taichung").CpuPercent);
        Assert.Null(model.Nodes.Single(node => node.Id == "taoyuan").SampledAt);
        Assert.False(model.ActiveWork.Single().Stale);
        Assert.Single(model.History);
    }

    [Fact]
    public void ExpiredSamplesAndWorkAreMarkedStaleWithoutInventingMeasurements()
    {
        var document = ValidDocument();
        document.SnapshotAt = Now.AddMinutes(-3);
        document.Nodes![0].SampledAt = Now.AddMinutes(-3);
        document.ActiveWork![0].StartedAt = Now.AddMinutes(-20);
        document.ActiveWork![0].UpdatedAt = Now.AddMinutes(-16);
        Assert.True(OperationsSnapshotSchema.TryNormalize(document, Now, out var model));
        Assert.StartsWith("stale", model.SourceStatus, StringComparison.Ordinal);
        Assert.True(model.Nodes[0].Stale);
        Assert.True(model.ActiveWork[0].Stale);
    }

    [Theory]
    [InlineData("https://example.test/evidence")]
    [InlineData("operator@example.test")]
    [InlineData("connected to 192.168.1.2")]
    [InlineData("C:\\secret\\raw.log")]
    public void SensitiveOrAddressShapedEvidenceInvalidatesWholeSnapshot(string evidence)
    {
        var document = ValidDocument();
        document.History![0].EvidenceSummary = evidence;
        Assert.False(OperationsSnapshotSchema.TryNormalize(document, Now, out _));
    }

    [Fact]
    public void UnknownNodeAndInvalidTimelineFailClosed()
    {
        var unknown = ValidDocument();
        unknown.Nodes!.Add(new OperationsNodeState { Id = "unknown", SampledAt = Now });
        Assert.False(OperationsSnapshotSchema.TryNormalize(unknown, Now, out _));

        var invalidTimeline = ValidDocument();
        invalidTimeline.History![0].EndedAt = invalidTimeline.History[0].StartedAt.AddMinutes(-1);
        Assert.False(OperationsSnapshotSchema.TryNormalize(invalidTimeline, Now, out _));
    }

    [Fact]
    public void PublisherAcceptsRelayStatusWithoutOptionalPresentationFieldsAndKeepsStartedIdentity()
    {
        if (!OperatingSystem.IsWindows()) return;
        WithPublisher((publisher, statusPath, _) =>
        {
            File.WriteAllText(statusPath, JsonSerializer.Serialize(new { schemaVersion = 1, task = "Codex relay TAICHUNG SAFE-1", status = "working", startedUtc = Now.AddMinutes(-5), updatedUtc = Now, ttl = 3600 }));
            var first = ReadWork(publisher, Now, null);
            Assert.NotNull(first); Assert.Equal(Now.AddMinutes(-5), first!.StartedAt); Assert.Equal("working", first.Status);

            File.WriteAllText(statusPath, JsonSerializer.Serialize(new { schemaVersion = 1, task = first.Name, status = "blocked", updatedUtc = Now.AddMinutes(1), ttl = 3600 }));
            var continued = ReadWork(publisher, Now.AddMinutes(1), new[] { first });
            Assert.NotNull(continued); Assert.Equal(first.StartedAt, continued!.StartedAt); Assert.Equal("blocked", continued.Status);
        });
    }

    [Theory]
    [InlineData("{\"schemaVersion\":1,\"task\":\"Relay\",\"status\":\"working\",\"updatedUtc\":\"2026-09-04T08:00:00Z\",\"ttl\":3600,\"phase\":\"\"}")]
    [InlineData("{\"schemaVersion\":1,\"task\":\"Relay\",\"status\":\"working\",\"updatedUtc\":\"2026-09-04T08:00:00Z\",\"ttl\":3600,\"progress\":101}")]
    [InlineData("{\"schemaVersion\":1,\"task\":\"Relay\",\"status\":\"working\",\"updatedUtc\":\"2026-09-04T08:00:00Z\",\"ttl\":3600,\"extra\":true}")]
    [InlineData("{\"schemaVersion\":1,\"task\":\"Relay\",\"status\":\"working\",\"startedUtc\":\"2026-09-04T08:01:00Z\",\"updatedUtc\":\"2026-09-04T08:00:00Z\",\"ttl\":3600}")]
    public void PublisherRejectsMalformedOptionalOrUnknownStatusFields(string json)
    {
        if (!OperatingSystem.IsWindows()) return;
        WithPublisher((publisher, statusPath, _) =>
        {
            File.WriteAllText(statusPath, json);
            Assert.Null(ReadWork(publisher, Now, null));
        });
    }

    [Fact]
    public void PublisherReadsDeduplicatedRelayHistoryAndRejectsInvalidWholeDocument()
    {
        if (!OperatingSystem.IsWindows()) return;
        WithPublisher((publisher, _, historyPath) =>
        {
            var started = Now.AddHours(-1);
            var events = new object[]
            {
                new { name="Relay task", type="codex-command-relay", startedAt=started, updatedAt=Now.AddMinutes(-2), endedAt=Now.AddMinutes(-2), status="failed", evidenceSummary="First terminal record" },
                new { name="Relay task", type="codex-command-relay", startedAt=started, updatedAt=Now.AddMinutes(-1), endedAt=Now.AddMinutes(-1), status="completed", evidenceSummary="Latest terminal record" },
                new { name="Other task", type="codex-command-relay", startedAt=started.AddMinutes(1), updatedAt=Now, endedAt=Now, status="cancelled", evidenceSummary=(string?)null }
            };
            File.WriteAllText(historyPath, JsonSerializer.Serialize(new { schemaVersion=1, events }));
            var history = ReadHistory(publisher, Now);
            Assert.Equal(2, history.Count); Assert.Equal("completed", history.Single(item => item.Name == "Relay task").Status);

            File.WriteAllText(historyPath, "{\"schemaVersion\":1,\"events\":[{\"name\":\"Bad\",\"type\":\"codex\",\"startedAt\":\"2026-09-04T08:00:00Z\",\"updatedAt\":\"2026-09-04T08:00:00Z\",\"endedAt\":\"2026-09-04T08:00:00Z\",\"status\":\"working\",\"evidenceSummary\":null}]}" );
            Assert.Empty(ReadHistory(publisher, Now));
            File.WriteAllText(historyPath, "{\"schemaVersion\":1,\"events\":null}");
            Assert.Empty(ReadHistory(publisher, Now));
        });
    }

    [Fact]
    public void PublisherMarksDisappearedActiveAsCancelledWithoutGuessingSuccess()
    {
        var previous = new OperationsWorkState { Name = "Expired relay", Type = "codex", Host = "local", StartedAt = Now.AddMinutes(-20), UpdatedAt = Now.AddMinutes(-16), Status = "working" };
        var history = new List<OperationsWorkState>();
        var method = typeof(OperationsTelemetryPublisher).GetMethod("AppendEndedCodexWork", BindingFlags.Static | BindingFlags.NonPublic)!;
        method.Invoke(null, new object?[] { new[] { previous }, null, Now, history });
        var ended = Assert.Single(history);
        Assert.Equal("cancelled", ended.Status); Assert.NotEqual("completed", ended.Status); Assert.NotEqual("failed", ended.Status);
    }

    [Fact]
    public void PublisherHistoryMergeIsBoundedToNewestFiveHundredIdentities()
    {
        var incoming = Enumerable.Range(0, 501).Select(index => new OperationsWorkState
        {
            Name = $"Task {index}", Type = "codex-command-relay", Host = "local", StartedAt = Now.AddMinutes(index),
            UpdatedAt = Now.AddMinutes(index), EndedAt = Now.AddMinutes(index), Status = "completed"
        }).ToList();
        var method = typeof(OperationsTelemetryPublisher).GetMethod("MergeHistory", BindingFlags.Static | BindingFlags.NonPublic)!;
        var merged = (List<OperationsWorkState>)method.Invoke(null, new object?[] { Array.Empty<OperationsWorkState>(), incoming })!;
        Assert.Equal(500, merged.Count); Assert.DoesNotContain(merged, item => item.Name == "Task 0"); Assert.Contains(merged, item => item.Name == "Task 500");
    }

    private static OperationsWorkState? ReadWork(OperationsTelemetryPublisher publisher, DateTimeOffset now, IReadOnlyCollection<OperationsWorkState>? previous)
    {
        var method = typeof(OperationsTelemetryPublisher).GetMethod("ReadCodexWork", BindingFlags.Instance | BindingFlags.NonPublic)!;
        return (OperationsWorkState?)method.Invoke(publisher, new object?[] { now, previous });
    }

    private static List<OperationsWorkState> ReadHistory(OperationsTelemetryPublisher publisher, DateTimeOffset now)
    {
        var method = typeof(OperationsTelemetryPublisher).GetMethod("ReadCodexHistory", BindingFlags.Instance | BindingFlags.NonPublic)!;
        return (List<OperationsWorkState>)method.Invoke(publisher, new object[] { now })!;
    }

    [SupportedOSPlatform("windows")]
    private static void WithPublisher(Action<OperationsTelemetryPublisher, string, string> action)
    {
        var directory = Path.Combine(Path.GetTempPath(), "Aevrynd-publisher-tests-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
        try
        {
            var status = Path.Combine(directory, "status.json"); var history = Path.Combine(directory, "operations-history.json");
            var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Operations:StatePath"] = Path.Combine(directory, "operations-state.json"),
                ["Operations:CodexStatusPath"] = status,
                ["Operations:CodexHistoryPath"] = history
            }).Build();
            action(new OperationsTelemetryPublisher(configuration, NullLogger<OperationsTelemetryPublisher>.Instance), status, history);
        }
        finally { Directory.Delete(directory, true); }
    }

    private static OperationsStateDocument ValidDocument() => new()
    {
        Version = 1,
        SnapshotAt = Now.AddSeconds(-20),
        Nodes =
        [
            new OperationsNodeState { Id = "local", CpuPercent = 27.44, RamPercent = 61.2, GpuPercent = 18, SampledAt = Now.AddSeconds(-20) },
            new OperationsNodeState { Id = "taichung", SampledAt = Now.AddSeconds(-20) }
        ],
        ActiveWork =
        [
            new OperationsWorkState { Name = "Bloom verification", Type = "engine test", Host = "local", StartedAt = Now.AddMinutes(-10), UpdatedAt = Now.AddMinutes(-1), Status = "working" }
        ],
        History =
        [
            new OperationsWorkState { Name = "HLOD slice", Type = "engine validation", Host = "local", StartedAt = Now.AddHours(-2), UpdatedAt = Now.AddHours(-1), EndedAt = Now.AddHours(-1), Status = "completed", EvidenceSummary = "Fresh validation passed with zero debug findings." }
        ]
    };
}
