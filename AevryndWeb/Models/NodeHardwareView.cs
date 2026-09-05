namespace AevryndWeb.Models;

public sealed record NodeHardwareView(
    string Id,
    string Name,
    string Model,
    string Reasoning,
    string ModelSource,
    string Role,
    string HardwareStatus,
    DateTimeOffset? SampledAt,
    string? Cpu,
    string? Ram,
    string? Gpu,
    string? Motherboard,
    string? Os,
    IReadOnlyList<string> Storage,
    string Source);
