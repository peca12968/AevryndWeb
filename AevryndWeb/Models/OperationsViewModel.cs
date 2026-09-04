namespace AevryndWeb.Models;

public sealed record OperationsViewModel(
    IReadOnlyList<OperationsNodeView> Nodes,
    IReadOnlyList<OperationsWorkView> ActiveWork,
    IReadOnlyList<OperationsWorkView> History,
    DateTimeOffset? SnapshotAt,
    bool SourceAvailable,
    string SourceStatus);

public sealed record OperationsNodeView(
    string Id,
    string Name,
    double? CpuPercent,
    double? RamPercent,
    double? GpuPercent,
    DateTimeOffset? SampledAt,
    bool Stale,
    string Availability,
    string Diagnostic);
public sealed record OperationsWorkView(string Name, string Type, string Host, DateTimeOffset StartedAt, DateTimeOffset? UpdatedAt, DateTimeOffset? EndedAt, string Status, string? EvidenceSummary, bool Stale);
