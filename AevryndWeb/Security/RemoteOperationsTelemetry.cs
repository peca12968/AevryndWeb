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
        string signatureHeader, IPAddress? remoteAddress, ReadOnlySpan<byte> body, DateTimeOffset now);
}

public interface IRemoteTelemetryStore
{
    bool TryReadFresh(string nodeId, DateTimeOffset now, out OperationsNodeState node);
    bool TryWrite(OperationsNodeState node);
}

/// <summary>
/// Authenticates exact request bytes. The signing input is:
/// POST\n/api/operations/telemetry\n{node}\n{unix-seconds}\n{nonce}\n{raw-json-body}.
/// Secrets must be 32-64 random bytes encoded as Base64 and supplied outside appsettings.json.
/// </summary>
public sealed class RemoteOperationsTelemetry(IConfiguration configuration, IRemoteTelemetryStore store) : IRemoteOperationsTelemetry
{
    private const string EndpointPath = "/api/operations/telemetry";
    private static readonly HashSet<string> AllowedNodeIds = new(StringComparer.Ordinal) { "taichung", "taoyuan" };
    private static readonly Regex NonceShape = new("^[A-Za-z0-9_-]{22,64}$", RegexOptions.CultureInvariant);
    private readonly object _nonceLock = new();
    private readonly Dictionary<string, DateTimeOffset> _seenNonces = new(StringComparer.Ordinal);

    public RemoteTelemetryResult Receive(string nodeHeader, string timestampHeader, string nonceHeader,
        string signatureHeader, IPAddress? remoteAddress, ReadOnlySpan<byte> body, DateTimeOffset now)
    {
        if (!AllowedNodeIds.Contains(nodeHeader) || body is { Length: <= 0 or > 4096 } ||
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
            !TryReadSignature(signatureHeader, out var suppliedSignature) ||
            !TryReadSecret(nodeSection["Secret"], out var secret))
            return new(RemoteTelemetryStatus.Unauthorized);

        try
        {
            var prefix = Encoding.UTF8.GetBytes($"POST\n{EndpointPath}\n{nodeHeader}\n{timestampHeader}\n{nonceHeader}\n");
            var signedBytes = new byte[prefix.Length + body.Length];
            prefix.CopyTo(signedBytes, 0); body.CopyTo(signedBytes.AsSpan(prefix.Length));
            var expectedSignature = HMACSHA256.HashData(secret, signedBytes);
            if (!CryptographicOperations.FixedTimeEquals(expectedSignature, suppliedSignature))
                return new(RemoteTelemetryStatus.Unauthorized);
        }
        finally { CryptographicOperations.ZeroMemory(secret); }

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
            !Metric(heartbeat.GpuPercent) || heartbeat.SampledUtc == default ||
            !WithinFreshWindow(heartbeat.SampledUtc, now) ||
            Math.Abs((heartbeat.SampledUtc - signedAt).TotalSeconds) > 15)
            return new(RemoteTelemetryStatus.Invalid);

        var nonceKey = nodeHeader + ":" + nonceHeader;
        lock (_nonceLock)
        {
            foreach (var expired in _seenNonces.Where(item => now - item.Value > TimeSpan.FromMinutes(2)).Select(item => item.Key).ToArray())
                _seenNonces.Remove(expired);
            if (_seenNonces.ContainsKey(nonceKey)) return new(RemoteTelemetryStatus.Replay);
            _seenNonces[nonceKey] = now;
        }

        var node = new OperationsNodeState
        {
            Id = nodeHeader,
            CpuPercent = heartbeat.CpuPercent,
            RamPercent = heartbeat.RamPercent,
            GpuPercent = heartbeat.GpuPercent,
            SampledAt = heartbeat.SampledUtc
        };
        return store.TryWrite(node) ? RemoteTelemetryResult.Accepted : new(RemoteTelemetryStatus.Unavailable);
    }

    private static bool WithinFreshWindow(DateTimeOffset value, DateTimeOffset now) =>
        value <= now.AddSeconds(30) && now - value <= TimeSpan.FromMinutes(2);

    private static bool Metric(double value) => double.IsFinite(value) && value is >= 0 and <= 100;

    private static bool AddressEquals(IPAddress expected, IPAddress actual)
    {
        if (expected.IsIPv4MappedToIPv6) expected = expected.MapToIPv4();
        if (actual.IsIPv4MappedToIPv6) actual = actual.MapToIPv4();
        return expected.Equals(actual);
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

    private static bool TryReadSignature(string value, out byte[] signature)
    {
        signature = [];
        const string prefix = "sha256=";
        if (!value.StartsWith(prefix, StringComparison.Ordinal) || value.Length != prefix.Length + 64) return false;
        try { signature = Convert.FromHexString(value[prefix.Length..]); return true; }
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
    [JsonRequired, JsonPropertyName("gpuPercent")] public double GpuPercent { get; set; }
    [JsonRequired, JsonPropertyName("sampledUtc")] public DateTimeOffset SampledUtc { get; set; }
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

    private string PathFor(string nodeId) => Path.Combine(DirectoryPath, nodeId + ".json");
    private static bool ValidNode(OperationsNodeState node) => AllowedNodeIds.Contains(node.Id) && node.SampledAt != default &&
        node.CpuPercent is >= 0 and <= 100 && double.IsFinite(node.CpuPercent.Value) &&
        node.RamPercent is >= 0 and <= 100 && double.IsFinite(node.RamPercent.Value) &&
        node.GpuPercent is >= 0 and <= 100 && double.IsFinite(node.GpuPercent.Value);
}
