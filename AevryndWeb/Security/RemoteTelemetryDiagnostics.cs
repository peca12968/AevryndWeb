using System.Collections.Concurrent;

namespace AevryndWeb.Security;

public sealed class RemoteTelemetryDiagnostics
{
    private readonly ConcurrentDictionary<string, (DateTimeOffset At, string Code)> observations = new(StringComparer.Ordinal);
    public void Record(string node, DateTimeOffset at, string code)
    {
        if (node is "taichung" or "taoyuan") observations[node] = (at, code);
    }
    public string Describe(string node, DateTimeOffset now)
    {
        if (!observations.TryGetValue(node, out var observation) || now - observation.At > TimeSpan.FromHours(1)) return "";
        return $" 最近接收結果：{observation.Code}（{PortalTime.Format(observation.At)}）。";
    }
}
