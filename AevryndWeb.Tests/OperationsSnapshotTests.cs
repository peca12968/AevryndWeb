using AevryndWeb.Security;
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
