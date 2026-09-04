using System.Text.Json;
using System.Text.Json.Serialization;

namespace AevryndWeb.Security;

public sealed class MemoryCodexEventRelayReplayStore : ICodexEventRelayReplayStore
{
    private readonly object _gate = new();
    private readonly Dictionary<string, DateTimeOffset> _entries = new(StringComparer.Ordinal);

    public CodexRelayResult TryConsume(string scope, string nonce, DateTimeOffset now)
    {
        lock (_gate)
        {
            foreach (var key in _entries.Where(item => now - item.Value > TimeSpan.FromMinutes(3)).Select(item => item.Key).ToArray()) _entries.Remove(key);
            var identity = scope + "\n" + nonce;
            if (_entries.ContainsKey(identity)) return CodexRelayResult.Replay;
            if (_entries.Count >= 2048) return CodexRelayResult.Unavailable;
            _entries.Add(identity, now); return CodexRelayResult.Accepted;
        }
    }
}

public sealed class FileCodexEventRelayReplayStore(IConfiguration configuration) : ICodexEventRelayReplayStore
{
    private const int MaximumFileBytes = 262_144;
    private readonly object _gate = new();
    private string DirectoryPath => configuration["Operations:CodexRelay:StateDirectory"] ??
        configuration["Operations:RemoteTelemetry:StateDirectory"] ?? @"C:\ProgramData\AevryndWeb\remote-telemetry";
    private string StatePath => Path.Combine(DirectoryPath, "codex-relay-replay.json");

    public CodexRelayResult TryConsume(string scope, string nonce, DateTimeOffset now)
    {
        if (scope is not ("publisher" or "node-taichung" or "node-taoyuan")) return CodexRelayResult.Invalid;
        lock (_gate)
        {
            if (!Ready() || !Read(out var state)) return CodexRelayResult.Unavailable;
            state.Entries.RemoveAll(item => now - item.ConsumedAt > TimeSpan.FromMinutes(3));
            if (state.Entries.Any(item => StringComparer.Ordinal.Equals(item.Scope, scope) && StringComparer.Ordinal.Equals(item.Nonce, nonce))) return CodexRelayResult.Replay;
            if (state.Entries.Count >= 2048) return CodexRelayResult.Unavailable;
            state.Entries.Add(new ReplayEntry { Scope = scope, Nonce = nonce, ConsumedAt = now });
            return Write(state) ? CodexRelayResult.Accepted : CodexRelayResult.Unavailable;
        }
    }

    private bool Read(out ReplayState state)
    {
        state = new();
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            if (!File.Exists(StatePath)) return true;
            if (!OperationsFileSecurity.HasSafeAcl(StatePath)) return false;
            var raw = File.ReadAllBytes(StatePath); if (raw.Length is <= 0 or > MaximumFileBytes) return false;
            var candidate = JsonSerializer.Deserialize<ReplayState>(raw, StrictJson);
            if (candidate is null || candidate.Version != 1 || candidate.Entries.Count > 2048 || candidate.Entries.Any(item =>
                    item.Scope is not ("publisher" or "node-taichung" or "node-taoyuan") || item.Nonce.Length is < 22 or > 64 || item.ConsumedAt == default) ||
                candidate.Entries.Select(item => item.Scope + "\n" + item.Nonce).Distinct(StringComparer.Ordinal).Count() != candidate.Entries.Count) return false;
            state = candidate; return true;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException) { return false; }
    }

    private bool Write(ReplayState state)
    {
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            var bytes = JsonSerializer.SerializeToUtf8Bytes(state); if (bytes.Length > MaximumFileBytes) return false;
            var temporary = StatePath + "." + Guid.NewGuid().ToString("N") + ".tmp";
            File.WriteAllBytes(temporary, bytes);
            if (!OperationsFileSecurity.HasSafeAcl(temporary)) { File.Delete(temporary); return false; }
            File.Move(temporary, StatePath, true); return OperationsFileSecurity.HasSafeAcl(StatePath);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException) { return false; }
    }

    private bool Ready() => OperatingSystem.IsWindows() && Directory.Exists(DirectoryPath) && OperationsFileSecurity.HasSafeAcl(DirectoryPath);
    private static readonly JsonSerializerOptions StrictJson = new() { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private sealed class ReplayState { [JsonRequired] public int Version { get; set; } = 1; [JsonRequired] public List<ReplayEntry> Entries { get; set; } = []; }
    private sealed class ReplayEntry { [JsonRequired] public string Scope { get; set; } = string.Empty; [JsonRequired] public string Nonce { get; set; } = string.Empty; [JsonRequired] public DateTimeOffset ConsumedAt { get; set; } }
}

public sealed class MemoryCodexEventRelayStore : ICodexEventRelayStore
{
    private readonly object _gate = new();
    private readonly List<CodexRelayCommandState> _commands = [];
    private readonly HashSet<string> _knownCommandIds = new(StringComparer.Ordinal);

    public CodexRelayResult TryCreate(CodexRelayCommandState command)
    {
        lock (_gate)
        {
            if (_knownCommandIds.Contains(command.CommandId)) return CodexRelayResult.Duplicate;
            if (_knownCommandIds.Count >= 4096) return CodexRelayResult.Unavailable;
            if (_commands.Count(item => item.Status is CodexRelayCommandStatus.Queued or CodexRelayCommandStatus.Running) >= 100) return CodexRelayResult.Unavailable;
            _knownCommandIds.Add(command.CommandId); _commands.Add(Clone(command)); Trim(); return CodexRelayResult.Accepted;
        }
    }

    public IReadOnlyList<CodexRelayCommandState> ReadPending(string nodeId)
    {
        lock (_gate) return _commands.Where(item => item.NodeId == nodeId && item.Status is CodexRelayCommandStatus.Queued or CodexRelayCommandStatus.Running).Select(Clone).ToArray();
    }

    public IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum)
    {
        lock (_gate) return _commands.OrderByDescending(item => item.UpdatedAt).Take(Math.Clamp(maximum, 1, 200)).Select(Clone).ToArray();
    }

    public CodexRelayResult TryAcknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now)
    {
        lock (_gate)
        {
            var command = _commands.SingleOrDefault(item => item.CommandId == ack.CommandId);
            if (command is null || command.NodeId != nodeId) return CodexRelayResult.Conflict;
            var next = Enum.Parse<CodexRelayCommandStatus>(ack.State, true);
            var valid = command.Status == CodexRelayCommandStatus.Queued && next is CodexRelayCommandStatus.Running or CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed ||
                command.Status == CodexRelayCommandStatus.Running && next is CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed;
            if (!valid) return CodexRelayResult.Conflict;
            if (ack.OccurredAtUtc < command.UpdatedAt) return CodexRelayResult.Conflict;
            command.Status = next; command.UpdatedAt = ack.OccurredAtUtc; command.ExitCode = ack.ExitCode; command.Summary = ack.Summary; Trim(); return CodexRelayResult.Accepted;
        }
    }

    private void Trim()
    {
        var terminal = _commands.Where(item => item.Status is CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed).OrderByDescending(item => item.UpdatedAt).Skip(200).ToArray();
        foreach (var command in terminal) _commands.Remove(command);
    }

    private static CodexRelayCommandState Clone(CodexRelayCommandState item) => new()
    {
        CommandId = item.CommandId, NodeId = item.NodeId, OwnedFiles = item.OwnedFiles.ToList(), Task = item.Task,
        Status = item.Status, CreatedAt = item.CreatedAt, UpdatedAt = item.UpdatedAt, ExitCode = item.ExitCode, Summary = item.Summary
    };
}

public sealed class FileCodexEventRelayStore(IConfiguration configuration) : ICodexEventRelayStore
{
    private const int MaximumFileBytes = 1_048_576;
    private readonly object _gate = new();
    private string DirectoryPath => configuration["Operations:CodexRelay:StateDirectory"] ??
        configuration["Operations:RemoteTelemetry:StateDirectory"] ?? @"C:\ProgramData\AevryndWeb\remote-telemetry";
    private string StatePath => Path.Combine(DirectoryPath, "commands.json");

    public CodexRelayResult TryCreate(CodexRelayCommandState command) => Mutate(ledger =>
    {
        if (ledger.KnownCommandIds.Contains(command.CommandId, StringComparer.Ordinal)) return CodexRelayResult.Duplicate;
        if (ledger.KnownCommandIds.Count >= 4096 || ledger.Commands.Count(item => item.Status is CodexRelayCommandStatus.Queued or CodexRelayCommandStatus.Running) >= 100) return CodexRelayResult.Unavailable;
        ledger.KnownCommandIds.Add(command.CommandId); ledger.Commands.Add(command); return CodexRelayResult.Accepted;
    });

    public IReadOnlyList<CodexRelayCommandState> ReadPending(string nodeId) => Read(out var commands)
        ? commands.Where(item => item.NodeId == nodeId && item.Status is CodexRelayCommandStatus.Queued or CodexRelayCommandStatus.Running).Select(Clone).ToArray() : [];

    public IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum) => Read(out var commands)
        ? commands.OrderByDescending(item => item.UpdatedAt).Take(Math.Clamp(maximum, 1, 200)).Select(Clone).ToArray() : [];

    public CodexRelayResult TryAcknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now) => Mutate(ledger =>
    {
        var command = ledger.Commands.SingleOrDefault(item => item.CommandId == ack.CommandId);
        if (command is null || command.NodeId != nodeId) return CodexRelayResult.Conflict;
        var next = Enum.Parse<CodexRelayCommandStatus>(ack.State, true);
        var valid = command.Status == CodexRelayCommandStatus.Queued && next is CodexRelayCommandStatus.Running or CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed ||
            command.Status == CodexRelayCommandStatus.Running && next is CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed;
        if (!valid) return CodexRelayResult.Conflict;
        if (ack.OccurredAtUtc < command.UpdatedAt) return CodexRelayResult.Conflict;
        command.Status = next; command.UpdatedAt = ack.OccurredAtUtc; command.ExitCode = ack.ExitCode; command.Summary = ack.Summary; return CodexRelayResult.Accepted;
    });

    private CodexRelayResult Mutate(Func<Ledger, CodexRelayResult> mutation)
    {
        lock (_gate)
        {
            if (!Ready() || !ReadCore(out var ledger)) return CodexRelayResult.Unavailable;
            var result = mutation(ledger); if (result != CodexRelayResult.Accepted) return result;
            var terminal = ledger.Commands.Where(item => item.Status is CodexRelayCommandStatus.Completed or CodexRelayCommandStatus.Failed).OrderByDescending(item => item.UpdatedAt).Skip(200).ToArray();
            foreach (var item in terminal) ledger.Commands.Remove(item);
            return WriteCore(ledger) ? CodexRelayResult.Accepted : CodexRelayResult.Unavailable;
        }
    }

    private bool Read(out List<CodexRelayCommandState> commands)
    {
        lock (_gate)
        {
            commands = [];
            if (!Ready() || !ReadCore(out var ledger)) return false;
            commands = ledger.Commands; return true;
        }
    }

    private bool ReadCore(out Ledger ledger)
    {
        ledger = new();
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            if (!File.Exists(StatePath)) return true;
            if (!OperationsFileSecurity.HasSafeAcl(StatePath)) return false;
            var raw = File.ReadAllBytes(StatePath); if (raw.Length is <= 0 or > MaximumFileBytes) return false;
            var candidate = JsonSerializer.Deserialize<Ledger>(raw, StrictJson);
            if (candidate is null || candidate.Version != 1 || candidate.Commands.Count > 300 || candidate.KnownCommandIds.Count > 4096 ||
                candidate.Commands.Any(item => !ValidStored(item)) || candidate.Commands.Select(item => item.CommandId).Distinct(StringComparer.Ordinal).Count() != candidate.Commands.Count ||
                candidate.KnownCommandIds.Any(id => id.Length is < 1 or > 128) || candidate.KnownCommandIds.Distinct(StringComparer.Ordinal).Count() != candidate.KnownCommandIds.Count ||
                candidate.Commands.Any(item => !candidate.KnownCommandIds.Contains(item.CommandId, StringComparer.Ordinal))) return false;
            ledger = candidate; return true;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException) { return false; }
    }

    private bool WriteCore(Ledger ledger)
    {
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            var bytes = JsonSerializer.SerializeToUtf8Bytes(ledger);
            if (bytes.Length > MaximumFileBytes) return false;
            var temporary = StatePath + "." + Guid.NewGuid().ToString("N") + ".tmp";
            File.WriteAllBytes(temporary, bytes);
            if (!OperationsFileSecurity.HasSafeAcl(temporary)) { File.Delete(temporary); return false; }
            File.Move(temporary, StatePath, true);
            return OperationsFileSecurity.HasSafeAcl(StatePath);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException) { return false; }
    }

    private bool Ready() => OperatingSystem.IsWindows() && Directory.Exists(DirectoryPath) && OperationsFileSecurity.HasSafeAcl(DirectoryPath);
    private static bool ValidStored(CodexRelayCommandState item) => item.CommandId.Length is > 0 and <= 128 && item.NodeId is "taichung" or "taoyuan" &&
        item.OwnedFiles.Count is >= 1 and <= 32 && item.OwnedFiles.All(path => path.Length is > 0 and <= 260 && !Path.IsPathRooted(path) && !path.Split('/', '\\').Any(part => part is "" or "." or "..")) &&
        item.Task.Length is > 0 and <= 8192 && item.CreatedAt != default && item.UpdatedAt >= item.CreatedAt && Enum.IsDefined(item.Status) && item.Summary is not { Length: > 4096 };
    private static CodexRelayCommandState Clone(CodexRelayCommandState item) => new() { CommandId = item.CommandId, NodeId = item.NodeId, OwnedFiles = item.OwnedFiles.ToList(), Task = item.Task, Status = item.Status, CreatedAt = item.CreatedAt, UpdatedAt = item.UpdatedAt, ExitCode = item.ExitCode, Summary = item.Summary };
    private static readonly JsonSerializerOptions StrictJson = new() { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private sealed class Ledger
    {
        [JsonRequired] public int Version { get; set; } = 1;
        [JsonRequired] public List<CodexRelayCommandState> Commands { get; set; } = [];
        [JsonRequired] public List<string> KnownCommandIds { get; set; } = [];
    }
}
