using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using AevryndWeb.Models;

namespace AevryndWeb.Security;

public sealed class OperationsScheduleProvider(IConfiguration configuration)
{
    private string StatePath => configuration["Operations:SchedulePath"] ?? @"C:\ProgramData\AevryndWeb\operations\task-schedule.json";
    private static readonly HashSet<string> Nodes = new(StringComparer.Ordinal) { "local", "taichung", "taoyuan" };
    private static readonly HashSet<string> States = new(StringComparer.Ordinal) { "queued", "acknowledged", "running", "blocked", "unconfirmed" };
    private static readonly HashSet<string> TerminalStates = new(StringComparer.Ordinal) { "completed", "failed", "cancelled" };
    private static readonly Regex IdPattern = new(@"^[A-Z0-9][A-Z0-9_-]{0,159}$", RegexOptions.CultureInvariant);
    private static readonly Regex PrivateText = new(@"[\x00-\x1f\x7f]|://|@|[A-Za-z]:[\\/]|(?:\d{1,3}\.){3}\d{1,3}|-----BEGIN", RegexOptions.CultureInvariant);
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
    };

    public OperationsScheduleView Read(DateTimeOffset now, OperationsViewModel snapshot)
    {
        try
        {
            var file = new FileInfo(StatePath);
            if (!file.Exists || file.Length is < 2 or > 262144 || (file.Attributes & FileAttributes.ReparsePoint) != 0 ||
                (OperatingSystem.IsWindows() && (!OperationsFileSecurity.HasSafeAcl(file.FullName) || !OperationsFileSecurity.HasSafeAcl(file.DirectoryName!))))
                return new(false, false, null, []);
            return Parse(File.ReadAllText(file.FullName), now, snapshot);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or ArgumentException)
        { return new(false, false, null, []); }
    }

    public static OperationsScheduleView Parse(string json, DateTimeOffset now, OperationsViewModel snapshot)
    {
        try
        {
            if (json.Length > 262144) return new(false, false, null, []);
            var document = JsonSerializer.Deserialize<ScheduleDocument>(json, JsonOptions);
            if (document is null || document.SchemaVersion is not (1 or 2) || document.ObservedAt == default || document.ObservedAt > now.AddMinutes(1) ||
                document.VerifiedAt > now.AddMinutes(1) || document.VerifiedAt < document.ObservedAt ||
                (document.SchemaVersion == 1 && document.VerifiedAt.HasValue) ||
                document.Tasks is null || document.Tasks.Count > 100 ||
                document.Tasks.Any(task => !Valid(task, document.SchemaVersion, document.ObservedAt, now)) ||
                document.Tasks.Select(task => (task.NodeId, task.Id)).Distinct().Count() != document.Tasks.Count)
                return new(false, false, null, []);
            var tasks = new List<OperationsScheduledTaskView>();
            var catalog = new List<OperationsScheduledTaskView>();
            foreach (var task in document.Tasks)
            {
                catalog.Add(new(task.Id, task.NodeId, task.Title, task.Description, task.State, task.Reason,
                    task.DependsOn, task.AssignedAt, task.UpdatedAt, task.Evidence));
                if (TerminalStates.Contains(task.State)) continue;
                var host = OperationsScheduleView.NodeHost(task.NodeId);
                var matching = snapshot.SourceAvailable ? snapshot.ActiveWork.Concat(snapshot.History)
                    .Where(item => item.Host == host && item.Name == task.Id && item.StartedAt >= task.AssignedAt).ToArray() : [];
                var latestStart = matching.Length > 0 ? matching.Max(item => item.StartedAt) : (DateTimeOffset?)null;
                // 只接合相同節點與命令的明確終態；遙測刷新與逾時不能自行推測工作結束。
                if (snapshot.SourceAvailable && snapshot.History.Any(item => item.Host == host && item.Name == task.Id &&
                    item.StartedAt >= task.AssignedAt && item.StartedAt == latestStart &&
                    (document.SchemaVersion == 1 || item.EndedAt > task.UpdatedAt) && IsExplicitTerminal(item))) continue;
                var current = snapshot.SourceAvailable ? snapshot.ActiveWork.FirstOrDefault(item => item.Host == host && item.Name == task.Id &&
                    item.StartedAt >= task.AssignedAt && item.StartedAt == latestStart &&
                    item.UpdatedAt.HasValue && item.UpdatedAt >= task.UpdatedAt) : null;
                var state = task.State;
                var reason = task.Reason;
                var updated = task.UpdatedAt;
                var conflict = document.SchemaVersion == 2 ? matching.FirstOrDefault(item => item.StartedAt == latestStart && item.EndedAt == task.UpdatedAt && IsExplicitTerminal(item)) : null;
                if (conflict is not null)
                {
                    state = "unconfirmed";
                    reason = $"來源狀態衝突：排程回報 {task.State}，遙測在同一事件時間回報 {conflict.Status}；保留原始歷程，等待主機核對。";
                }
                if (current is not null && current.UpdatedAt > task.UpdatedAt)
                {
                    updated = current.UpdatedAt!.Value;
                    state = current.Status == "blocked" ? "blocked" : task.NodeId == "local" && task.State == "running" ? "running" : "acknowledged";
                    reason = current.Status == "blocked" ? "工作來源回報受阻；等待後續處理。" : "工作來源有更新；接單回報不等於已確認程序正在執行。";
                }
                tasks.Add(new(task.Id, task.NodeId, task.Title, task.Description, state, reason,
                    task.DependsOn, task.AssignedAt, updated, task.Evidence));
            }
            return new(true, now - (document.VerifiedAt ?? document.ObservedAt) > TimeSpan.FromMinutes(2), document.ObservedAt,
                tasks.OrderBy(task => task.NodeId, StringComparer.Ordinal).ThenBy(task => task.AssignedAt).ThenBy(task => task.Id, StringComparer.Ordinal).ToArray()) { Catalog = catalog, VerifiedAt = document.VerifiedAt };
        }
        catch (JsonException) { return new(false, false, null, []); }
    }

    public static OperationsViewModel ReconcileWork(OperationsViewModel snapshot)
    {
        if (!snapshot.SourceAvailable) return snapshot;
        // 終態只排除同一工作實例；不得用較舊或其他主機的終態結束新工作。
        var terminal = snapshot.History.Where(IsExplicitTerminal).Select(item => (item.Host, item.Name, item.StartedAt)).ToHashSet();
        return snapshot with { ActiveWork = snapshot.ActiveWork.Where(item => !terminal.Contains((item.Host, item.Name, item.StartedAt))).ToArray() };
    }

    private static bool IsExplicitTerminal(OperationsWorkView item) => item.EndedAt.HasValue && TerminalStates.Contains(item.Status) &&
        item.EvidenceSummary != "工作摘要停止更新；來源未提供結束原因。";

    private static bool Valid(ScheduleTask? task, int schemaVersion, DateTimeOffset observed, DateTimeOffset now) => task is not null &&
        task.Id is not null && IdPattern.IsMatch(task.Id) && task.NodeId is not null && Nodes.Contains(task.NodeId) &&
        task.State is not null && (States.Contains(task.State) || schemaVersion == 2 && TerminalStates.Contains(task.State)) && Safe(task.Title, 80) && Safe(task.Description, 600) &&
        Safe(task.Reason, 400) && Safe(task.Evidence, 240) && task.DependsOn is not null && task.DependsOn.Count <= 10 &&
        task.DependsOn.All(id => id is not null && IdPattern.IsMatch(id) && id != task.Id) &&
        task.DependsOn.Distinct(StringComparer.Ordinal).Count() == task.DependsOn.Count &&
        task.AssignedAt != default && task.AssignedAt <= task.UpdatedAt && task.UpdatedAt <= observed.AddMinutes(1) && task.UpdatedAt <= now.AddMinutes(1);

    private static bool Safe(string? value, int maximum) => !string.IsNullOrWhiteSpace(value) && value.Length <= maximum && !PrivateText.IsMatch(value);

    private sealed class ScheduleDocument
    {
        [JsonRequired] public int SchemaVersion { get; set; }
        [JsonRequired] public DateTimeOffset ObservedAt { get; set; }
        public DateTimeOffset? VerifiedAt { get; set; }
        [JsonRequired] public List<ScheduleTask> Tasks { get; set; } = [];
    }
    private sealed class ScheduleTask
    {
        [JsonRequired] public string Id { get; set; } = "";
        [JsonRequired] public string NodeId { get; set; } = "";
        [JsonRequired] public string Title { get; set; } = "";
        [JsonRequired] public string Description { get; set; } = "";
        [JsonRequired] public string State { get; set; } = "";
        [JsonRequired] public string Reason { get; set; } = "";
        [JsonRequired] public List<string> DependsOn { get; set; } = [];
        [JsonRequired] public DateTimeOffset AssignedAt { get; set; }
        [JsonRequired] public DateTimeOffset UpdatedAt { get; set; }
        [JsonRequired] public string Evidence { get; set; } = "";
    }
}
