using AevryndWeb.Security;

namespace AevryndWeb.Models;

public sealed record RemoteConsoleViewModel(bool LocallyEnabled, bool GrantActive, DateTimeOffset? EnabledUntilUtc, DateTimeOffset? GrantExpiresAt,
    IReadOnlyList<string> Capabilities, RemoteDesktopAvailability DesktopAvailability);
