namespace AevryndWeb.Models;

public sealed record OperationsScheduleView(bool SourceAvailable, bool Stale, DateTimeOffset? ObservedAt,
    IReadOnlyList<OperationsScheduledTaskView> Tasks)
{
    public IReadOnlyList<OperationsScheduledTaskView> Catalog { get; init; } = [];
    public DateTimeOffset? VerifiedAt { get; init; }
    public string Diagnostic { get; init; } = "";
    public bool LocalScheduleStale { get; init; }
    public string DisplayDiagnostic => Diagnostic switch
    {
        "" => "",
        "遠端派工來源已完成核對。" or "遠端派工來源有部分事件待核對；目前僅顯示已驗證資料。" or
        "遠端派工來源尚未完成近期核對；保留已驗證資料，不推測工作狀態。" or
        "遠端派工來源目前無法核對；保留既有資料，不推測工作狀態。" => Diagnostic,
        _ => "來源狀態待核對；目前僅顯示可驗證資料。"
    };

    public string WorkTitle(OperationsWorkView work) => Catalog.OrderByDescending(task => task.AssignedAt).FirstOrDefault(task =>
        task.Id == work.Name && NodeHost(task.NodeId) == work.Host && work.StartedAt >= task.AssignedAt)?.Title ?? work.Name;

    public static string NodeHost(string nodeId) => nodeId switch { "local" => "本機", "taichung" => "台中", "taoyuan" => "桃園", _ => "" };
}

public sealed record OperationsScheduledTaskView(string Id, string NodeId, string Title, string Description,
    string State, string Reason, IReadOnlyList<string> DependsOn, DateTimeOffset AssignedAt,
    DateTimeOffset UpdatedAt, string Evidence)
{
    public string? InstanceId { get; init; }
}
