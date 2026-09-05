using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace AevryndWeb.Security;

public sealed record OperationsDispatchDocument(int SchemaVersion, DateTimeOffset? ObservedAt, IReadOnlyList<OperationsDispatchTask> Tasks, int RejectedEvents);
public sealed record OperationsDispatchTask(string Id, string NodeId, long CommandCommentId, string WorkKey, int Generation,
    string Title, string Description, string State, string Reason, string[] DependsOn, string? Supersedes,
    DateTimeOffset AssignedAt, DateTimeOffset UpdatedAt, DateTimeOffset? AcknowledgedAt, DateTimeOffset? EndedAt,
    DateTimeOffset? AckDeadline, DateTimeOffset? LeaseExpiresAt, long EventCommentId, string Evidence);

// 純資料投影：只接受固定 Issue 的 OWNER 事件，不執行派工內容，也不宣告程序存在。
public static class OperationsDispatchProjection
{
    public static async Task<string> ReadBoundedAsync(StreamReader reader, int limit, CancellationToken cancellationToken)
    {
        var result = new System.Text.StringBuilder(); var buffer = new char[4096];
        while (true)
        {
            var count = await reader.ReadAsync(buffer.AsMemory(), cancellationToken);
            if (count == 0) return result.ToString();
            if (result.Length + count > limit) throw new IOException("DISPATCH_PROCESS_OUTPUT_LIMIT");
            result.Append(buffer, 0, count);
        }
    }
    public const string IssueUrl = "https://api.github.com/repos/peca12968/Aevrynd/issues/1";
    public const string OwnerLogin = "peca12968";
    public const long OwnerId = 321279667;
    public static readonly JsonSerializerOptions JsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private static readonly Regex Identifier = new("^[A-Z0-9][A-Z0-9_-]{0,159}$", RegexOptions.CultureInvariant);
    private static readonly Regex PrivateText = new(@"[\x00-\x1f\x7f]|://|@|[A-Za-z]:[\\/]|(?:\d{1,3}\.){3}\d{1,3}|-----BEGIN", RegexOptions.CultureInvariant);
    private static readonly HashSet<string> Terminal = new(StringComparer.Ordinal) { "completed", "failed", "cancelled", "superseded" };
    private sealed record Event(long Id, DateTimeOffset CreatedAt, string Kind, Dictionary<string, string> Fields);
    private sealed record ArchiveDirective(long CommentId, string NodeId, long Cutoff, DateTimeOffset CreatedAt);
    private sealed record ArchivedCommand(long CommentId, string NodeId, string CommandId);
    private sealed record RejectedEvent(long CommentId, bool MayArchive);

    public static string BuildJson(string commentsJson, string? previousJson, DateTimeOffset now)
    {
        if (commentsJson.Length > 33_554_432) throw new JsonException("DISPATCH_INPUT_LIMIT");
        using var document = JsonDocument.Parse(commentsJson, new JsonDocumentOptions { MaxDepth = 40 });
        CheckDuplicateProperties(document.RootElement);
        var comments = Flatten(document.RootElement, 0).ToArray();
        if (comments.Length > 5000) throw new JsonException("DISPATCH_COMMENT_LIMIT");
        var events = new List<Event>();
        var archivedCommands = new List<ArchivedCommand>();
        var seen = new Dictionary<long, string>();
        var rejectedEvents = new List<RejectedEvent>();
        void Reject(long commentId, bool mayArchive = true) => rejectedEvents.Add(new(commentId, mayArchive));
        foreach (var comment in comments)
        {
            if (!Trusted(comment)) continue;
            var id = comment.GetProperty("id").GetInt64();
            var raw = comment.GetRawText();
            if (seen.TryGetValue(id, out var prior)) { if (prior != raw) throw new JsonException("DISPATCH_CONFLICTING_COMMENT"); continue; }
            seen.Add(id, raw);
            if (!comment.TryGetProperty("body", out var bodyElement) || bodyElement.ValueKind != JsonValueKind.String) { Reject(id); continue; }
            var body = bodyElement.GetString()!;
            var declaresArchive = body.Contains("ARCHIVE_THROUGH_COMMENT_ID:", StringComparison.OrdinalIgnoreCase);
            var trimmedBody = body.TrimStart();
            var declaresArchivedBridge = trimmedBody.StartsWith("[AEVRYND-ARCHIVED-BRIDGE]", StringComparison.Ordinal) ||
                trimmedBody.StartsWith("封存說明：此命令在狀態校正 cutoff 前沒有任何節點回覆，全文保留但不得再執行。", StringComparison.Ordinal);
            if (!TryTime(Text(comment, "created_at"), out var created) || created > now.AddMinutes(1)) { Reject(id, !declaresArchive && !declaresArchivedBridge); continue; }
            if (TryArchivedCommandEnvelope(body, out var archivedNode, out var archivedCommand))
            {
                archivedCommands.Add(new(id, archivedNode, archivedCommand));
                continue;
            }
            if (declaresArchivedBridge) { Reject(id, false); continue; }
            if (!TryEnvelope(body, out var kind, out var fields)) { if (body.Contains("COMMAND_ID:", StringComparison.Ordinal)) Reject(id, !declaresArchive); continue; }
            events.Add(new(id, created, kind, fields));
        }
        var ordered = events.OrderBy(item => item.CreatedAt).ThenBy(item => item.Id).ToArray();
        var tasks = new Dictionary<long, OperationsDispatchTask>();
        var leases = new Dictionary<long, int>();
        var archiveDirectives = new List<ArchiveDirective>();
        foreach (var item in ordered.Where(item => item.Kind == "MAIN_COMMAND"))
        {
            var fields = item.Fields;
            if (!Id(fields.GetValueOrDefault("COMMAND_ID")) || !Node(fields.GetValueOrDefault("TARGET"), out var node) ||
                !Number(fields, "GENERATION", 1, 1, 10000, out var generation) ||
                !Number(fields, "ACK_DEADLINE_SECONDS", 0, 0, 86400, out var ackSeconds) ||
                !Number(fields, "LEASE_SECONDS", 0, 0, 604800, out var leaseSeconds) ||
                !OptionalPositiveLongBefore(fields, "ARCHIVE_THROUGH_COMMENT_ID", item.Id, out var archiveThrough)) { Reject(item.Id, !fields.ContainsKey("ARCHIVE_THROUGH_COMMENT_ID")); continue; }
            var id = fields["COMMAND_ID"];
            var workKey = fields.GetValueOrDefault("WORK_KEY") ?? id;
            var supersedes = fields.GetValueOrDefault("SUPERSEDES_COMMAND_ID");
            var dependencies = (fields.GetValueOrDefault("DEPENDS_ON_COMMAND_ID") ?? fields.GetValueOrDefault("DEPENDS_ON") ?? "")
                .Split([',', ';', ' '], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
            if (!Id(workKey) || (supersedes is not null && (!Id(supersedes) || supersedes == id)) ||
                dependencies.Length > 10 || dependencies.Any(value => !Id(value) || value == id) || dependencies.Distinct(StringComparer.Ordinal).Count() != dependencies.Length) { Reject(item.Id, !fields.ContainsKey("ARCHIVE_THROUGH_COMMENT_ID")); continue; }
            var sourceTitle = fields.GetValueOrDefault("TITLE") ?? fields.GetValueOrDefault("TASK") ?? "";
            var title = SafeTitle(sourceTitle, node);
            var description = Safe(sourceTitle, 600) ? sourceTitle : "詳細工作範圍請依原始派工；此處僅顯示已驗證的任務狀態。";
            tasks.Add(item.Id, new(id, node, item.Id, workKey, generation, title, description, "queued", "已派送，尚未收到已驗證接單事件。",
                dependencies, supersedes, item.CreatedAt, item.CreatedAt, null, null,
                ackSeconds > 0 ? item.CreatedAt.AddSeconds(ackSeconds) : null, null, item.Id, "OWNER MAIN_COMMAND " + item.Id));
            leases[item.Id] = leaseSeconds;
            if (archiveThrough.HasValue) archiveDirectives.Add(new(item.Id, node, archiveThrough.Value, item.CreatedAt));
        }
        if (tasks.Count > 500) throw new JsonException("DISPATCH_TASK_LIMIT");
        foreach (var item in ordered.Where(item => item.Kind != "MAIN_COMMAND"))
        {
            var fields = item.Fields;
            if (fields.ContainsKey("ARCHIVE_THROUGH_COMMENT_ID")) { Reject(item.Id, false); continue; }
            if (!Id(fields.GetValueOrDefault("COMMAND_ID")) || !Node(fields.GetValueOrDefault("NODE"), out var node)) { Reject(item.Id); continue; }
            var candidates = tasks.Values.Where(task => task.Id == fields["COMMAND_ID"] && task.NodeId == node && task.AssignedAt <= item.CreatedAt).ToArray();
            if (fields.TryGetValue("COMMENT_ID", out var reference)) candidates = candidates.Where(task => reference == task.CommandCommentId.ToString(CultureInfo.InvariantCulture)).ToArray();
            if (fields.TryGetValue("GENERATION", out var generation)) candidates = candidates.Where(task => generation == task.Generation.ToString(CultureInfo.InvariantCulture)).ToArray();
            if (fields.TryGetValue("WORK_KEY", out var key)) candidates = candidates.Where(task => key == task.WorkKey).ToArray();
            if (candidates.Length != 1)
            {
                if (candidates.Length == 0 && IsArchivedLateEvent(item, fields, archivedCommands, archiveDirectives)) continue;
                Reject(item.Id); continue;
            }
            var task = candidates[0];
            var status = fields.GetValueOrDefault("STATUS");
            var ack = item.Kind == "NODE_ACK" || item.Kind == "BRIDGE" && status is "ACK" or "ACCEPTED";
            if (ack && status is not (null or "ACK" or "ACCEPTED" or "QUEUED_DEPENDENCY")) { Reject(item.Id); continue; }
            if (!ack && status is null) { Reject(item.Id); continue; }
            if (Terminal.Contains(task.State)) continue;
            var state = ack ? "acknowledged" : status switch
            {
                "COMPLETED" or "COMPLETE" => "completed",
                "FAILED" => "failed", "CANCELLED" => "cancelled",
                "BLOCKED" or "NEEDS_MAIN_VALIDATION" or "NEEDS_REMOTE_VALIDATION" => "blocked",
                // 未結構化的完成宣稱不自動成為成功；仍保留報告存在的證據。
                _ => "unconfirmed"
            };
            var reason = ack ? "已接單；接單不代表程序正在執行。" : state switch
            {
                "completed" => "節點明確回報完成；不代表其他驗收項目已通過。",
                "failed" => "節點明確回報失敗，等待主機處理。",
                "cancelled" => "節點明確回報取消。",
                "blocked" => "節點正在等待必要條件或主機驗證。",
                _ => "節點已提供報告，結果等待主機確認；未推定成功、失敗或程序狀態。"
            };
            if (!ack && Safe(status, 80)) reason += " 回報狀態：" + status + "。";
            var acknowledged = task.AcknowledgedAt ?? (ack ? item.CreatedAt : null);
            tasks[task.CommandCommentId] = task with
            {
                State = state, Reason = reason, UpdatedAt = item.CreatedAt, AcknowledgedAt = acknowledged,
                EndedAt = Terminal.Contains(state) ? item.CreatedAt : null,
                LeaseExpiresAt = task.LeaseExpiresAt ?? (ack && leases[task.CommandCommentId] > 0 ? item.CreatedAt.AddSeconds(leases[task.CommandCommentId]) : null),
                EventCommentId = item.Id, Evidence = $"OWNER MAIN_COMMAND {task.CommandCommentId}；{(ack ? "NODE_ACK" : "NODE_REPORT")} {item.Id}。"
            };
        }
        // 只有明確較新世代的取代宣告能收回派遣租約；逾時本身不能完成或取消舊工作。
        foreach (var replacement in tasks.Values.Where(task => task.Supersedes is not null).OrderBy(task => task.AssignedAt).ToArray())
        {
            var previous = tasks.Values.Where(task => task.Id == replacement.Supersedes && task.WorkKey == replacement.WorkKey &&
                task.Generation < replacement.Generation && task.AssignedAt < replacement.AssignedAt).ToArray();
            if (previous.Length != 1) { Reject(replacement.CommandCommentId); continue; }
            var old = previous[0];
            if (Terminal.Contains(old.State) && old.EndedAt <= replacement.AssignedAt) continue;
            tasks[old.CommandCommentId] = old with { State = "superseded", UpdatedAt = replacement.AssignedAt, EndedAt = replacement.AssignedAt,
                EventCommentId = replacement.CommandCommentId, Reason = "較新派工已明確接手或撤回此派遣租約；不代表舊程序已停止。",
                Evidence = $"OWNER MAIN_COMMAND {replacement.CommandCommentId} 明確取代 {old.CommandCommentId}。" };
        }
        if (!string.IsNullOrEmpty(previousJson))
        {
            var previous = ReadDocument(previousJson);
            foreach (var old in previous.Tasks)
            {
                // API 完整回應若遺失先前命令，保留已驗證證據；重新抓取不能復活已終止的同一派遣實例。
                if (!tasks.TryGetValue(old.CommandCommentId, out var current)) tasks[old.CommandCommentId] = old;
                else if (Terminal.Contains(old.State)) tasks[old.CommandCommentId] = old;
                else if (current.UpdatedAt < old.UpdatedAt) tasks[old.CommandCommentId] = old;
            }
        }
        // 快照校正只終止同節點、截止留言（含）以前仍非終態的派遣。放在 previous snapshot 合併後，
        // 可防止較舊快照把已封存的等待工作復活；既有終態與較新／其他節點工作均不受影響。
        foreach (var directive in archiveDirectives.OrderBy(item => item.CreatedAt).ThenBy(item => item.CommentId))
        {
            foreach (var old in tasks.Values.Where(task => task.NodeId == directive.NodeId &&
                task.CommandCommentId <= directive.Cutoff && task.AssignedAt <= directive.CreatedAt && !Terminal.Contains(task.State)).ToArray())
            {
                tasks[old.CommandCommentId] = old with
                {
                    State = "superseded", UpdatedAt = old.UpdatedAt > directive.CreatedAt ? old.UpdatedAt : directive.CreatedAt,
                    EndedAt = directive.CreatedAt, EventCommentId = directive.CommentId,
                    Reason = "OWNER 快照校正已封存此節點的較舊非終態派遣；不代表程序執行結果。",
                    Evidence = $"OWNER MAIN_COMMAND {directive.CommentId} 封存截至留言 {directive.Cutoff} 的派遣 {old.CommandCommentId}。"
                };
            }
        }
        if (tasks.Count > 500) throw new JsonException("DISPATCH_TASK_LIMIT");
        // 只有兩個遠端節點都以有效 OWNER MAIN_COMMAND 提供封存範圍，才可忽略共同涵蓋的歷史拒絕事件。
        // cutoff 不一致時採較小值；archive 指令本身的錯誤永遠不能被 horizon 隱藏。
        long? rejectionHorizon = null;
        var latestTaichung = archiveDirectives.Where(item => item.NodeId == "taichung").OrderBy(item => item.CreatedAt).ThenBy(item => item.CommentId).LastOrDefault();
        var latestTaoyuan = archiveDirectives.Where(item => item.NodeId == "taoyuan").OrderBy(item => item.CreatedAt).ThenBy(item => item.CommentId).LastOrDefault();
        if (latestTaichung is not null && latestTaoyuan is not null) rejectionHorizon = Math.Min(latestTaichung.Cutoff, latestTaoyuan.Cutoff);
        var rejected = rejectedEvents.Count(item => !rejectionHorizon.HasValue || !item.MayArchive || item.CommentId > rejectionHorizon.Value);
        var result = new OperationsDispatchDocument(1, tasks.Count > 0 ? tasks.Values.Max(task => task.UpdatedAt) : null,
            tasks.Values.OrderBy(task => task.AssignedAt).ThenBy(task => task.CommandCommentId).ToArray(), rejected);
        return JsonSerializer.Serialize(result, JsonOptions);
    }

    public static OperationsDispatchDocument ReadDocument(string json)
    {
        if (json.Length > 2_097_152) throw new JsonException("DISPATCH_STATE_LIMIT");
        using var parsed = JsonDocument.Parse(json); CheckDuplicateProperties(parsed.RootElement);
        var result = JsonSerializer.Deserialize<OperationsDispatchDocument>(json, JsonOptions) ?? throw new JsonException("DISPATCH_STATE_EMPTY");
        if (result.SchemaVersion != 1 || result.Tasks is null || result.Tasks.Count > 500 || result.RejectedEvents < 0 ||
            result.Tasks.Any(task => task is null) || result.Tasks.Select(task => task.CommandCommentId).Distinct().Count() != result.Tasks.Count ||
            result.Tasks.Any(task => !Id(task.Id) || !Id(task.WorkKey) || !Node(task.NodeId?.ToUpperInvariant(), out _) || task.CommandCommentId <= 0 ||
                task.Generation < 1 || !Safe(task.Title, 80) || !Safe(task.Description, 600) || !Safe(task.Reason, 400) || !Safe(task.Evidence, 240) ||
                task.State is not ("queued" or "acknowledged" or "blocked" or "unconfirmed" or "completed" or "failed" or "cancelled" or "superseded") ||
                task.AssignedAt == default || task.UpdatedAt < task.AssignedAt || task.AcknowledgedAt < task.AssignedAt ||
                task.EndedAt < task.AssignedAt || (Terminal.Contains(task.State) && !task.EndedAt.HasValue) ||
                task.DependsOn is null || task.DependsOn.Length > 10 || task.DependsOn.Any(value => !Id(value))))
            throw new JsonException("DISPATCH_STATE_INVALID");
        return result;
    }

    private static bool Trusted(JsonElement item) => item.ValueKind == JsonValueKind.Object &&
        item.TryGetProperty("id", out var id) && id.TryGetInt64(out var number) && number > 0 && Text(item, "issue_url") == IssueUrl &&
        Text(item, "author_association") == "OWNER" && item.TryGetProperty("user", out var user) &&
        Text(user, "login") == OwnerLogin && user.TryGetProperty("id", out var owner) && owner.TryGetInt64(out var ownerId) && ownerId == OwnerId;
    private static string? Text(JsonElement item, string key) => item.ValueKind == JsonValueKind.Object && item.TryGetProperty(key, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
    private static IEnumerable<JsonElement> Flatten(JsonElement item, int depth)
    {
        if (depth > 4) throw new JsonException("DISPATCH_NESTING_LIMIT");
        if (item.ValueKind == JsonValueKind.Object) { yield return item; yield break; }
        if (item.ValueKind != JsonValueKind.Array) throw new JsonException("DISPATCH_EXPECTED_ARRAY");
        foreach (var child in item.EnumerateArray()) foreach (var entry in Flatten(child, depth + 1)) yield return entry;
    }
    private static void CheckDuplicateProperties(JsonElement item)
    {
        if (item.ValueKind == JsonValueKind.Object)
        {
            var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var property in item.EnumerateObject()) { if (!keys.Add(property.Name)) throw new JsonException("DISPATCH_DUPLICATE_PROPERTY"); CheckDuplicateProperties(property.Value); }
        }
        else if (item.ValueKind == JsonValueKind.Array) foreach (var child in item.EnumerateArray()) CheckDuplicateProperties(child);
    }
    private static bool TryEnvelope(string body, out string kind, out Dictionary<string, string> fields)
    {
        fields = new(StringComparer.Ordinal); kind = "";
        if (body.Length > 100_000) return false;
        var content = body.Trim();
        if (content.StartsWith("[AEVRYND-BRIDGE]", StringComparison.Ordinal))
        {
            if (!content.EndsWith("[/AEVRYND-BRIDGE]", StringComparison.Ordinal)) return false;
            content = content[16..^17].Trim(); kind = "BRIDGE";
        }
        foreach (var wrapper in new[] { "MAIN_COMMAND", "NODE_ACK", "NODE_REPORT" })
            if (content.StartsWith("[" + wrapper + "]", StringComparison.Ordinal))
            {
                var closing = "[/" + wrapper + "]";
                if (!content.EndsWith(closing, StringComparison.Ordinal)) return false;
                content = content[(wrapper.Length + 2)..^closing.Length].Trim(); kind = wrapper; break;
            }
        if (kind.Length == 0 || Regex.IsMatch(content, @"(?m)^\[/?(?:MAIN_COMMAND|NODE_ACK|NODE_REPORT|AEVRYND-BRIDGE)\]")) return false;
        var protectedFields = new HashSet<string>(new[] { "COMMAND_ID", "NODE", "TARGET", "STATUS", "COMMENT_ID", "WORK_KEY", "GENERATION", "SUPERSEDES_COMMAND_ID", "DEPENDS_ON_COMMAND_ID", "DEPENDS_ON", "TITLE", "TASK", "ACK_DEADLINE_SECONDS", "LEASE_SECONDS", "ARCHIVE_THROUGH_COMMENT_ID" }, StringComparer.OrdinalIgnoreCase);
        foreach (var line in content.Split('\n'))
        {
            var match = Regex.Match(line.TrimEnd('\r'), @"^([A-Za-z_]+):\s*(.*)$");
            if (!match.Success || !protectedFields.Contains(match.Groups[1].Value)) continue;
            var key = match.Groups[1].Value;
            if (key != key.ToUpperInvariant() || !fields.TryAdd(key, match.Groups[2].Value.Trim())) return false;
        }
        return fields.ContainsKey("COMMAND_ID");
    }
    private static bool TryArchivedCommandEnvelope(string body, out string node, out string commandId)
    {
        node = ""; commandId = "";
        var content = body.Trim();
        const string outerOpen = "[AEVRYND-ARCHIVED-BRIDGE]";
        const string outerClose = "[/AEVRYND-ARCHIVED-BRIDGE]";
        const string innerOpen = "[ARCHIVED_COMMAND]";
        const string innerClose = "[/ARCHIVED_COMMAND]";
        const string legacyPrefix = "封存說明：此命令在狀態校正 cutoff 前沒有任何節點回覆，全文保留但不得再執行。";
        if (content.StartsWith(outerOpen, StringComparison.Ordinal) && content.EndsWith(outerClose, StringComparison.Ordinal))
            content = content[outerOpen.Length..^outerClose.Length].Trim();
        else if (content.StartsWith(legacyPrefix, StringComparison.Ordinal))
            content = content[legacyPrefix.Length..].Trim();
        else return false;
        if (!content.StartsWith(innerOpen, StringComparison.Ordinal) || !content.EndsWith(innerClose, StringComparison.Ordinal)) return false;
        content = content[innerOpen.Length..^innerClose.Length].Trim();
        if (Regex.IsMatch(content, @"(?m)^\[/?(?:AEVRYND-ARCHIVED-BRIDGE|ARCHIVED_COMMAND)\]")) return false;
        var fields = new Dictionary<string, string>(StringComparer.Ordinal);
        var protectedFields = new HashSet<string>(new[] { "COMMAND_ID", "TARGET" }, StringComparer.OrdinalIgnoreCase);
        foreach (var line in content.Split('\n'))
        {
            var match = Regex.Match(line.TrimEnd('\r'), @"^([A-Za-z_]+):\s*(.*)$");
            if (!match.Success || !protectedFields.Contains(match.Groups[1].Value)) continue;
            var key = match.Groups[1].Value;
            if (key != key.ToUpperInvariant() || !fields.TryAdd(key, match.Groups[2].Value.Trim())) return false;
        }
        if (!Id(fields.GetValueOrDefault("COMMAND_ID")) || !Node(fields.GetValueOrDefault("TARGET"), out node)) return false;
        commandId = fields["COMMAND_ID"];
        return true;
    }
    private static bool IsArchivedLateEvent(Event item, Dictionary<string, string> fields, IReadOnlyList<ArchivedCommand> archivedCommands,
        IReadOnlyList<ArchiveDirective> archiveDirectives)
    {
        if (!Id(fields.GetValueOrDefault("COMMAND_ID")) || !Node(fields.GetValueOrDefault("NODE"), out var node)) return false;
        var status = fields.GetValueOrDefault("STATUS");
        var validReplyShape = item.Kind switch
        {
            "NODE_ACK" => status is null or "ACK" or "ACCEPTED" or "QUEUED_DEPENDENCY",
            "NODE_REPORT" => status is not null,
            "BRIDGE" => status is not null,
            _ => false
        };
        if (!validReplyShape) return false;
        var latestTaichung = archiveDirectives.Where(candidate => candidate.NodeId == "taichung")
            .OrderBy(candidate => candidate.CreatedAt).ThenBy(candidate => candidate.CommentId).LastOrDefault();
        var latestTaoyuan = archiveDirectives.Where(candidate => candidate.NodeId == "taoyuan")
            .OrderBy(candidate => candidate.CreatedAt).ThenBy(candidate => candidate.CommentId).LastOrDefault();
        if (latestTaichung is null || latestTaoyuan is null) return false;
        var directive = archiveDirectives.Where(candidate => candidate.NodeId == node)
            .OrderBy(candidate => candidate.CreatedAt).ThenBy(candidate => candidate.CommentId).LastOrDefault();
        if (directive is null || item.Id <= directive.Cutoff) return false;
        var matchingCommands = archivedCommands.Count(command => command.CommentId <= directive.Cutoff && command.NodeId == node && command.CommandId == fields["COMMAND_ID"]);
        return matchingCommands == 1;
    }
    private static bool Number(Dictionary<string, string> fields, string key, int fallback, int minimum, int maximum, out int value)
    {
        value = fallback; return !fields.TryGetValue(key, out var raw) || int.TryParse(raw, NumberStyles.None, CultureInfo.InvariantCulture, out value) && value >= minimum && value <= maximum;
    }
    private static bool OptionalPositiveLongBefore(Dictionary<string, string> fields, string key, long upperExclusive, out long? value)
    {
        value = null;
        if (!fields.TryGetValue(key, out var raw)) return true;
        if (!long.TryParse(raw, NumberStyles.None, CultureInfo.InvariantCulture, out var parsed) || parsed <= 0 || parsed >= upperExclusive) return false;
        value = parsed;
        return true;
    }
    private static bool Node(string? value, out string node) { node = value switch { "LOCAL" => "local", "TAICHUNG" => "taichung", "TAOYUAN" => "taoyuan", _ => "" }; return node.Length > 0; }
    private static bool Id(string? value) => value is not null && Identifier.IsMatch(value);
    private static bool Safe(string? value, int limit) => !string.IsNullOrWhiteSpace(value) && value.Length <= limit && !PrivateText.IsMatch(value);
    private static bool TryTime(string? value, out DateTimeOffset result) => DateTimeOffset.TryParseExact(value, ["yyyy-MM-dd'T'HH:mm:ss'Z'", "yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK"], CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out result);
    private static string SafeTitle(string value, string node)
    {
        var first = value.Split(['。', '；', '\n'])[0].Trim();
        if (Safe(first, 600) && Regex.IsMatch(first, "[\u3400-\u9fff]")) return first.Length > 80 ? first[..76] + "…" : first;
        return (node == "taichung" ? "台中" : node == "taoyuan" ? "桃園" : "本機") + "派遣工作";
    }
}
