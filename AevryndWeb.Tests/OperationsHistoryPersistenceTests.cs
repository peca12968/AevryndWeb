using AevryndWeb.Security;
using AevryndWeb.Models;
using Microsoft.Extensions.Configuration;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text.Json;
using System.Runtime.Versioning;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsHistoryPersistenceTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 5, 12, 0, 0, TimeSpan.Zero);

    [Fact]
    public void TerminalHistoryRemainsValidAfterMetricsFreshnessExpires()
    {
        var terminal = new OperationsWorkState
        {
            Name = "HLOD audit", Type = "engine", Host = "taichung",
            StartedAt = Now.AddHours(-3), UpdatedAt = Now.AddHours(-2), EndedAt = Now.AddHours(-2),
            Status = "completed", EvidenceSummary = "verified"
        };

        Assert.True(OperationsSnapshotSchema.TryNormalizeRemoteWork([], [terminal], "taichung", Now, out _, out var history));
        Assert.Single(history);
        Assert.Equal("completed", history[0].Status);
    }

    [Fact]
    public void PersistedHistoryRejectsActiveOrWrongNodeEntries()
    {
        var active = new OperationsWorkState
        {
            Name = "still running", Type = "engine", Host = "taichung",
            StartedAt = Now.AddMinutes(-5), UpdatedAt = Now.AddMinutes(-1), Status = "working"
        };
        var wrongNode = new OperationsWorkState
        {
            Name = active.Name, Type = active.Type, Host = "taoyuan", StartedAt = active.StartedAt,
            UpdatedAt = Now, EndedAt = Now, Status = "completed", EvidenceSummary = "verified"
        };

        Assert.False(OperationsSnapshotSchema.TryNormalizeRemoteWork([], [active], "taichung", Now, out _, out _));
        Assert.False(OperationsSnapshotSchema.TryNormalizeRemoteWork([], [wrongNode], "taichung", Now, out _, out _));
    }

    [Fact]
    public void PersistedHistoryRejectsInvalidTerminalReceiptShape()
    {
        var invalid = new OperationsWorkState
        {
            Name = "invalid", Type = "engine", Host = "taichung",
            StartedAt = Now.AddMinutes(-4), UpdatedAt = Now.AddMinutes(-3), EndedAt = Now.AddMinutes(-2),
            Status = "completed", EvidenceSummary = "https://untrusted.example/receipt"
        };

        Assert.False(OperationsSnapshotSchema.TryNormalizeRemoteWork([], [invalid], "taichung", Now, out _, out _));
    }

    [Fact]
    [SupportedOSPlatform("windows")]
    public void FileStoreAndProviderKeepTerminalHistoryAcrossExpiredMetricsAndRestart()
    {
        if (!OperatingSystem.IsWindows()) return;
        var root = Path.Combine(Path.GetTempPath(), "Aevrynd-history-runtime-" + Guid.NewGuid().ToString("N"));
        var remoteDirectory = Path.Combine(root, "remote");
        var stateDirectory = Path.Combine(root, "state");
        Directory.CreateDirectory(remoteDirectory); Directory.CreateDirectory(stateDirectory);
        try
        {
            SecureDirectory(remoteDirectory); SecureDirectory(stateDirectory);
            var now = DateTimeOffset.UtcNow;
            var terminal = new OperationsWorkState
            {
                Name = "REMOTE-TERMINAL-01", Type = "engine", Host = "taichung",
                StartedAt = now.AddMinutes(-20), UpdatedAt = now.AddMinutes(-18), EndedAt = now.AddMinutes(-18),
                Status = "completed", EvidenceSummary = "fresh terminal receipt"
            };
            var freshNode = new OperationsNodeState { Id = "taichung", CpuPercent = 41, RamPercent = 52, GpuPercent = 10, SampledAt = now };
            var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Operations:RemoteTelemetry:StateDirectory"] = remoteDirectory,
                ["Operations:StatePath"] = Path.Combine(stateDirectory, "operations-state.json")
            }).Build();
            var store = new FileRemoteTelemetryStore(configuration);
            Assert.True(store.TryWriteSnapshot(new RemoteTelemetrySnapshot(freshNode, [], [terminal])));
            Assert.True(store.TryReadFreshSnapshot("taichung", now, out _));
            Assert.False(store.TryReadFreshSnapshot("taichung", now.AddMinutes(3), out _));
            Assert.True(store.TryReadHistory("taichung", now, out var persisted));
            Assert.Single(persisted);

            var localDocument = new OperationsStateDocument
            {
                Version = 1, SnapshotAt = now,
                Nodes = [new OperationsNodeState { Id = "local", CpuPercent = 12, RamPercent = 34, GpuPercent = 5, SampledAt = now }, freshNode],
                ActiveWork = [], History = []
            };
            var statePath = Path.Combine(stateDirectory, "operations-state.json");
            File.WriteAllText(statePath, JsonSerializer.Serialize(localDocument)); SecureFile(statePath);
            var provider = new FileOperationsSnapshotProvider(configuration, store);
            var model = provider.Read(now.AddMinutes(3));
            Assert.Equal("unavailable", model.Nodes.Single(node => node.Id == "taichung").Availability);
            var remoteNode = model.Nodes.Single(node => node.Id == "taichung");
            Assert.Null(remoteNode.CpuPercent); Assert.Null(remoteNode.RamPercent); Assert.Null(remoteNode.GpuPercent); Assert.Null(remoteNode.SampledAt);
            Assert.Contains(model.History, item => item.Name == terminal.Name && item.Host == "台中");
            var schedule = $$"""{"schemaVersion":1,"observedAt":"{{now.AddMinutes(3):O}}","tasks":[{"id":"REMOTE-TERMINAL-01","nodeId":"taichung","title":"遠端終態","description":"驗證","state":"running","reason":"等待","dependsOn":[],"assignedAt":"{{terminal.StartedAt:O}}","updatedAt":"{{now.AddMinutes(2):O}}","evidence":"receipt"}]}""";
            Assert.Empty(OperationsScheduleProvider.Parse(schedule, now.AddMinutes(3), model).Tasks);

            var restartedStore = new FileRemoteTelemetryStore(configuration);
            var restartedProvider = new FileOperationsSnapshotProvider(configuration, restartedStore);
            var restartedModel = restartedProvider.Read(now.AddMinutes(3));
            Assert.Equal("unavailable", restartedModel.Nodes.Single(node => node.Id == "taichung").Availability);
            Assert.Contains(restartedModel.History, item => item.Name == terminal.Name && item.Host == "台中");
            Assert.True(restartedStore.TryReadHistory("taichung", now.AddMinutes(3), out var afterRestart));
            Assert.Single(afterRestart);

            var remotePath = Path.Combine(remoteDirectory, "taichung.json");
            File.WriteAllText(remotePath, JsonSerializer.Serialize(new RemoteTelemetryEnvelope
            {
                Version = 2, Node = new OperationsNodeState { Id = "unknown", CpuPercent = freshNode.CpuPercent, RamPercent = freshNode.RamPercent, GpuPercent = freshNode.GpuPercent, SampledAt = freshNode.SampledAt }, ActiveWork = [], History = [terminal]
            })); SecureFile(remotePath);
            Assert.False(restartedStore.TryReadHistory("taichung", now.AddMinutes(3), out _));
            File.WriteAllText(remotePath, JsonSerializer.Serialize(new RemoteTelemetryEnvelope
            {
                Version = 2, Node = freshNode, ActiveWork = [], History = [new OperationsWorkState
                {
                    Name = "nonterminal", Type = "engine", Host = "taichung", StartedAt = now.AddMinutes(-2), UpdatedAt = now.AddMinutes(-1), Status = "working"
                }]
            })); SecureFile(remotePath);
            Assert.False(restartedStore.TryReadHistory("taichung", now.AddMinutes(3), out _));
        }
        finally { Directory.Delete(root, true); }
    }

    [Fact]
    public void RemoteTerminalHistoryPreventsScheduleTaskRevival()
    {
        var now = DateTimeOffset.UtcNow;
        var terminal = new OperationsWorkView("REMOTE-TERMINAL-02", "engine", "台中", now.AddMinutes(-10), now.AddMinutes(-8), now.AddMinutes(-8), "completed", "receipt", false);
        var snapshot = new OperationsViewModel([], [], [terminal], now, true, "current", []);
        var schedule = $$"""{"schemaVersion":1,"observedAt":"{{now:O}}","tasks":[{"id":"REMOTE-TERMINAL-02","nodeId":"taichung","title":"遠端終態","description":"驗證","state":"running","reason":"等待","dependsOn":[],"assignedAt":"{{now.AddMinutes(-10):O}}","updatedAt":"{{now.AddMinutes(-9):O}}","evidence":"receipt"}]}""";
        Assert.Empty(OperationsScheduleProvider.Parse(schedule, now, snapshot).Tasks);
    }

    [SupportedOSPlatform("windows")]
    private static void SecureDirectory(string path)
    {
        var current = WindowsIdentity.GetCurrent().User!;
        var security = new DirectorySecurity(); security.SetAccessRuleProtection(true, false);
        foreach (var sid in new[] { current, new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null), new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null) })
            security.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
        new DirectoryInfo(path).SetAccessControl(security);
    }

    [SupportedOSPlatform("windows")]
    private static void SecureFile(string path)
    {
        var current = WindowsIdentity.GetCurrent().User!;
        var security = new FileSecurity(); security.SetAccessRuleProtection(true, false);
        foreach (var sid in new[] { current, new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null), new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null) })
            security.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, AccessControlType.Allow));
        new FileInfo(path).SetAccessControl(security);
    }
}
