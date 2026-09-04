namespace AevryndWeb.Security;

public interface IRemoteControlLeaseRegistry
{
    bool TryAcquire(string sessionId);
    bool IsActive(string sessionId);
    void Release(string sessionId);
    void ReleaseAll();
}

public sealed class RemoteControlLeaseRegistry : IRemoteControlLeaseRegistry
{
    private readonly object sync = new();
    private string? activeSessionId;
    public bool TryAcquire(string sessionId)
    {
        lock (sync)
        {
            if (sessionId.Length == 0 || activeSessionId is not null) return false;
            activeSessionId = sessionId; return true;
        }
    }
    public bool IsActive(string sessionId) { lock (sync) return StringComparer.Ordinal.Equals(activeSessionId, sessionId); }
    public void Release(string sessionId) { lock (sync) if (StringComparer.Ordinal.Equals(activeSessionId, sessionId)) activeSessionId = null; }
    public void ReleaseAll() { lock (sync) activeSessionId = null; }
}
