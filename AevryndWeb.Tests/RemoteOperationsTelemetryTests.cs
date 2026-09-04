using System.Globalization;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AevryndWeb.Security;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class RemoteOperationsTelemetryTests
{
    private static readonly DateTimeOffset Now = new(2026, 9, 4, 8, 0, 0, TimeSpan.Zero);
    private static readonly byte[] Secret = Enumerable.Range(1, 32).Select(value => (byte)value).ToArray();

    [Fact]
    public void ValidMeasuredHeartbeatBehindProxyIsAcceptedWithoutSourceBinding()
    {
        var store = new FakeTelemetryStore(); var receiver = Receiver(store, requireAddress: false);
        var request = SignedRequest("taichung", Now, 21.5, 62.25, 44);
        var result = receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.Signature,
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
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.Signature,
                IPAddress.Loopback, request.Body, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Accepted,
            receiver.Receive(request.Node, request.Timestamp, request.Nonce + "A",
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
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.Signature,
                IPAddress.Loopback, request.Body, Now).Status);
    }

    [Fact]
    public void TamperReplayStaleAndEstimatedValuesAreRejected()
    {
        var receiver = Receiver(new FakeTelemetryStore(), false);
        var valid = SignedRequest("taoyuan", Now, 10, 20, 30);
        var tampered = valid.Body.ToArray(); tampered[^2] ^= 1;
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.Signature, IPAddress.Loopback, tampered, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Accepted,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.Signature, IPAddress.Loopback, valid.Body, Now).Status);
        Assert.Equal(RemoteTelemetryStatus.Replay,
            receiver.Receive(valid.Node, valid.Timestamp, valid.Nonce, valid.Signature, IPAddress.Loopback, valid.Body, Now).Status);

        var stale = SignedRequest("taoyuan", Now.AddMinutes(-2).AddSeconds(-1), 10, 20, 30);
        Assert.Equal(RemoteTelemetryStatus.Unauthorized,
            receiver.Receive(stale.Node, stale.Timestamp, stale.Nonce, stale.Signature, IPAddress.Loopback, stale.Body, Now).Status);

        var estimated = SignedRequest("taoyuan", Now, 10, 20, 30, "estimated", "abcdefghijklmnopqrstuv1");
        Assert.Equal(RemoteTelemetryStatus.Invalid,
            receiver.Receive(estimated.Node, estimated.Timestamp, estimated.Nonce, estimated.Signature, IPAddress.Loopback, estimated.Body, Now).Status);
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
            receiver.Receive(request.Node, request.Timestamp, request.Nonce, request.Signature, IPAddress.Loopback, request.Body, Now).Status);
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
                receiver.Receive("taichung", timestamp, nonce, Sign("taichung", timestamp, nonce, body),
                    IPAddress.Loopback, body, Now).Status);
        }
    }

    private static RemoteOperationsTelemetry Receiver(FakeTelemetryStore store, bool requireAddress)
    {
        var values = new Dictionary<string, string?>
        {
            ["Operations:RemoteTelemetry:RequireSourceAddress"] = requireAddress.ToString(),
            ["Operations:RemoteTelemetry:Nodes:taichung:Address"] = "192.168.50.98",
            ["Operations:RemoteTelemetry:Nodes:taichung:Secret"] = Convert.ToBase64String(Secret),
            ["Operations:RemoteTelemetry:Nodes:taoyuan:Address"] = "100.89.42.36",
            ["Operations:RemoteTelemetry:Nodes:taoyuan:Secret"] = Convert.ToBase64String(Secret)
        };
        return new RemoteOperationsTelemetry(new ConfigurationBuilder().AddInMemoryCollection(values).Build(), store);
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
        return new(node, timestamp, nonce, Sign(node, timestamp, nonce, body), body);
    }

    private static string Sign(string node, string timestamp, string nonce, byte[] body)
    {
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/operations/telemetry\n{node}\n{timestamp}\n{nonce}\n");
        return "sha256=" + Convert.ToHexString(HMACSHA256.HashData(Secret, prefix.Concat(body).ToArray())).ToLowerInvariant();
    }

    private sealed record Signed(string Node, string Timestamp, string Nonce, string Signature, byte[] Body);
    private sealed class FakeTelemetryStore : IRemoteTelemetryStore
    {
        public OperationsNodeState? Node { get; private set; }
        public bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node) { node = default!; return false; }
        public bool TryWrite(OperationsNodeState node) { Node = node; return true; }
    }
}
