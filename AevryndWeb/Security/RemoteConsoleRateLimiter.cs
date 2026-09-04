using System.Collections.Concurrent;

namespace AevryndWeb.Security;

public interface IRemoteConsoleRateLimiter
{
    bool AllowFrame(string key, DateTimeOffset now, out TimeSpan retryAfter);
    bool AllowText(string key, DateTimeOffset now, out TimeSpan retryAfter);
    bool AllowInteraction(string key, DateTimeOffset now, out TimeSpan retryAfter);
    bool AllowShell(string key, DateTimeOffset now, out TimeSpan retryAfter);
}

public sealed class RemoteConsoleRateLimiter : IRemoteConsoleRateLimiter
{
    private static readonly TimeSpan FrameInterval = TimeSpan.FromMilliseconds(1500);
    private static readonly TimeSpan TextWindow = TimeSpan.FromMinutes(1);
    private readonly ConcurrentDictionary<string, DateTimeOffset> nextFrames = new();
    private readonly ConcurrentDictionary<string, Window> textWindows = new();
    private readonly ConcurrentDictionary<string, Window> interactionWindows = new();
    private readonly ConcurrentDictionary<string, Window> shellWindows = new();

    public bool AllowFrame(string key, DateTimeOffset now, out TimeSpan retryAfter)
    {
        key = "global";
        while (true)
        {
            if (nextFrames.TryGetValue(key, out var next) && next > now)
            {
                retryAfter = next - now;
                return false;
            }

            var replacement = now.Add(FrameInterval);
            if (nextFrames.TryAdd(key, replacement) || nextFrames.TryUpdate(key, replacement, next))
            {
                retryAfter = TimeSpan.Zero;
                return true;
            }
        }
    }

    public bool AllowText(string key, DateTimeOffset now, out TimeSpan retryAfter)
    {
        var current = textWindows.AddOrUpdate(
            key,
            _ => new Window(now.Add(TextWindow), 1),
            (_, old) => old.Until <= now ? new Window(now.Add(TextWindow), 1) : old with { Count = old.Count + 1 });
        retryAfter = current.Until - now;
        return current.Count <= 30;
    }

    public bool AllowInteraction(string key, DateTimeOffset now, out TimeSpan retryAfter)
    {
        var current = interactionWindows.AddOrUpdate(key, _ => new Window(now.Add(TextWindow), 1),
            (_, old) => old.Until <= now ? new Window(now.Add(TextWindow), 1) : old with { Count = old.Count + 1 });
        retryAfter = current.Until - now;
        return current.Count <= 120;
    }

    public bool AllowShell(string key, DateTimeOffset now, out TimeSpan retryAfter)
    {
        var current = shellWindows.AddOrUpdate(key, _ => new Window(now.Add(TextWindow), 1),
            (_, old) => old.Until <= now ? new Window(now.Add(TextWindow), 1) : old with { Count = old.Count + 1 });
        retryAfter = current.Until - now;
        return current.Count <= 10;
    }

    private sealed record Window(DateTimeOffset Until, int Count);
}
