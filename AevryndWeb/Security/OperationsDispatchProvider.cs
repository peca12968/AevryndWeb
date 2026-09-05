using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AevryndWeb.Models;

namespace AevryndWeb.Security;

public sealed class OperationsDispatchProvider(IConfiguration configuration)
{
    public OperationsViewModel Read(DateTimeOffset now, OperationsViewModel model)
    {
        var directory = configuration["Operations:Dispatch:StateDirectory"] ?? @"C:\ProgramData\AevryndWeb\operations";
        try
        {
            var state = ReadSafe(Path.Combine(directory, "dispatch-state.json"), 2097152);
            var health = ReadSafe(Path.Combine(directory, "dispatch-health.json"), 8192);
            return Project(state, health, now, model);
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or ArgumentException or KeyNotFoundException or InvalidOperationException or FormatException)
        {
            return Unify(model with { Schedule = model.Schedule with { Stale = true,
                Diagnostic = "DISPATCH_SOURCE_UNAVAILABLE：動態派遣來源未提供可驗證快照；保留既有資料，不推測工作停止。" } });
        }
    }

    private static string ReadSafe(string path, long maximum)
    {
        var file = new FileInfo(path);
        if (!file.Exists || file.Length < 2 || file.Length > maximum) throw new IOException("DISPATCH_FILE_UNAVAILABLE");
        for (FileSystemInfo? item = file; item is not null; item = item is FileInfo f ? f.Directory : ((DirectoryInfo)item).Parent)
            if ((item.Attributes & FileAttributes.ReparsePoint) != 0) throw new IOException("DISPATCH_REPARSE_PATH");
        if (OperatingSystem.IsWindows() && (!OperationsFileSecurity.HasSafeAcl(path) || !OperationsFileSecurity.HasSafeAcl(file.DirectoryName!)))
            throw new IOException("DISPATCH_ACL_REJECTED");
        return File.ReadAllText(path);
    }

    public static OperationsViewModel Project(string state, string health, DateTimeOffset now, OperationsViewModel model)
    {
        var document = OperationsDispatchProjection.ReadDocument(state);
        using var parsed = JsonDocument.Parse(health);
        var root = parsed.RootElement;
        if (root.GetProperty("schemaVersion").GetInt32() != 1 ||
            root.GetProperty("stateSha256").GetString() != Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(state))) ||
            document.ObservedAt > now.AddMinutes(1)) throw new JsonException("DISPATCH_HEALTH_MISMATCH");
        DateTimeOffset? verified = root.GetProperty("lastSuccessAt").ValueKind == JsonValueKind.String
            ? root.GetProperty("lastSuccessAt").GetDateTimeOffset() : null;
        var status = root.GetProperty("status").GetString();
        if (verified > now.AddMinutes(1)) throw new JsonException("DISPATCH_HEALTH_FUTURE");
        var stale = status is not ("current" or "partial") || !verified.HasValue || now - verified.Value > TimeSpan.FromMinutes(2);
        var catalog = model.Schedule.Catalog.Where(old => !document.Tasks.Any(task => task.Id == old.Id && task.NodeId == old.NodeId)).ToList();
        var tasks = model.Schedule.Tasks.Where(old => !document.Tasks.Any(task => task.Id == old.Id && task.NodeId == old.NodeId)).ToList();
        var history = model.History.ToList();
        foreach (var task in document.Tasks)
        {
            var entry = new OperationsScheduledTaskView(task.Id, task.NodeId, task.Title, task.Description, task.State, task.Reason,
                task.DependsOn, task.AssignedAt, task.UpdatedAt, task.Evidence) { InstanceId = task.CommandCommentId.ToString(System.Globalization.CultureInfo.InvariantCulture) };
            catalog.Add(entry);
            if (task.State is "completed" or "failed")
            {
                if (!history.Any(work => work.Name == task.Id && work.Host == OperationsScheduleView.NodeHost(task.NodeId) && work.StartedAt >= task.AssignedAt))
                    history.Add(new(task.Id, "派遣事件（開始欄為指派時間）", OperationsScheduleView.NodeHost(task.NodeId), task.AssignedAt,
                        task.UpdatedAt, task.EndedAt, task.State, task.Evidence + " " + task.Reason, false));
                continue;
            }
            if (task.State is "cancelled" or "superseded") continue;
            if (task.State == "queued" && task.AckDeadline < now)
                entry = entry with { State = "unconfirmed", Reason = "接單期限已過，尚未驗證接單；未推測取消或完成。 " + entry.Reason };
            if (task.LeaseExpiresAt < now && task.State == "acknowledged")
                entry = entry with { State = "unconfirmed", Reason = "派遣租約已過，程序狀態待確認；未推測已停止。 " + entry.Reason };
            if (task.DependsOn.Any(id => !document.Tasks.Any(dependency => dependency.Id == id && dependency.State is "completed" or "failed" or "cancelled")))
                entry = entry with { State = "blocked", Reason = "相依任務尚無可驗證終態；" + entry.Reason };
            tasks.Add(entry);
        }
        return Unify(model with { History = history, Schedule = new(true, stale, document.ObservedAt, tasks)
        {
            Catalog = catalog, VerifiedAt = verified,
            Diagnostic = stale ? "DISPATCH_SOURCE_STALE：來源未在兩分鐘內完成線上核對；離線快照不代表已連線。" :
                status == "partial" ? "DISPATCH_EVENTS_REJECTED：部分留言格式或識別未通過驗證，僅顯示已驗證事件。" : "DISPATCH_SOURCE_CURRENT：完整來源已核對。"
        } });
    }

    // 單一任務區保留來源提供的真實時間；ACK、過期來源及租約都不能被升級為執行中。
    public static OperationsViewModel Unify(OperationsViewModel model)
    {
        var tasks = model.Schedule.Tasks.ToList();
        foreach (var work in model.ActiveWork)
        {
            var node = work.Host switch { "本機" => "local", "台中" => "taichung", "桃園" => "taoyuan", _ => "" };
            if (node.Length == 0) continue;
            var matched = tasks.Where(task => task.Id == work.Name && task.NodeId == node && work.StartedAt >= task.AssignedAt)
                .OrderByDescending(task => task.AssignedAt).FirstOrDefault();
            if (model.Schedule.Catalog.Any(task => task.Id == work.Name && task.NodeId == node && work.StartedAt >= task.AssignedAt &&
                task.State is "completed" or "failed" or "cancelled" or "superseded" &&
                !model.Schedule.Catalog.Any(newer => newer.Id == task.Id && newer.NodeId == node && newer.AssignedAt > task.AssignedAt && newer.AssignedAt <= work.StartedAt))) continue;
            var state = work.Stale ? "unconfirmed" : work.Status == "working" ? "running" : work.Status is "running" or "blocked" ? work.Status : "unconfirmed";
            var reason = (work.Stale ? "工作來源已過期；未推測已停止。" : "工作狀態由節點遙測提供。") + " " + (work.EvidenceSummary ?? "");
            if (matched is not null)
            {
                // 明確派遣受阻／待確認不能被較舊的程序快照覆蓋。
                if ((work.UpdatedAt ?? work.StartedAt) >= matched.UpdatedAt)
                    tasks[tasks.IndexOf(matched)] = matched with { State = state, Reason = reason, UpdatedAt = work.UpdatedAt ?? work.StartedAt };
            }
            else tasks.Add(new(work.Name, node, model.Schedule.WorkTitle(work), "節點目前工作；開始時間依來源保留。", state, reason, [],
                work.StartedAt, work.UpdatedAt ?? work.StartedAt, work.EvidenceSummary ?? "來源未提供摘要。") { InstanceId = node + "-" + work.Name + "-" + work.StartedAt.ToUnixTimeMilliseconds() });
        }
        return model with { Schedule = model.Schedule with { Tasks = tasks.OrderByDescending(task => task.UpdatedAt).ToArray() },
            History = model.History.Where(work => work.Status is "completed" or "failed" && work.EndedAt.HasValue).OrderByDescending(work => work.StartedAt).Take(500).ToArray() };
    }
}
