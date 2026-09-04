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

public sealed class FileOperationsSnapshotProvider(IConfiguration configuration) : IOperationsSnapshotProvider
{
    private static readonly (string Id, string Name)[] KnownNodes = [("local", "本機"), ("taichung", "台中"), ("taoyuan", "桃園")];
    private string StatePath => configuration["Operations:StatePath"] ?? @"C:\ProgramData\AevryndWeb\operations-state.json";

    public OperationsViewModel Read(DateTimeOffset now)
    {
        var unavailable = Empty("unavailable：找不到通過 ACL 與 schema 驗證的操作摘要。");
        try
        {
            var directory = Path.GetDirectoryName(StatePath);
            if (!OperatingSystem.IsWindows() || directory is null || !Directory.Exists(directory) || !File.Exists(StatePath) || !HasSafeAcl(directory) || !HasSafeAcl(StatePath)) return unavailable;
            var info = new FileInfo(StatePath); if (info.Length is <= 0 or > 524_288) return Empty("invalid：操作摘要大小不符合限制。");
            var document = JsonSerializer.Deserialize<OperationsStateDocument>(File.ReadAllText(StatePath), new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = false,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
            });
            return document is not null && OperationsSnapshotSchema.TryNormalize(document, now, out var model)
                ? model
                : Empty("invalid：操作摘要 schema 或時間無效。");
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or ArgumentException)
        { return Empty("invalid：操作摘要無法安全讀取。"); }
    }

    private OperationsViewModel Empty(string status) => new(KnownNodes.Select(node => new OperationsNodeView(node.Id, node.Name, null, null, null, null, true)).ToArray(), [], [], null, false, status);

    [SupportedOSPlatform("windows")]
    private static bool HasSafeAcl(string path)
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
            now - document.SnapshotAt > TimeSpan.FromMinutes(2) ? "stale：摘要超過兩分鐘未更新。" : "current");
        return true;
    }

    private static OperationsNodeView NormalizeNode(string id, string name, OperationsNodeState? node, DateTimeOffset now)
    {
        if (node is null || node.SampledAt == default || node.SampledAt > now.AddMinutes(1)) return new(id, name, null, null, null, null, true);
        return new(id, name, Metric(node.CpuPercent), Metric(node.RamPercent), Metric(node.GpuPercent), node.SampledAt, now - node.SampledAt > TimeSpan.FromMinutes(2));
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
