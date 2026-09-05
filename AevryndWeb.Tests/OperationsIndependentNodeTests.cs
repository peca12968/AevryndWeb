using AevryndWeb.Security;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsIndependentNodeTests
{
    [Theory]
    [InlineData(20, "current")]
    [InlineData(40, "stale")]
    public void MissingLocalStateDoesNotHideIndependentlyVerifiedRemote(int age, string availability)
    {
        var now = DateTimeOffset.Parse("2026-09-05T08:30:00Z");
        var diagnostics = new RemoteTelemetryDiagnostics(); diagnostics.Record("taoyuan", now, "WORK_TIMELINE_SCHEMA_REJECTED");
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        { ["Operations:StatePath"] = Path.Combine(Path.GetTempPath(), "aevrynd-absent-" + Guid.NewGuid().ToString("N"), "state.json") }).Build();
        var result = new FileOperationsSnapshotProvider(config, new Store(now.AddSeconds(-age)), diagnostics).Read(now);
        Assert.False(result.SourceAvailable);
        Assert.Equal("unavailable", result.Nodes.Single(node => node.Id == "local").Availability);
        var taichung = result.Nodes.Single(node => node.Id == "taichung");
        Assert.Equal(availability, taichung.Availability); Assert.Equal(7, taichung.CpuPercent); Assert.Equal(now.AddSeconds(-age), taichung.SampledAt);
        var taoyuan = result.Nodes.Single(node => node.Id == "taoyuan"); Assert.Null(taoyuan.CpuPercent);
        Assert.Contains("REMOTE_SAMPLE_EXPIRED", taoyuan.Diagnostic); Assert.Contains("WORK_TIMELINE_SCHEMA_REJECTED", taoyuan.Diagnostic);
        Assert.Contains("台北時間 (UTC+8)", taoyuan.Diagnostic);
    }
    private sealed class Store(DateTimeOffset at) : IRemoteTelemetryStore
    {
        public string ReadDiagnostic(string nodeId, DateTimeOffset now) => "REMOTE_SAMPLE_EXPIRED：已超過兩分鐘。";
        public bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node)
        {
            node = new() { Id = nodeId, CpuPercent = 7, RamPercent = 40.8, GpuPercent = 1, SampledAt = at };
            return nodeId == "taichung";
        }
        public bool TryWrite(OperationsNodeState node) => false;
    }
}
