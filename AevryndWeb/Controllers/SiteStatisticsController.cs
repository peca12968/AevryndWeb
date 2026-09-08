using AevryndWeb.Data;
using AevryndWeb.Models;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[ApiController]
[Route("api/stats")]
public sealed class SiteStatisticsController(ISiteStatisticsStore statistics) : ControllerBase
{
    [HttpGet]
    [ResponseCache(NoStore = true, Location = ResponseCacheLocation.None)]
    public async Task<ActionResult<SiteStatisticsResponse>> Get(CancellationToken cancellationToken) =>
        Ok(await statistics.ReadAsync(cancellationToken));

    [HttpPost]
    [ResponseCache(NoStore = true, Location = ResponseCacheLocation.None)]
    public async Task<ActionResult<SiteStatisticsResponse>> Heartbeat(
        [FromBody] StatisticsHeartbeatRequest request,
        CancellationToken cancellationToken)
    {
        if (request.SessionId == Guid.Empty || request.ViewId == Guid.Empty)
        {
            return BadRequest(new { error = "Invalid analytics identifier." });
        }

        return Ok(await statistics.HeartbeatAsync(
            request.SessionId,
            request.ViewId,
            cancellationToken));
    }
}
