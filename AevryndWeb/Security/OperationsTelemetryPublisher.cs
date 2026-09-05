using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace AevryndWeb.Security;

/// <summary>以低頻率發布本機可驗證的基本遙測；遠端節點與 GPU 不猜測。</summary>
[SupportedOSPlatform("windows")]
public sealed class OperationsTelemetryPublisher(
    IConfiguration configuration,
    ILogger<OperationsTelemetryPublisher> logger) : BackgroundService
{
    private readonly string _statePath = configuration["Operations:StatePath"] ?? @"C:\ProgramData\AevryndWeb\operations\operations-state.json";
    private readonly string _codexStatusPath = configuration["Operations:CodexStatusPath"] ?? @"C:\ProgramData\Aevrynd\Codex\status.json";
    private readonly string _codexHistoryPath = configuration["Operations:CodexHistoryPath"] ??
        Path.Combine(Path.GetDirectoryName(configuration["Operations:CodexStatusPath"] ?? @"C:\ProgramData\Aevrynd\Codex\status.json")!, "operations-history.json");
    private ulong _previousIdle;
    private ulong _previousKernel;
    private ulong _previousUser;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (!OperatingSystem.IsWindows()) return;
        Directory.CreateDirectory(Path.GetDirectoryName(_statePath)!);
        while (!stoppingToken.IsCancellationRequested)
        {
            try { Publish(DateTimeOffset.UtcNow); }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or ExternalException)
            { logger.LogWarning(exception, "Operations telemetry publish skipped."); }
            await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
        }
    }

    private void Publish(DateTimeOffset now)
    {
        var cpu = ReadCpuPercent();
        var memory = new MemoryStatus();
        GlobalMemoryStatusEx(ref memory);
        var previous = ReadPrevious();
        var nodes = previous?.Nodes?.Where(node => !string.Equals(node.Id, "local", StringComparison.Ordinal)).ToList()
            ?? [];
        nodes.Insert(0, new OperationsNodeState
        {
            Id = "local", CpuPercent = cpu, RamPercent = memory.Total > 0 ? 100d * (memory.Total - memory.Available) / memory.Total : null,
            GpuPercent = ReadGpuPercent(), SampledAt = now
        });
        var authoritativeHistory = ReadCodexHistory(now);
        var cachedHistory = ReconcileCachedHistory(previous?.History, authoritativeHistory);
        var history = MergeHistory(cachedHistory, authoritativeHistory);
        var codexWork = ResolveCodexWork(previous?.ActiveWork, ReadCodexWork(now, previous?.ActiveWork), history);
        var activeWork = previous?.ActiveWork?.Where(item => !string.Equals(item.Type, "codex", StringComparison.Ordinal)).ToList() ?? [];
        if (codexWork is not null) activeWork.Insert(0, codexWork);
        var document = new OperationsStateDocument
        {
            Version = 1,
            SnapshotAt = now,
            Nodes = nodes,
            ActiveWork = activeWork,
            History = MergeHistory([], history)
        };
        var temporary = _statePath + ".tmp";
        File.WriteAllText(temporary, JsonSerializer.Serialize(document, new JsonSerializerOptions { WriteIndented = true }));
        File.Move(temporary, _statePath, true);
    }

    private static OperationsWorkState? ResolveCodexWork(
        IReadOnlyCollection<OperationsWorkState>? previousActive,
        OperationsWorkState? current,
        IReadOnlyCollection<OperationsWorkState> history)
    {
        // status 缺失或 TTL 過期只代表 publisher 暫時沒有新證據；保留原始時間讓頁面標示 stale，不能臆造 terminal。
        var candidate = current ?? previousActive?.FirstOrDefault(item => string.Equals(item.Type, "codex", StringComparison.Ordinal));
        return candidate is not null && !history.Any(item => SameIdentity(item, candidate)) ? candidate : null;
    }

    private static List<OperationsWorkState> ReconcileCachedHistory(
        IReadOnlyCollection<OperationsWorkState>? cached,
        IReadOnlyCollection<OperationsWorkState> authoritative)
    {
        return (cached ?? [])
            .Where(item => !IsLegacySyntheticCancelled(item) || authoritative.Any(entry => SameIdentity(entry, item)))
            .ToList();
    }

    private static bool IsLegacySyntheticCancelled(OperationsWorkState item) =>
        item.Type == "codex" && item.Host == "local" && item.Status == "cancelled" &&
        item.EvidenceSummary == "工作摘要停止更新；來源未提供結束原因。";

    private OperationsWorkState? ReadCodexWork(DateTimeOffset now, IReadOnlyCollection<OperationsWorkState>? previousActive)
    {
        try
        {
            if (!SafeSourceFile(_codexStatusPath, 8192)) return null;
            var raw = File.ReadAllBytes(_codexStatusPath);
            var status = JsonSerializer.Deserialize<CodexStatusDocument>(raw, StrictJson);
            if (status is null || status.SchemaVersion != 1 || status.Status is not ("working" or "blocked") ||
                status.Progress is < 0 or > 100 || status.Ttl is < 1 or > 3600 || !SafeText(status.Task, 80) ||
                (status.Phase is not null && !SafeText(status.Phase, 120)) ||
                status.UpdatedUtc == default || status.UpdatedUtc > now.AddMinutes(1) ||
                now - status.UpdatedUtc > TimeSpan.FromSeconds(status.Ttl)) return null;
            if (status.StartedUtc.HasValue && (status.StartedUtc.Value == default || status.StartedUtc > status.UpdatedUtc ||
                status.StartedUtc < now.AddYears(-1))) return null;
            var previous = previousActive?.FirstOrDefault(item => item.Type == "codex" && item.Name == status.Task.Trim());
            var startedAt = status.StartedUtc ?? previous?.StartedAt ?? status.UpdatedUtc;
            return new OperationsWorkState
            {
                Name = status.Task.Trim(), Type = "codex", Host = "local", StartedAt = startedAt,
                UpdatedAt = status.UpdatedUtc, Status = status.Status, EvidenceSummary = status.Phase
            };
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        { return null; }
    }

    private List<OperationsWorkState> ReadCodexHistory(DateTimeOffset now)
    {
        try
        {
            if (!File.Exists(_codexHistoryPath)) return [];
            if (!SafeSourceFile(_codexHistoryPath, 524_288)) return [];
            var document = JsonSerializer.Deserialize<CodexHistoryDocument>(File.ReadAllBytes(_codexHistoryPath), StrictJson);
            if (document is null || document.SchemaVersion != 1 || document.Events is null || document.Events.Count > 500) return [];
            var result = new List<OperationsWorkState>(document.Events.Count);
            foreach (var item in document.Events)
            {
                if (item is null || !SafeText(item.Name, 80) || !SafeText(item.Type, 40) || item.Status is not ("completed" or "failed" or "cancelled") ||
                    item.StartedAt == default || item.UpdatedAt == default || item.EndedAt == default ||
                    item.StartedAt > item.UpdatedAt || item.UpdatedAt > item.EndedAt || item.EndedAt > now.AddMinutes(1) ||
                    (item.EvidenceSummary is not null && !SafeText(item.EvidenceSummary, 240))) return [];
                result.Add(new OperationsWorkState { Name = item.Name, Type = item.Type, Host = "local", StartedAt = item.StartedAt,
                    UpdatedAt = item.UpdatedAt, EndedAt = item.EndedAt, Status = item.Status, EvidenceSummary = item.EvidenceSummary });
            }
            return MergeHistory([], result);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        { return []; }
    }

    private static List<OperationsWorkState> MergeHistory(IEnumerable<OperationsWorkState>? existing, IEnumerable<OperationsWorkState> incoming) =>
        (existing ?? []).Concat(incoming).Where(item => item is not null)
            .GroupBy(item => (item.Name, item.StartedAt))
            .Select(group => group.OrderByDescending(item => item.UpdatedAt).First())
            .OrderBy(item => item.StartedAt).TakeLast(500).ToList();

    private static bool SameIdentity(OperationsWorkState left, OperationsWorkState right) =>
        StringComparer.Ordinal.Equals(left.Name, right.Name) && left.StartedAt == right.StartedAt;

    private static bool SafeSourceFile(string path, int maximum)
    {
        var item = new FileInfo(path);
        return item.Exists && item.Length is >= 2 && item.Length <= maximum && (item.Attributes & FileAttributes.ReparsePoint) == 0;
    }

    private static bool SafeText(string? value, int maximum) => !string.IsNullOrWhiteSpace(value) && value.Length <= maximum &&
        !value.Any(char.IsControl) && !value.Contains("://", StringComparison.Ordinal) && !value.Contains('@') &&
        !value.Contains(":\\", StringComparison.Ordinal) && !IpAddressShape.IsMatch(value);

    private static readonly JsonSerializerOptions StrictJson = new() { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private static readonly Regex IpAddressShape = new(@"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)", RegexOptions.CultureInvariant);

    private OperationsStateDocument? ReadPrevious()
    {
        try
        {
            if (!File.Exists(_statePath)) return null;
            return JsonSerializer.Deserialize<OperationsStateDocument>(File.ReadAllText(_statePath));
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        { return null; }
    }

    private double? ReadCpuPercent()
    {
        if (!GetSystemTimes(out var idle, out var kernel, out var user)) return null;
        var idleTicks = ToUInt64(idle); var kernelTicks = ToUInt64(kernel); var userTicks = ToUInt64(user);
        if (_previousKernel == 0) { _previousIdle = idleTicks; _previousKernel = kernelTicks; _previousUser = userTicks; return null; }
        var total = (kernelTicks - _previousKernel) + (userTicks - _previousUser);
        var busy = total > 0 ? total - (idleTicks - _previousIdle) : 0;
        _previousIdle = idleTicks; _previousKernel = kernelTicks; _previousUser = userTicks;
        return total > 0 ? Math.Round(100d * busy / total, 1) : null;
    }

    private static double? ReadGpuPercent()
    {
        try
        {
            using var process = Process.Start(new ProcessStartInfo
            {
                FileName = "nvidia-smi",
                Arguments = "--query-gpu=utilization.gpu --format=csv,noheader,nounits",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            });
            if (process is null) return null;
            var output = process.StandardOutput.ReadToEnd();
            if (!process.WaitForExit(1500)) { try { process.Kill(); } catch { } return null; }
            var values = output.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries)
                .Select(value => double.TryParse(value.Trim(), System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out var parsed) ? parsed : (double?)null)
                .Where(value => value.HasValue).Select(value => value!.Value).ToArray();
            return values.Length == 0 ? null : Math.Round(values.Average(), 1);
        }
        catch (Exception exception) when (exception is InvalidOperationException or System.ComponentModel.Win32Exception)
        { return null; }
    }

    private static ulong ToUInt64(System.Runtime.InteropServices.ComTypes.FILETIME value) => ((ulong)(uint)value.dwHighDateTime << 32) | (uint)value.dwLowDateTime;

    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GetSystemTimes(out System.Runtime.InteropServices.ComTypes.FILETIME idle, out System.Runtime.InteropServices.ComTypes.FILETIME kernel, out System.Runtime.InteropServices.ComTypes.FILETIME user);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    [StructLayout(LayoutKind.Sequential)] private struct MemoryStatus { public uint Length; public uint MemoryLoad; public ulong Total; public ulong Available; public ulong PageFile; public ulong AvailablePageFile; public ulong Virtual; public ulong AvailableVirtual; public ulong AvailableExtended; public MemoryStatus() { Length = (uint)Marshal.SizeOf<MemoryStatus>(); } }

    private sealed class CodexStatusDocument
    {
        [JsonRequired, JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonRequired, JsonPropertyName("status")] public string Status { get; set; } = string.Empty;
        [JsonRequired, JsonPropertyName("task")] public string Task { get; set; } = string.Empty;
        [JsonPropertyName("phase")] public string? Phase { get; set; }
        [JsonPropertyName("progress")] public int? Progress { get; set; }
        [JsonPropertyName("startedUtc")] public DateTimeOffset? StartedUtc { get; set; }
        [JsonRequired, JsonPropertyName("updatedUtc")] public DateTimeOffset UpdatedUtc { get; set; }
        [JsonRequired, JsonPropertyName("ttl")] public int Ttl { get; set; }
    }

    private sealed class CodexHistoryDocument
    {
        [JsonRequired, JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonRequired, JsonPropertyName("events")] public List<CodexHistoryEvent?> Events { get; set; } = [];
    }

    private sealed class CodexHistoryEvent
    {
        [JsonRequired, JsonPropertyName("name")] public string Name { get; set; } = string.Empty;
        [JsonRequired, JsonPropertyName("type")] public string Type { get; set; } = string.Empty;
        [JsonRequired, JsonPropertyName("startedAt")] public DateTimeOffset StartedAt { get; set; }
        [JsonRequired, JsonPropertyName("updatedAt")] public DateTimeOffset UpdatedAt { get; set; }
        [JsonRequired, JsonPropertyName("endedAt")] public DateTimeOffset EndedAt { get; set; }
        [JsonRequired, JsonPropertyName("status")] public string Status { get; set; } = string.Empty;
        [JsonRequired, JsonPropertyName("evidenceSummary")] public string? EvidenceSummary { get; set; }
    }
}
