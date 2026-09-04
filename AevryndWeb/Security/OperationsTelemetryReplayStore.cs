using System.Text.Json;
using System.Text.Json.Serialization;
using System.Runtime.Versioning;

namespace AevryndWeb.Security;

public enum ReplayConsumeStatus { Accepted, Replay, Unavailable }

public interface IOperationsTelemetryReplayStore
{
    ReplayConsumeStatus TryConsume(string nodeId, string nonce, DateTimeOffset now);
}

public sealed class MemoryOperationsTelemetryReplayStore : IOperationsTelemetryReplayStore
{
    private readonly object _gate = new();
    private readonly Dictionary<string, DateTimeOffset> _entries = new(StringComparer.Ordinal);
    public ReplayConsumeStatus TryConsume(string nodeId, string nonce, DateTimeOffset now)
    {
        lock (_gate)
        {
            foreach (var expired in _entries.Where(item => now - item.Value > TimeSpan.FromMinutes(2)).Select(item => item.Key).ToArray()) _entries.Remove(expired);
            return _entries.TryAdd(nodeId + ":" + nonce, now) ? ReplayConsumeStatus.Accepted : ReplayConsumeStatus.Replay;
        }
    }
}

/// <summary>以獨占鎖與原子替換保存 nonce；程序重啟後仍拒絕 freshness window 內的重播。</summary>
public sealed class FileOperationsTelemetryReplayStore(IConfiguration configuration) : IOperationsTelemetryReplayStore
{
    private readonly object _gate = new();
    private string DirectoryPath => configuration["Operations:RemoteTelemetry:StateDirectory"] ?? @"C:\ProgramData\AevryndWeb\remote-telemetry";

    public ReplayConsumeStatus TryConsume(string nodeId, string nonce, DateTimeOffset now)
    {
        if (!OperatingSystem.IsWindows() || !Directory.Exists(DirectoryPath) || !OperationsFileSecurity.HasSafeAcl(DirectoryPath)) return ReplayConsumeStatus.Unavailable;
        lock (_gate)
        {
            var lockPath = Path.Combine(DirectoryPath, "nonce-ledger.lock");
            var ledgerPath = Path.Combine(DirectoryPath, "nonce-ledger.json");
            try
            {
                using var processLock = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
                if (!OperationsFileSecurity.HasSafeAcl(lockPath)) return ReplayConsumeStatus.Unavailable;
                var document = Read(ledgerPath);
                if (document is null) return ReplayConsumeStatus.Unavailable;
                document.Entries.RemoveAll(entry => now - entry.SeenAt > TimeSpan.FromMinutes(2));
                if (document.Entries.Any(entry => entry.NodeId == nodeId && entry.Nonce == nonce)) return ReplayConsumeStatus.Replay;
                document.Entries.Add(new ReplayEntry { NodeId = nodeId, Nonce = nonce, SeenAt = now });
                if (document.Entries.Count > 4096) return ReplayConsumeStatus.Unavailable;
                var temporary = ledgerPath + ".tmp";
                File.WriteAllBytes(temporary, JsonSerializer.SerializeToUtf8Bytes(document)); File.Move(temporary, ledgerPath, true);
                return OperationsFileSecurity.HasSafeAcl(ledgerPath) ? ReplayConsumeStatus.Accepted : ReplayConsumeStatus.Unavailable;
            }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException) { return ReplayConsumeStatus.Unavailable; }
        }
    }

    [SupportedOSPlatform("windows")]
    private static ReplayLedgerDocument? Read(string path)
    {
        if (!File.Exists(path)) return new ReplayLedgerDocument();
        if (!OperationsFileSecurity.HasSafeAcl(path)) return null;
        var raw = File.ReadAllBytes(path); if (raw.Length is <= 0 or > 524_288) return null;
        var document = JsonSerializer.Deserialize<ReplayLedgerDocument>(raw, new JsonSerializerOptions { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow });
        return document is { Version: 1, Entries.Count: <= 4096 } && document.Entries.All(entry => entry.NodeId is "taichung" or "taoyuan" && entry.Nonce.Length is >= 22 and <= 64 && entry.SeenAt != default) ? document : null;
    }

    private sealed class ReplayLedgerDocument { public int Version { get; set; } = 1; public List<ReplayEntry> Entries { get; set; } = []; }
    private sealed class ReplayEntry { public string NodeId { get; set; } = string.Empty; public string Nonce { get; set; } = string.Empty; public DateTimeOffset SeenAt { get; set; } }
}
