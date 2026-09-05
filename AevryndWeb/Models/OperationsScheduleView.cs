namespace AevryndWeb.Models;

public sealed record OperationsScheduleView(bool SourceAvailable, bool Stale, DateTimeOffset? ObservedAt,
    IReadOnlyList<OperationsScheduledTaskView> Tasks);

public sealed record OperationsScheduledTaskView(string Id, string NodeId, string Title, string Description,
    string State, string Reason, IReadOnlyList<string> DependsOn, DateTimeOffset AssignedAt,
    DateTimeOffset UpdatedAt, string Evidence);
