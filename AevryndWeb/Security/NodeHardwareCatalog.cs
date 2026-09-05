using System.Text.Json;
using System.Text.Json.Serialization;
using AevryndWeb.Models;

namespace AevryndWeb.Security;

public sealed class NodeHardwareCatalog(IWebHostEnvironment environment)
{
    private const int SchemaVersion = 1;
    private static readonly HashSet<string> KnownIds = new(StringComparer.Ordinal) { "local", "taichung", "taoyuan" };
    private string Path => System.IO.Path.Combine(environment.ContentRootPath, "Data", "node-hardware.json");

    public IReadOnlyList<NodeHardwareView> Read()
    {
        try
        {
            if (!File.Exists(Path)) return [];
            var document = JsonSerializer.Deserialize<NodeHardwareDocument>(File.ReadAllText(Path), new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow
            });
            if (document is null || document.SchemaVersion != SchemaVersion || document.Nodes is null || document.Nodes.Count > 3 ||
                document.Nodes.Any(node => !KnownIds.Contains(node.Id)) || document.Nodes.Select(node => node.Id).Distinct(StringComparer.Ordinal).Count() != document.Nodes.Count)
                return [];
            return document.Nodes.Select(node => new NodeHardwareView(node.Id, node.Name, node.Model, node.Reasoning, node.ModelSource,
                node.Role, ResolveHardwareStatus(node.HardwareStatus, node.Cpu, node.Ram, node.Gpu, node.Motherboard, node.Os, node.Storage), node.SampledAt, node.Cpu, node.Ram, node.Gpu, node.Motherboard, node.Os,
                node.Storage?.Take(16).ToArray() ?? [], node.Source)).ToArray();
        }
        catch (Exception exception) when (exception is IOException or JsonException or UnauthorizedAccessException)
        { return []; }
    }

    public static string ResolveHardwareStatus(string declaredStatus, string? cpu, string? ram, string? gpu, string? motherboard, string? os, IReadOnlyCollection<string>? storage)
    {
        var fields = new[] { cpu, ram, gpu, motherboard, os };
        var hasAny = fields.Any(value => !string.IsNullOrWhiteSpace(value)) || storage?.Any(value => !string.IsNullOrWhiteSpace(value)) == true;
        var complete = fields.All(value => !string.IsNullOrWhiteSpace(value)) && storage?.Any(value => !string.IsNullOrWhiteSpace(value)) == true;
        if (declaredStatus is not ("verified" or "partial")) return "pending";
        if (declaredStatus == "verified" && complete) return "verified";
        return hasAny ? "partial" : "pending";
    }

    private sealed class NodeHardwareDocument
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("nodes")] public List<NodeHardwareEntry>? Nodes { get; set; }
    }

    private sealed class NodeHardwareEntry
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Model { get; set; } = string.Empty;
        public string Reasoning { get; set; } = string.Empty;
        public string ModelSource { get; set; } = string.Empty;
        public string Role { get; set; } = string.Empty;
        public string HardwareStatus { get; set; } = "pending";
        public DateTimeOffset? SampledAt { get; set; }
        public string? Cpu { get; set; }
        public string? Ram { get; set; }
        public string? Gpu { get; set; }
        public string? Motherboard { get; set; }
        public string? Os { get; set; }
        public List<string>? Storage { get; set; }
        public string Source { get; set; } = string.Empty;
    }
}
