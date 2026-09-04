using AevryndWeb.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[Authorize(Policy = PortalIdentity.OperationsPolicy)]
[Route("Operations")]
public sealed class OperationsController(IOperationsSnapshotProvider snapshots) : Controller
{
    [HttpGet("")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Index() => View(snapshots.Read(DateTimeOffset.UtcNow));

    [HttpGet("snapshot")]
    [Produces("application/json")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Snapshot() => Ok(snapshots.Read(DateTimeOffset.UtcNow));
}
