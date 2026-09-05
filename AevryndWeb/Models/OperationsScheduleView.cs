namespace AevryndWeb.Models;

public sealed record OperationsScheduleView(bool SourceAvailable, bool Stale, DateTimeOffset? ObservedAt,
    IReadOnlyList<OperationsScheduledTaskView> Tasks)
{
    public IReadOnlyList<OperationsScheduledTaskView> Catalog { get; init; } = [];
    public DateTimeOffset? VerifiedAt { get; init; }
    public string Diagnostic { get; init; } = "";

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
