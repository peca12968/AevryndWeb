using System.Security.AccessControl;
using System.Security.Principal;
using System.Runtime.Versioning;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using AevryndWeb.Models;

namespace AevryndWeb.Security;

public interface IOperationsSnapshotProvider
{
    OperationsViewModel Read(DateTimeOffset now);
}

public sealed class FileOperationsSnapshotProvider(IConfiguration configuration, IRemoteTelemetryStore remoteTelemetry, RemoteTelemetryDiagnostics? diagnostics = null) : IOperationsSnapshotProvider
{
    private static readonly (string Id, string Name)[] KnownNodes = [("local", "本機"), ("taichung", "台中"), ("taoyuan", "桃園")];
    private string StatePath => configuration["Operations:StatePath"] ?? @"C:\ProgramData\AevryndWeb\operations\operations-state.json";

    public OperationsViewModel Read(DateTimeOffset now)
    {
        try
        {
            var directory = Path.GetDirectoryName(StatePath);
            if (!OperatingSystem.IsWindows() || directory is null || !Directory.Exists(directory) || !File.Exists(StatePath) || !HasSafeAcl(directory) || !HasSafeAcl(StatePath))
                return Empty("unavailable：找不到通過 ACL 與 schema 驗證的操作摘要。", now);
            var info = new FileInfo(StatePath); if (info.Length is <= 0 or > 524_288) return Empty("invalid：操作摘要大小不符合限制。", now);
            var document = JsonSerializer.Deserialize<OperationsStateDocument>(File.ReadAllText(StatePath), new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = false,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
            });
            if (document is null || !OperationsSnapshotSchema.TryNormalize(document, now, out var model))
                return Empty("invalid：操作摘要 schema 或時間無效。", now);
            var nodes = model.Nodes.ToArray();
            var activeWork = model.ActiveWork.ToList();
            var history = model.History.ToList();
            for (var index = 0; index < nodes.Length; index++)
            {
                if (nodes[index].Id == "local") continue;
                if (remoteTelemetry.TryReadFreshSnapshot(nodes[index].Id, now, out var remote))
                {
                    // 遠端 store 的 freshness window 是兩分鐘；頁面節點契約仍以 35 秒區分 current/stale。
                    // 因此 35–120 秒的最後實測值必須保留並標示 stale，不得硬設 current。
                    nodes[index] = OperationsSnapshotSchema.NormalizeNode(nodes[index].Id, nodes[index].Name, remote.Node, now);
                    if (OperationsSnapshotSchema.TryNormalizeRemoteWork(remote.ActiveWork, remote.History, nodes[index].Id, now, out var remoteActive, out var remoteHistory))
                    { activeWork.AddRange(remoteActive); history.AddRange(remoteHistory); }
                }
                else
                {
                    // 過期時先無條件清除 remote metrics；歷程保存與即時 metrics TTL 分離。
                    nodes[index] = new OperationsNodeView(nodes[index].Id, nodes[index].Name, null, null, null, null, true, "unavailable",
                        remoteTelemetry.ReadDiagnostic(nodes[index].Id, now) + (diagnostics?.Describe(nodes[index].Id, now) ?? ""));
                    if (remoteTelemetry.TryReadHistory(nodes[index].Id, now, out var persistedHistory) &&
                        OperationsSnapshotSchema.TryNormalizeRemoteWork([], persistedHistory, nodes[index].Id, now, out _, out var normalizedPersistedHistory))
                        history.AddRange(normalizedPersistedHistory);
                }
            }
            return model with
            {
                Nodes = nodes,
                ActiveWork = activeWork.OrderByDescending(item => item.UpdatedAt ?? item.StartedAt).ToArray(),
                History = history.GroupBy(item => (item.Host, item.Name, item.StartedAt)).Select(group => group.OrderByDescending(item => item.UpdatedAt).First()).OrderByDescending(item => item.StartedAt).Take(500).ToArray()
            };
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or ArgumentException)
        { return Empty("invalid：操作摘要無法安全讀取。", now); }
    }

    private OperationsViewModel Empty(string status, DateTimeOffset now)
    {
        var nodes = KnownNodes.Select(node => new OperationsNodeView(node.Id, node.Name, null, null, null, null, true, "unavailable",
            node.Id == "local" ? "LOCAL_STATE_UNAVAILABLE：本機操作摘要無法驗證。" : remoteTelemetry.ReadDiagnostic(node.Id, now) + (diagnostics?.Describe(node.Id, now) ?? ""))).ToArray();
        var active = new List<OperationsWorkView>(); var history = new List<OperationsWorkView>();
        // 本機摘要失效不能遮蔽另外通過簽章、schema 與時效驗證的副機資料。
        for (var index = 1; index < nodes.Length; index++)
        {
            if (remoteTelemetry.TryReadFreshSnapshot(nodes[index].Id, now, out var snapshot))
            {
                nodes[index] = OperationsSnapshotSchema.NormalizeNode(nodes[index].Id, nodes[index].Name, snapshot.Node, now);
                if (OperationsSnapshotSchema.TryNormalizeRemoteWork(snapshot.ActiveWork, snapshot.History, nodes[index].Id, now, out var work, out var past))
                { active.AddRange(work); history.AddRange(past); }
            }
            else if (remoteTelemetry.TryReadHistory(nodes[index].Id, now, out var past) &&
                OperationsSnapshotSchema.TryNormalizeRemoteWork([], past, nodes[index].Id, now, out _, out var normalized)) history.AddRange(normalized);
        }
        return new(nodes, active, history.OrderByDescending(work => work.StartedAt).Take(500).ToArray(), null, false, status, []);
    }

    [SupportedOSPlatform("windows")]
    private static bool HasSafeAcl(string path) => OperationsFileSecurity.HasSafeAcl(path);
}

internal static class OperationsFileSecurity
{
    [SupportedOSPlatform("windows")]
    internal static bool HasSafeAcl(string path)
    {
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) return false;
        var current = WindowsIdentity.GetCurrent().User; if (current is null) return false;
        FileSystemSecurity security = File.Exists(path) ? FileSystemAclExtensions.GetAccessControl(new FileInfo(path)) : FileSystemAclExtensions.GetAccessControl(new DirectoryInfo(path));
        var owner = (SecurityIdentifier?)security.GetOwner(typeof(SecurityIdentifier));
        var administrators = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null); var system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
        if (owner is null || (!owner.Equals(current) && !owner.Equals(administrators) && !owner.Equals(system))) return false;
        foreach (FileSystemAccessRule rule in security.GetAccessRules(true, true, typeof(SecurityIdentifier)))
        {
            if (rule.AccessControlType != AccessControlType.Allow) continue;
            var sid = (SecurityIdentifier)rule.IdentityReference;
            if (sid.Equals(current) || sid.Equals(administrators) || sid.Equals(system)) continue;
            const FileSystemRights dangerous = FileSystemRights.Read | FileSystemRights.ReadData | FileSystemRights.ReadAttributes | FileSystemRights.ReadExtendedAttributes |
                FileSystemRights.Write | FileSystemRights.Modify | FileSystemRights.FullControl |
                FileSystemRights.CreateFiles | FileSystemRights.CreateDirectories | FileSystemRights.WriteData | FileSystemRights.AppendData |
                FileSystemRights.WriteAttributes | FileSystemRights.WriteExtendedAttributes | FileSystemRights.ChangePermissions | FileSystemRights.TakeOwnership;
            if ((rule.FileSystemRights & dangerous) != 0) return false;
        }
        return true;
    }
}

public static class OperationsSnapshotSchema
{
    private static readonly (string Id, string Name)[] KnownNodes = [("local", "本機"), ("taichung", "台中"), ("taoyuan", "桃園")];
    private static readonly HashSet<string> WorkStatuses = new(StringComparer.Ordinal) { "working", "completed", "failed", "blocked", "cancelled" };
    private static readonly Regex IpAddressShape = new(@"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)", RegexOptions.CultureInvariant);

    public static bool TryNormalize(OperationsStateDocument document, DateTimeOffset now, out OperationsViewModel model)
    {
        model = default!;
        if (document.Version != 1 || document.SnapshotAt == default || document.SnapshotAt > now.AddMinutes(1) ||
            document.Nodes is null || document.Nodes.Count > KnownNodes.Length ||
            document.Nodes.Any(item => !KnownNodes.Any(known => known.Id == item.Id)) ||
            document.Nodes.Select(item => item.Id).Distinct(StringComparer.Ordinal).Count() != document.Nodes.Count ||
            !TryNormalizeWork(document.ActiveWork, now, false, 50, out var active) ||
            !TryNormalizeWork(document.History, now, true, 500, out var history)) return false;

        var sourceNodes = document.Nodes.ToDictionary(item => item.Id, StringComparer.Ordinal);
        var nodes = KnownNodes.Select(known => NormalizeNode(known.Id, known.Name, sourceNodes.GetValueOrDefault(known.Id), now)).ToArray();
        model = new(nodes, active, history.OrderByDescending(item => item.StartedAt).ToArray(), document.SnapshotAt, true,
            now - document.SnapshotAt > TimeSpan.FromMinutes(2) ? "stale：摘要超過兩分鐘未更新。" : "current", []);
        return true;
    }

    public static bool TryValidateRemoteWork(IReadOnlyList<OperationsWorkState> active, IReadOnlyList<OperationsWorkState> history, string nodeId, DateTimeOffset now) =>
        TryNormalizeRemoteWork(active, history, nodeId, now, out _, out _);

    public static bool TryNormalizeRemoteWork(IReadOnlyList<OperationsWorkState> active, IReadOnlyList<OperationsWorkState> history, string nodeId, DateTimeOffset now,
        out OperationsWorkView[] normalizedActive, out OperationsWorkView[] normalizedHistory)
    {
        normalizedActive = []; normalizedHistory = [];
        var activeKeys = active.Select(item => (item.Name, item.StartedAt)).ToHashSet();
        if (!KnownNodes.Any(node => node.Id == nodeId) || active.Any(item => item.Host != nodeId) || history.Any(item => item.Host != nodeId) ||
            active.GroupBy(item => (item.Name, item.StartedAt)).Any(group => group.Count() > 1) || history.GroupBy(item => (item.Name, item.StartedAt)).Any(group => group.Count() > 1)) return false;
        if (history.Any(item => activeKeys.Contains((item.Name, item.StartedAt)))) return false;
        return TryNormalizeWork(active.ToList(), now, false, 10, out normalizedActive) && TryNormalizeWork(history.ToList(), now, true, 100, out normalizedHistory);
    }

    internal static OperationsNodeView NormalizeNode(string id, string name, OperationsNodeState? node, DateTimeOffset now)
    {
        if (node is null || node.SampledAt == default || node.SampledAt > now.AddMinutes(1))
            return new(id, name, null, null, null, null, true, "unavailable", "摘要中沒有可驗證的採樣時間與量測值。");
        var cpu = Metric(node.CpuPercent); var ram = Metric(node.RamPercent); var gpu = Metric(node.GpuPercent);
        var stale = now - node.SampledAt > TimeSpan.FromSeconds(35);
        var availability = cpu is null && ram is null && gpu is null ? "unavailable" : stale ? "stale" : "current";
        var diagnostic = availability switch
        {
            "unavailable" => "採樣存在，但沒有任何通過範圍驗證的量測值。",
            "stale" => "採樣超過 35 秒未更新；保留最後實測值，不進行推估。",
            _ when gpu is null => "CPU 與 RAM 為即時實測；GPU 計數器不可用。",
            _ => "本機即時實測資料。"
        };
        return new(id, name, cpu, ram, gpu, node.SampledAt, stale || availability == "unavailable", availability, diagnostic);
    }

    private static bool TryNormalizeWork(List<OperationsWorkState>? source, DateTimeOffset now, bool completed, int maximum, out OperationsWorkView[] result)
    {
        result = [];
        if (source is null || source.Count > maximum) return false;
        var normalized = new List<OperationsWorkView>(source.Count);
        foreach (var item in source)
        {
            if (!SafeText(item.Name, 80) || !SafeText(item.Type, 40) || !KnownNodes.Any(node => node.Id == item.Host) || !WorkStatuses.Contains(item.Status) ||
                item.StartedAt == default || item.StartedAt > now.AddMinutes(1) || item.UpdatedAt > now.AddMinutes(1) || completed != item.EndedAt.HasValue ||
                item.EndedAt < item.StartedAt || item.UpdatedAt < item.StartedAt || item.UpdatedAt > item.EndedAt ||
                (!completed && item.Status is not ("working" or "blocked")) || (completed && item.Status is "working" or "blocked") ||
                (item.EvidenceSummary is not null && !SafeText(item.EvidenceSummary, 240))) return false;
            var label = KnownNodes.Single(node => node.Id == item.Host).Name;
            var referenceTime = item.UpdatedAt ?? item.StartedAt;
            normalized.Add(new(item.Name, item.Type, label, item.StartedAt, item.UpdatedAt, item.EndedAt, item.Status, item.EvidenceSummary, !completed && now - referenceTime > TimeSpan.FromMinutes(15)));
        }
        result = normalized.ToArray();
        return true;
    }

    private static double? Metric(double? value) => value.HasValue && value.Value is >= 0 and <= 100 && double.IsFinite(value.Value) ? Math.Round(value.Value, 1) : null;
    private static bool SafeText(string? value, int maximum) => !string.IsNullOrWhiteSpace(value) && value.Length <= maximum &&
        !value.Any(char.IsControl) && !value.Contains("://", StringComparison.Ordinal) && !value.Contains('@') && !value.Contains(":\\", StringComparison.Ordinal) && !IpAddressShape.IsMatch(value);
}

public sealed class OperationsStateDocument
{
    public int Version { get; set; }
    public DateTimeOffset SnapshotAt { get; set; }
    public List<OperationsNodeState>? Nodes { get; set; }
    public List<OperationsWorkState>? ActiveWork { get; set; }
    public List<OperationsWorkState>? History { get; set; }
}
public sealed class OperationsNodeState { public string Id { get; set; } = string.Empty; public double? CpuPercent { get; set; } public double? RamPercent { get; set; } public double? GpuPercent { get; set; } public DateTimeOffset SampledAt { get; set; } }
public sealed class OperationsWorkState { public string Name { get; set; } = string.Empty; public string Type { get; set; } = string.Empty; public string Host { get; set; } = string.Empty; public DateTimeOffset StartedAt { get; set; } public DateTimeOffset? UpdatedAt { get; set; } public DateTimeOffset? EndedAt { get; set; } public string Status { get; set; } = string.Empty; public string? EvidenceSummary { get; set; } }
