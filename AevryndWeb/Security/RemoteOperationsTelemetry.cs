using System.Globalization;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace AevryndWeb.Security;

public enum RemoteTelemetryStatus { Accepted, Invalid, Unauthorized, Replay, Unavailable }

public readonly record struct RemoteTelemetryResult(RemoteTelemetryStatus Status)
{
    public static readonly RemoteTelemetryResult Accepted = new(RemoteTelemetryStatus.Accepted);
}

public interface IRemoteOperationsTelemetry
{
    RemoteTelemetryResult Receive(string nodeHeader, string timestampHeader, string nonceHeader,
        string keyIdHeader, string signatureHeader, IPAddress? remoteAddress, ReadOnlySpan<byte> body, DateTimeOffset now);
}

public interface IRemoteTelemetryStore
{
    bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node);
    bool TryWrite(OperationsNodeState node);
    bool TryReadHistory(string nodeId, DateTimeOffset now, out IReadOnlyList<OperationsWorkState> history)
    {
        history = [];
        return false;
    }
    bool TryReadFreshSnapshot(string nodeId, DateTimeOffset now, out RemoteTelemetrySnapshot snapshot)
    {
        if (TryReadFresh(nodeId, now, out var node)) { snapshot = new(node, [], []); return true; }
        snapshot = default!; return false;
    }
    bool TryWriteSnapshot(RemoteTelemetrySnapshot snapshot) => TryWrite(snapshot.Node);
}

public sealed record RemoteTelemetrySnapshot(OperationsNodeState Node, IReadOnlyList<OperationsWorkState> ActiveWork, IReadOnlyList<OperationsWorkState> History);

/// <summary>
/// Authenticates exact request bytes. The signing input is:
/// POST\n/api/operations/telemetry\n{node}\n{unix-seconds}\n{nonce}\n{raw-json-body}.
/// 每個節點只允許一種外部設定的驗證模式；ECDSA 不會失敗後降級至 HMAC。
/// </summary>
public sealed class RemoteOperationsTelemetry(IConfiguration configuration, IRemoteTelemetryStore store, IOperationsTelemetryReplayStore replayStore) : IRemoteOperationsTelemetry
{
    private const string EndpointPath = "/api/operations/telemetry";
    private static readonly HashSet<string> AllowedNodeIds = new(StringComparer.Ordinal) { "taichung", "taoyuan" };
    private static readonly Regex NonceShape = new("^[A-Za-z0-9_-]{22,64}$", RegexOptions.CultureInvariant);
    private static readonly Regex KeyIdShape = new("^[a-f0-9]{32}$", RegexOptions.CultureInvariant);

    public RemoteTelemetryResult Receive(string nodeHeader, string timestampHeader, string nonceHeader,
        string keyIdHeader, string signatureHeader, IPAddress? remoteAddress, ReadOnlySpan<byte> body, DateTimeOffset now)
    {
        if (!AllowedNodeIds.Contains(nodeHeader) || body is { Length: <= 0 or > 131072 } ||
            !NonceShape.IsMatch(nonceHeader) ||
            !long.TryParse(timestampHeader, NumberStyles.None, CultureInfo.InvariantCulture, out var timestampSeconds))
            return new(RemoteTelemetryStatus.Invalid);

        DateTimeOffset signedAt;
        try { signedAt = DateTimeOffset.FromUnixTimeSeconds(timestampSeconds); }
        catch (ArgumentOutOfRangeException) { return new(RemoteTelemetryStatus.Invalid); }
        if (!WithinFreshWindow(signedAt, now)) return new(RemoteTelemetryStatus.Unauthorized);

        var nodeSection = configuration.GetSection($"Operations:RemoteTelemetry:Nodes:{nodeHeader}");
        var requireSourceAddress = configuration.GetValue<bool>("Operations:RemoteTelemetry:RequireSourceAddress");
        if ((requireSourceAddress && (!IPAddress.TryParse(nodeSection["Address"], out var expectedAddress) ||
                remoteAddress is null || !AddressEquals(expectedAddress, remoteAddress))) ||
            !TryAuthenticate(nodeSection, nodeHeader, timestampHeader, nonceHeader, keyIdHeader, signatureHeader, body))
            return new(RemoteTelemetryStatus.Unauthorized);

        RemoteTelemetryHeartbeat? heartbeat;
        try
        {
            heartbeat = JsonSerializer.Deserialize<RemoteTelemetryHeartbeat>(body, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = false,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
            });
        }
        catch (JsonException) { return new(RemoteTelemetryStatus.Invalid); }

        if (heartbeat is null || heartbeat.Version != 1 || heartbeat.NodeId != nodeHeader ||
            heartbeat.Measurement != "measured" || !Metric(heartbeat.CpuPercent) || !Metric(heartbeat.RamPercent) ||
            !OptionalMetric(heartbeat.GpuPercent) || heartbeat.SampledUtc == default ||
            !WithinFreshWindow(heartbeat.SampledUtc, now) ||
            Math.Abs((heartbeat.SampledUtc - signedAt).TotalSeconds) > 15)
            return new(RemoteTelemetryStatus.Invalid);

        var activeWork = heartbeat.ActiveWork ?? [];
        var history = heartbeat.History ?? [];
        if (activeWork.Count > 10 || history.Count > 100 ||
            !OperationsSnapshotSchema.TryValidateRemoteWork(activeWork, history, nodeHeader, now))
            return new(RemoteTelemetryStatus.Invalid);

        var replayStatus = replayStore.TryConsume(nodeHeader, nonceHeader, now);
        if (replayStatus == ReplayConsumeStatus.Replay) return new(RemoteTelemetryStatus.Replay);
        if (replayStatus == ReplayConsumeStatus.Unavailable) return new(RemoteTelemetryStatus.Unavailable);

        var node = new OperationsNodeState
        {
            Id = nodeHeader,
            CpuPercent = heartbeat.CpuPercent,
            RamPercent = heartbeat.RamPercent,
            GpuPercent = heartbeat.GpuPercent,
            SampledAt = heartbeat.SampledUtc
        };
        return store.TryWriteSnapshot(new(node, activeWork, history)) ? RemoteTelemetryResult.Accepted : new(RemoteTelemetryStatus.Unavailable);
    }

    private static bool WithinFreshWindow(DateTimeOffset value, DateTimeOffset now) =>
        value <= now.AddSeconds(30) && now - value <= TimeSpan.FromMinutes(2);

    private static bool Metric(double value) => double.IsFinite(value) && value is >= 0 and <= 100;
    private static bool OptionalMetric(double? value) => value is null || Metric(value.Value);

    private static bool AddressEquals(IPAddress expected, IPAddress actual)
    {
        if (expected.IsIPv4MappedToIPv6) expected = expected.MapToIPv4();
        if (actual.IsIPv4MappedToIPv6) actual = actual.MapToIPv4();
        return expected.Equals(actual);
    }

    private static bool TryAuthenticate(IConfigurationSection nodeSection, string nodeId, string timestamp, string nonce,
        string keyId, string signatureHeader, ReadOnlySpan<byte> body)
    {
        var prefix = Encoding.UTF8.GetBytes($"POST\n{EndpointPath}\n{nodeId}\n{timestamp}\n{nonce}\n");
        var signedBytes = new byte[prefix.Length + body.Length];
        prefix.CopyTo(signedBytes, 0); body.CopyTo(signedBytes.AsSpan(prefix.Length));
        var mode = nodeSection["AuthenticationMode"] ?? "EcdsaP256";

        if (StringComparer.Ordinal.Equals(mode, "EcdsaP256"))
            return TryVerifyEcdsa(nodeSection, keyId, signatureHeader, signedBytes);
        if (!StringComparer.Ordinal.Equals(mode, "HmacSha256") || keyId.Length != 0 ||
            !TryReadHmacSignature(signatureHeader, out var suppliedSignature) ||
            !TryReadSecret(nodeSection["Secret"], out var secret)) return false;
        try
        {
            var expectedSignature = HMACSHA256.HashData(secret, signedBytes);
            return CryptographicOperations.FixedTimeEquals(expectedSignature, suppliedSignature);
        }
        finally { CryptographicOperations.ZeroMemory(secret); }
    }

    private static bool TryVerifyEcdsa(IConfigurationSection nodeSection, string keyId, string signatureHeader, byte[] signedBytes)
    {
        var revokedText = nodeSection[$"Keys:{keyId}:Revoked"];
        if (!KeyIdShape.IsMatch(keyId) ||
            (revokedText is not null && (!bool.TryParse(revokedText, out var revoked) || revoked)) ||
            !TryReadEcdsaSignature(signatureHeader, out var signature) ||
            !TryReadPublicKey(nodeSection[$"Keys:{keyId}:PublicKey"], out var publicKey)) return false;
        try
        {
            using var verifier = ECDsa.Create();
            verifier.ImportSubjectPublicKeyInfo(publicKey, out var bytesRead);
            var configuredKeyId = Convert.ToHexString(SHA256.HashData(publicKey)[..16]).ToLowerInvariant();
            var curveOid = verifier.ExportParameters(false).Curve.Oid.Value;
            return StringComparer.Ordinal.Equals(configuredKeyId, keyId) && bytesRead == publicKey.Length && verifier.KeySize == 256 &&
                StringComparer.Ordinal.Equals(curveOid, "1.2.840.10045.3.1.7") &&
                verifier.VerifyData(signedBytes, signature, HashAlgorithmName.SHA256, DSASignatureFormat.IeeeP1363FixedFieldConcatenation);
        }
        catch (CryptographicException) { return false; }
        finally { CryptographicOperations.ZeroMemory(publicKey); }
    }

    private static bool TryReadPublicKey(string? encoded, out byte[] publicKey)
    {
        publicKey = [];
        if (string.IsNullOrWhiteSpace(encoded) || encoded.Length > 256) return false;
        try
        {
            publicKey = Convert.FromBase64String(encoded);
            if (publicKey.Length is >= 80 and <= 120) return true;
            CryptographicOperations.ZeroMemory(publicKey); publicKey = []; return false;
        }
        catch (FormatException) { return false; }
    }

    private static bool TryReadSecret(string? encoded, out byte[] secret)
    {
        secret = [];
        if (string.IsNullOrWhiteSpace(encoded)) return false;
        try
        {
            secret = Convert.FromBase64String(encoded);
            if (secret.Length is >= 32 and <= 64) return true;
            CryptographicOperations.ZeroMemory(secret); secret = []; return false;
        }
        catch (FormatException) { return false; }
    }

    private static bool TryReadHmacSignature(string value, out byte[] signature)
    {
        signature = [];
        const string prefix = "sha256=";
        if (!value.StartsWith(prefix, StringComparison.Ordinal) || value.Length != prefix.Length + 64) return false;
        try { signature = Convert.FromHexString(value[prefix.Length..]); return true; }
        catch (FormatException) { return false; }
    }

    private static bool TryReadEcdsaSignature(string value, out byte[] signature)
    {
        signature = [];
        const string prefix = "ecdsa-p256-sha256=";
        if (!value.StartsWith(prefix, StringComparison.Ordinal) || value.Length != prefix.Length + 86) return false;
        var encoded = value[prefix.Length..].Replace('-', '+').Replace('_', '/') + "==";
        try { signature = Convert.FromBase64String(encoded); return signature.Length == 64; }
        catch (FormatException) { return false; }
    }
}

public sealed class RemoteTelemetryHeartbeat
{
    [JsonRequired, JsonPropertyName("version")] public int Version { get; set; }
    [JsonRequired, JsonPropertyName("nodeId")] public string NodeId { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("measurement")] public string Measurement { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("cpuPercent")] public double CpuPercent { get; set; }
    [JsonRequired, JsonPropertyName("ramPercent")] public double RamPercent { get; set; }
    [JsonRequired, JsonPropertyName("gpuPercent")] public double? GpuPercent { get; set; }
    [JsonRequired, JsonPropertyName("sampledUtc")] public DateTimeOffset SampledUtc { get; set; }
    [JsonPropertyName("activeWork")] public List<OperationsWorkState>? ActiveWork { get; set; }
    [JsonPropertyName("history")] public List<OperationsWorkState>? History { get; set; }
}

public sealed class FileRemoteTelemetryStore(IConfiguration configuration) : IRemoteTelemetryStore
{
    private static readonly HashSet<string> AllowedNodeIds = new(StringComparer.Ordinal) { "taichung", "taoyuan" };
    private readonly object _writeLock = new();
    private string DirectoryPath => configuration["Operations:RemoteTelemetry:StateDirectory"] ?? @"C:\ProgramData\AevryndWeb\remote-telemetry";

    public bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node)
    {
        node = default!;
        if (!TryRead(nodeId, out var candidate) || candidate.SampledAt > now.AddSeconds(30) || now - candidate.SampledAt > TimeSpan.FromMinutes(2)) return false;
        node = candidate;
        return true;
    }

    public bool TryWrite(OperationsNodeState node)
    {
        if (!ValidNode(node) || !OperatingSystem.IsWindows() || !Directory.Exists(DirectoryPath) ||
            !OperationsFileSecurity.HasSafeAcl(DirectoryPath)) return false;
        lock (_writeLock)
        {
            if (TryRead(node.Id, out var previous) && node.SampledAt <= previous.SampledAt) return false;
            try
            {
                var path = PathFor(node.Id); var temporary = path + ".tmp";
                File.WriteAllBytes(temporary, JsonSerializer.SerializeToUtf8Bytes(node));
                File.Move(temporary, path, true);
                return OperationsFileSecurity.HasSafeAcl(path);
            }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException) { return false; }
        }
    }

    public bool TryReadFreshSnapshot(string nodeId, DateTimeOffset now, out RemoteTelemetrySnapshot snapshot)
    {
        snapshot = default!;
        if (!TryReadEnvelope(nodeId, out var envelope) || envelope.Node.SampledAt > now.AddSeconds(30) || now - envelope.Node.SampledAt > TimeSpan.FromMinutes(2)) return false;
        snapshot = new(envelope.Node, envelope.ActiveWork, envelope.History); return true;
    }

    public bool TryReadHistory(string nodeId, DateTimeOffset now, out IReadOnlyList<OperationsWorkState> history)
    {
        history = [];
        // 歷程讀取不要求最新 heartbeat，但仍要求既有 ACL、strict envelope 與終態 schema 驗證。
        if (!TryReadEnvelope(nodeId, out var envelope) || envelope.History.Any(item => item.Status is "working" or "blocked") ||
            !OperationsSnapshotSchema.TryValidateRemoteWork([], envelope.History, nodeId, now)) return false;
        history = envelope.History;
        return true;
    }

    public bool TryWriteSnapshot(RemoteTelemetrySnapshot snapshot)
    {
        if (!ValidNode(snapshot.Node) || !OperationsSnapshotSchema.TryValidateRemoteWork(snapshot.ActiveWork, snapshot.History, snapshot.Node.Id, DateTimeOffset.UtcNow) ||
            !OperatingSystem.IsWindows() || !Directory.Exists(DirectoryPath) || !OperationsFileSecurity.HasSafeAcl(DirectoryPath)) return false;
        lock (_writeLock)
        {
            var hasPreviousEnvelope = TryReadEnvelope(snapshot.Node.Id, out var previousEnvelope);
            if ((hasPreviousEnvelope && snapshot.Node.SampledAt <= previousEnvelope.Node.SampledAt) ||
                (TryRead(snapshot.Node.Id, out var previousNode) && snapshot.Node.SampledAt <= previousNode.SampledAt)) return false;
            var history = (hasPreviousEnvelope ? previousEnvelope.History : []).Concat(snapshot.History)
                .GroupBy(item => (item.Name, item.StartedAt)).Select(group => group.OrderByDescending(item => item.UpdatedAt).First())
                .OrderBy(item => item.StartedAt).TakeLast(100).ToList();
            // 合併舊歷程後再驗證，避免已結束 identity 被下一個 heartbeat 復活為 active。
            if (!OperationsSnapshotSchema.TryValidateRemoteWork(snapshot.ActiveWork, history, snapshot.Node.Id, DateTimeOffset.UtcNow)) return false;
            try
            {
                var path = PathFor(snapshot.Node.Id); var temporary = path + ".tmp";
                var envelope = new RemoteTelemetryEnvelope { Version = 2, Node = snapshot.Node, ActiveWork = snapshot.ActiveWork.ToList(), History = history };
                File.WriteAllBytes(temporary, JsonSerializer.SerializeToUtf8Bytes(envelope)); File.Move(temporary, path, true);
                return OperationsFileSecurity.HasSafeAcl(path);
            }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException) { return false; }
        }
    }

    private bool TryRead(string nodeId, out OperationsNodeState node)
    {
        node = default!;
        if (!AllowedNodeIds.Contains(nodeId) || !OperatingSystem.IsWindows() || !Directory.Exists(DirectoryPath) ||
            !OperationsFileSecurity.HasSafeAcl(DirectoryPath)) return false;
        var path = PathFor(nodeId);
        try
        {
            if (!File.Exists(path) || !OperationsFileSecurity.HasSafeAcl(path)) return false;
            var raw = File.ReadAllBytes(path); if (raw.Length is <= 0 or > 2048) return false;
            var candidate = JsonSerializer.Deserialize<OperationsNodeState>(raw, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = false,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
            });
            if (candidate is null || candidate.Id != nodeId || !ValidNode(candidate)) return false;
            node = candidate; return true;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException) { return false; }
    }

    private bool TryReadEnvelope(string nodeId, out RemoteTelemetryEnvelope envelope)
    {
        envelope = default!;
        if (!AllowedNodeIds.Contains(nodeId) || !OperatingSystem.IsWindows() || !Directory.Exists(DirectoryPath) || !OperationsFileSecurity.HasSafeAcl(DirectoryPath)) return false;
        var path = PathFor(nodeId);
        try
        {
            if (!File.Exists(path) || !OperationsFileSecurity.HasSafeAcl(path)) return false;
            var raw = File.ReadAllBytes(path); if (raw.Length is <= 0 or > 131_072) return false;
            var candidate = JsonSerializer.Deserialize<RemoteTelemetryEnvelope>(raw, new JsonSerializerOptions { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow });
            if (candidate is null || candidate.Version != 2 || candidate.Node.Id != nodeId || !ValidNode(candidate.Node) || candidate.ActiveWork.Count > 10 || candidate.History.Count > 100) return false;
            envelope = candidate; return true;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException) { return false; }
    }

    private string PathFor(string nodeId) => Path.Combine(DirectoryPath, nodeId + ".json");
    private static bool ValidNode(OperationsNodeState node) => AllowedNodeIds.Contains(node.Id) && node.SampledAt != default &&
        node.CpuPercent is >= 0 and <= 100 && double.IsFinite(node.CpuPercent.Value) &&
        node.RamPercent is >= 0 and <= 100 && double.IsFinite(node.RamPercent.Value) &&
        (node.GpuPercent is null || node.GpuPercent is >= 0 and <= 100 && double.IsFinite(node.GpuPercent.Value));
}

public sealed class RemoteTelemetryEnvelope
{
    public int Version { get; set; }
    public OperationsNodeState Node { get; set; } = new();
    public List<OperationsWorkState> ActiveWork { get; set; } = [];
    public List<OperationsWorkState> History { get; set; } = [];
}
