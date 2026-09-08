namespace AevryndWeb.Models;

public sealed record StatisticsHeartbeatRequest(Guid SessionId, Guid? ViewId);

public sealed record SiteStatisticsResponse(long Online, long TotalViews);
