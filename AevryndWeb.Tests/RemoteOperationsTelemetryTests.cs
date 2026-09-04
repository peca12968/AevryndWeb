using System.Globalization;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Runtime.Versioning;
using AevryndWeb.Security;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class RemoteOperationsTelemetryTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 4, 8, 0, 0, TimeSpan.Zero);
    private static readonly ECDsa Key = ECDsa.Create(ECCurve.NamedCurves.nistP256);
    private static readonly byte[] PublicKey = Key.ExportSubjectPublicKeyInfo();
    private static readonly string KeyId = Convert.ToHexString(SHA256.HashData(PublicKey)[..16]).ToLowerInvariant();

    [Fact]
    public void ValidMeasuredHeartbeatBehindProxyIsAcceptedWithoutSourceBinding()
    {
        var store = new FakeTelemetryStore(); var receiver = Receiver(store, requireAddress: false);
        var request = SignedRequest("taichung", Now, 21.5, 62.25, 44);
        var result = receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature,
            IPAddress.Loopback, request.Body, Now);
        Assert.Equal(RemoteTelemetryStatus.Accepted, result.Status);
        Assert.Equal(21.5, store.Node!.CpuPercent);
        Assert.Equal(Now, store.Node.SampledAt);
    }

    [Fact]
    public void EnabledSourceBindingFailsClosedWhenProxyDoesNotRestoreNodeAddress()
    {
        var receiver = Receiver(new FakeTelemetryStore(), requireAddress: true);
        var request = SignedRequest("taichung", Now, 21.5, 62.25, 44);
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature,
                IPAddress.Loopback, request.Body, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Accepted,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce + "A", request.KeyId,
                Sign(request.Node, request.Timestamp, request.Nonce + "A", request.Body),
                IPAddress.Parse("192.168.50.98"), request.Body, Now).Status);
    }

    [Theory]
    [InlineData("unknown")]
    [InlineData("local")]
    public void UnknownAndLocalNodesAreNotRemoteAllowlisted(string node)
    {
        var receiver = Receiver(new FakeTelemetryStore(), false);
        var request = SignedRequest(node, Now, 10, 20, 30);
        Assert.Equal(RemoteTelemetryStatus.Invalid,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature,
                IPAddress.Loopback, request.Body, Now).Status);
    }

    [Fact]
    public void TamperReplayStaleAndEstimatedValuesAreRejected()
    {
        var receiver = Receiver(new FakeTelemetryStore(), false);
        var valid = SignedRequest("taoyuan", Now, 10, 20, 30);
        var tampered = valid.Body.ToArray(); tampered[^2] ^= 1;
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.KeyId, valid.Signature, IPAddress.Loopback, tampered, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Accepted,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.KeyId, valid.Signature, IPAddress.Loopback, valid.Body, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Replay,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.KeyId, valid.Signature, IPAddress.Loopback, valid.Body, Now).Status);

        var stale = SignedRequest("taoyuan", Now.AddMinutes(-2).AddSeconds(-1), 10, 20, 30);
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(stale.Node, stale.Timestamp, stale.Nonce, stale.KeyId, stale.Signature, IPAddress.Loopback, stale.Body, Now).Status);

        var estimated = SignedRequest("taoyuan", Now, 10, 20, 30, "estimated", "abcdefghijklmnopqrstuv1");
        Assert.Equal(RemoteTelemetryStatus.Invalid,
            receiver.Receive(estimated.Node, estimated.Timestamp, estimated.Nonce, estimated.KeyId, estimated.Signature, IPAddress.Loopback, estimated.Body, Now).Status);
    }

    [Fact]
    public void UnknownRevokedAndCrossNodeKeysFailClosed()
    {
        var request = SignedRequest("taichung", Now, 10, 20, 30);
        var unknown = Receiver(new FakeTelemetryStore(), false);
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            unknown.Receive(request.Node, request.Timestamp, request.Nonce, new string('0', 32), request.Signature, IPAddress.Loopback, request.Body, Now).Status);

        var revokedValues = ConfigurationValues(false);
        revokedValues[$"Operations:RemoteTelemetry:Nodes:taichung:Keys:{KeyId}:Revoked"] = "true";
        var revoked = new RemoteOperationsTelemetry(new ConfigurationBuilder().AddInMemoryCollection(revokedValues).Build(), new FakeTelemetryStore(), new MemoryOperationsTelemetryReplayStore());
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            revoked.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature, IPAddress.Loopback, request.Body, Now).Status);

        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            unknown.Receive("taoyuan", request.Timestamp, request.Nonce, request.KeyId, request.Signature, IPAddress.Loopback, request.Body, Now).Status);
    }

    [Fact]
    public void EcdsaModeNeverDowngradesToConfiguredHmacSecret()
    {
        var secret = Enumerable.Range(1, 32).Select(value => (byte)value).ToArray();
        var values = ConfigurationValues(false);
        values["Operations:RemoteTelemetry:Nodes:taichung:Secret"] = Convert.ToBase64String(secret);
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(values).Build();
        var receiver = new RemoteOperationsTelemetry(configuration, new FakeTelemetryStore(), new MemoryOperationsTelemetryReplayStore());
        var request = SignedRequest("taichung", Now, 10, 20, 30);
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/operations/telemetry\ntaichung\n{request.Timestamp}\n{request.Nonce}\n");
        var legacy = "sha256=" + Convert.ToHexString(HMACSHA256.HashData(secret, prefix.Concat(request.Body).ToArray())).ToLowerInvariant();
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, string.Empty, legacy, IPAddress.Loopback, request.Body, Now).Status);
    }

    [Fact]
    public void ExplicitLegacyHmacModeRemainsCompatibleWithoutKeyId()
    {
        var secret = RandomNumberGenerator.GetBytes(32);
        var values = ConfigurationValues(false);
        values["Operations:RemoteTelemetry:Nodes:taichung:AuthenticationMode"] = "HmacSha256";
        values["Operations:RemoteTelemetry:Nodes:taichung:Secret"] = Convert.ToBase64String(secret);
        var receiver = new RemoteOperationsTelemetry(new ConfigurationBuilder().AddInMemoryCollection(values).Build(), new FakeTelemetryStore(), new MemoryOperationsTelemetryReplayStore());
        var request = SignedRequest("taichung", Now, 10, 20, 30);
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/operations/telemetry\ntaichung\n{request.Timestamp}\n{request.Nonce}\n");
        var signature = "sha256=" + Convert.ToHexString(HMACSHA256.HashData(secret, prefix.Concat(request.Body).ToArray())).ToLowerInvariant();
        Assert.Equal(RemoteTelemetryStatus.Accepted,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, string.Empty, signature, IPAddress.Loopback, request.Body, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce + "A", request.KeyId, signature, IPAddress.Loopback, request.Body, Now).Status);
    }

    [Theory]
    [InlineData(-0.1, 20, 30)]
    [InlineData(10, 100.1, 30)]
    [InlineData(10, 20, 101)]
    public void OutOfRangeMetricsAreRejected(double cpu, double ram, double gpu)
    {
        var receiver = Receiver(new FakeTelemetryStore(), false);
        var request = SignedRequest("taichung", Now, cpu, ram, gpu);
        Assert.Equal(RemoteTelemetryStatus.Invalid,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature, IPAddress.Loopback, request.Body, Now).Status);
    }

    [Fact]
    public void MissingMetricAndUnknownPayloadMemberAreRejected()
    {
        var receiver = Receiver(new FakeTelemetryStore(), false);
        var timestamp = Now.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture);
        foreach (var json in new[]
        {
            $"{{\"version\":1,\"nodeId\":\"taichung\",\"measurement\":\"measured\",\"cpuPercent\":10,\"ramPercent\":20,\"sampledUtc\":\"{Now:O}\"}}",
            $"{{\"version\":1,\"nodeId\":\"taichung\",\"measurement\":\"measured\",\"cpuPercent\":10,\"ramPercent\":20,\"gpuPercent\":30,\"sampledUtc\":\"{Now:O}\",\"estimatedCpu\":10}}"
        })
        {
            var body = Encoding.UTF8.GetBytes(json); var nonce = "abcdefghijklmnopqrstuv";
            Assert.Equal(RemoteTelemetryStatus.Invalid,
                receiver.Receive("taichung", timestamp, nonce, KeyId, Sign("taichung", timestamp, nonce, body),
                    IPAddress.Loopback, body, Now).Status);
        }
    }

    [Fact]
    public void SignedWorkAndHistoryAreAcceptedOnlyForAuthenticatedNode()
    {
        var store = new FakeTelemetryStore(); var receiver = Receiver(store, false);
        var active = new OperationsWorkState { Name = "Qwen regression scan", Type = "codex", Host = "taichung", StartedAt = Now.AddMinutes(-5), UpdatedAt = Now, Status = "working" };
        var ended = new OperationsWorkState { Name = "Asset audit", Type = "qwen", Host = "taichung", StartedAt = Now.AddMinutes(-20), UpdatedAt = Now.AddMinutes(-1), EndedAt = Now.AddMinutes(-1), Status = "completed", EvidenceSummary = "Bounded audit completed." };
        var body = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, nodeId = "taichung", measurement = "measured", cpuPercent = 10, ramPercent = 20, gpuPercent = (double?)null, sampledUtc = Now, activeWork = new[] { active }, history = new[] { ended } });
        var timestamp = Now.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture); var nonce = "abcdefghijklmnopqrstuv";
        Assert.Equal(RemoteTelemetryStatus.Accepted, receiver.Receive("taichung", timestamp, nonce, KeyId, Sign("taichung", timestamp, nonce, body), IPAddress.Loopback, body, Now).Status);
        Assert.Single(store.Snapshot!.ActiveWork); Assert.Single(store.Snapshot.History); Assert.Null(store.Snapshot.Node.GpuPercent);

        var contradictory = new OperationsWorkState { Name = active.Name, Type = active.Type, Host = active.Host, StartedAt = active.StartedAt, UpdatedAt = Now, EndedAt = Now, Status = "completed" };
        var contradictionBody = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, nodeId = "taichung", measurement = "measured", cpuPercent = 10, ramPercent = 20, gpuPercent = (double?)null, sampledUtc = Now, activeWork = new[] { active }, history = new[] { contradictory } });
        var contradictionNonce = nonce + "B";
        Assert.Equal(RemoteTelemetryStatus.Invalid, receiver.Receive("taichung", timestamp, contradictionNonce, KeyId, Sign("taichung", timestamp, contradictionNonce, contradictionBody), IPAddress.Loopback, contradictionBody, Now).Status);

        active.Host = "taoyuan"; nonce += "A";
        body = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, nodeId = "taichung", measurement = "measured", cpuPercent = 10, ramPercent = 20, gpuPercent = (double?)null, sampledUtc = Now, activeWork = new[] { active }, history = Array.Empty<OperationsWorkState>() });
        Assert.Equal(RemoteTelemetryStatus.Invalid, receiver.Receive("taichung", timestamp, nonce, KeyId, Sign("taichung", timestamp, nonce, body), IPAddress.Loopback, body, Now).Status);
    }

    [Fact]
    public void ReplayIsRejectedAfterReceiverAndReplayStoreRestart()
    {
        if (!OperatingSystem.IsWindows()) return;
        var directory = SecureTemporaryDirectory();
        try
        {
            var configuration = Configuration(false, directory);
            var request = SignedRequest("taichung", Now, 10, 20, 30);
            var first = new RemoteOperationsTelemetry(configuration, new FakeTelemetryStore(), new FileOperationsTelemetryReplayStore(configuration));
            Assert.Equal(RemoteTelemetryStatus.Accepted, first.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature, IPAddress.Loopback, request.Body, Now).Status);
            var restarted = new RemoteOperationsTelemetry(configuration, new FakeTelemetryStore(), new FileOperationsTelemetryReplayStore(configuration));
            Assert.Equal(RemoteTelemetryStatus.Replay, restarted.Receive(request.Node, request.Timestamp, request.Nonce, request.KeyId, request.Signature, IPAddress.Loopback, request.Body, Now).Status);
        }
        finally { Directory.Delete(directory, true); }
    }

    [Fact]
    public void FileStoreRejectsOutOfOrderCorruptAndOversizedSnapshots()
    {
        if (!OperatingSystem.IsWindows()) return;
        var directory = SecureTemporaryDirectory();
        try
        {
            var configuration = Configuration(false, directory); var store = new FileRemoteTelemetryStore(configuration);
            var completed = new OperationsWorkState { Name = "Persistent audit", Type = "codex", Host = "taichung", StartedAt = Now.AddMinutes(-2), UpdatedAt = Now.AddMinutes(-1), EndedAt = Now.AddMinutes(-1), Status = "completed" };
            var current = new RemoteTelemetrySnapshot(new OperationsNodeState { Id = "taichung", CpuPercent = 10, RamPercent = 20, GpuPercent = null, SampledAt = Now }, [], [completed]);
            Assert.True(store.TryWriteSnapshot(current));
            Assert.True(store.TryReadFreshSnapshot("taichung", Now, out var read)); Assert.Equal(Now, read.Node.SampledAt);
            var older = current with { Node = new OperationsNodeState { Id = "taichung", CpuPercent = 30, RamPercent = 40, GpuPercent = 50, SampledAt = Now.AddSeconds(-1) } };
            Assert.False(store.TryWriteSnapshot(older));
            var later = new RemoteTelemetrySnapshot(new OperationsNodeState { Id = "taichung", CpuPercent = 11, RamPercent = 21, GpuPercent = null, SampledAt = Now.AddSeconds(1) }, [], []);
            Assert.True(store.TryWriteSnapshot(later)); Assert.True(store.TryReadFreshSnapshot("taichung", Now.AddSeconds(1), out read)); Assert.Single(read.History);
            var path = Path.Combine(directory, "taichung.json");
            File.WriteAllText(path, "{not-json"); Assert.False(store.TryReadFreshSnapshot("taichung", Now, out _));
            File.WriteAllBytes(path, new byte[131_073]); Assert.False(store.TryReadFreshSnapshot("taichung", Now, out _));
        }
        finally { Directory.Delete(directory, true); }
    }

    [Fact]
    public void FileStoreRejectsCrossHeartbeatResurrectionWithoutChangingStoredSnapshot()
    {
        if (!OperatingSystem.IsWindows()) return;
        var directory = SecureTemporaryDirectory();
        try
        {
            var store = new FileRemoteTelemetryStore(Configuration(false, directory));
            var identity = Now.AddMinutes(-5);
            var completed = new OperationsWorkState { Name = "Stable identity", Type = "codex", Host = "taichung", StartedAt = identity, UpdatedAt = Now.AddMinutes(-1), EndedAt = Now.AddMinutes(-1), Status = "completed" };
            var first = new RemoteTelemetrySnapshot(new OperationsNodeState { Id = "taichung", CpuPercent = 10, RamPercent = 20, SampledAt = Now }, [], [completed]);
            Assert.True(store.TryWriteSnapshot(first));

            var resurrected = new OperationsWorkState { Name = completed.Name, Type = "codex", Host = "taichung", StartedAt = identity, UpdatedAt = Now.AddSeconds(1), Status = "working" };
            var conflicting = new RemoteTelemetrySnapshot(new OperationsNodeState { Id = "taichung", CpuPercent = 99, RamPercent = 99, SampledAt = Now.AddSeconds(1) }, [resurrected], []);
            Assert.False(store.TryWriteSnapshot(conflicting));
            Assert.True(store.TryReadFreshSnapshot("taichung", Now.AddSeconds(1), out var unchanged));
            Assert.Equal(Now, unchanged.Node.SampledAt); Assert.Empty(unchanged.ActiveWork); Assert.Single(unchanged.History);

            var newIdentity = new OperationsWorkState { Name = completed.Name, Type = "codex", Host = "taichung", StartedAt = identity.AddSeconds(1), UpdatedAt = Now.AddSeconds(2), Status = "working" };
            var legitimate = new RemoteTelemetrySnapshot(new OperationsNodeState { Id = "taichung", CpuPercent = 11, RamPercent = 21, SampledAt = Now.AddSeconds(2) }, [newIdentity], []);
            Assert.True(store.TryWriteSnapshot(legitimate));
            Assert.True(store.TryReadFreshSnapshot("taichung", Now.AddSeconds(2), out var updated)); Assert.Single(updated.ActiveWork); Assert.Single(updated.History);
        }
        finally { Directory.Delete(directory, true); }
    }

    private static RemoteOperationsTelemetry Receiver(FakeTelemetryStore store, bool requireAddress)
    {
        return new RemoteOperationsTelemetry(Configuration(requireAddress), store, new MemoryOperationsTelemetryReplayStore());
    }

    private static IConfiguration Configuration(bool requireAddress, string? stateDirectory = null)
    {
        return new ConfigurationBuilder().AddInMemoryCollection(ConfigurationValues(requireAddress, stateDirectory)).Build();
    }

    private static Dictionary<string, string?> ConfigurationValues(bool requireAddress, string? stateDirectory = null)
    {
        return new Dictionary<string, string?>
        {
            ["Operations:RemoteTelemetry:RequireSourceAddress"] = requireAddress.ToString(),
            ["Operations:RemoteTelemetry:Nodes:taichung:Address"] = "192.168.50.98",
            ["Operations:RemoteTelemetry:Nodes:taichung:AuthenticationMode"] = "EcdsaP256",
            [$"Operations:RemoteTelemetry:Nodes:taichung:Keys:{KeyId}:PublicKey"] = Convert.ToBase64String(PublicKey),
            ["Operations:RemoteTelemetry:Nodes:taoyuan:Address"] = "100.89.42.36",
            ["Operations:RemoteTelemetry:Nodes:taoyuan:AuthenticationMode"] = "EcdsaP256",
            [$"Operations:RemoteTelemetry:Nodes:taoyuan:Keys:{KeyId}:PublicKey"] = Convert.ToBase64String(PublicKey),
            ["Operations:RemoteTelemetry:StateDirectory"] = stateDirectory
        };
    }

    [SupportedOSPlatform("windows")]
    private static string SecureTemporaryDirectory()
    {
        var path = Path.Combine(Path.GetTempPath(), "AevryndWeb-tests-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(path);
        var security = new DirectorySecurity(); security.SetAccessRuleProtection(true, false);
        var inheritance = InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit;
        foreach (var sid in new[] { WindowsIdentity.GetCurrent().User!, new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null), new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null) })
            security.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, inheritance, PropagationFlags.None, AccessControlType.Allow));
        new DirectoryInfo(path).SetAccessControl(security); return path;
    }

    private static Signed SignedRequest(string node, DateTimeOffset sampledAt, double cpu, double ram, double gpu,
        string measurement = "measured", string nonce = "abcdefghijklmnopqrstuv")
    {
        var body = JsonSerializer.SerializeToUtf8Bytes(new
        {
            version = 1, nodeId = node, measurement, cpuPercent = cpu, ramPercent = ram,
            gpuPercent = gpu, sampledUtc = sampledAt
        });
        var timestamp = sampledAt.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture);
        return new(node, timestamp, nonce, KeyId, Sign(node, timestamp, nonce, body), body);
    }

    private static string Sign(string node, string timestamp, string nonce, byte[] body)
    {
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/operations/telemetry\n{node}\n{timestamp}\n{nonce}\n");
        var signature = Key.SignData(prefix.Concat(body).ToArray(), HashAlgorithmName.SHA256, DSASignatureFormat.IeeeP1363FixedFieldConcatenation);
        return "ecdsa-p256-sha256=" + Convert.ToBase64String(signature).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    private sealed record Signed(string Node, string Timestamp, string Nonce, string KeyId, string Signature, byte[] Body);
    private sealed class FakeTelemetryStore : IRemoteTelemetryStore
    {
        public OperationsNodeState? Node { get; private set; }
        public RemoteTelemetrySnapshot? Snapshot { get; private set; }
        public bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node) { node = default!; return false; }
        public bool TryWrite(OperationsNodeState node) { Node = node; return true; }
        public bool TryWriteSnapshot(RemoteTelemetrySnapshot snapshot) { Snapshot = snapshot; Node = snapshot.Node; return true; }
    }
}
