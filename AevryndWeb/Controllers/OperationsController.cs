using AevryndWeb.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[Authorize(Policy = PortalIdentity.PortalOwnerPolicy)]
[Route("Operations")]
public sealed class OperationsController(IOperationsSnapshotProvider snapshots) : Controller
{
    [HttpGet("")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Index() => View(snapshots.Read(DateTimeOffset.UtcNow));
}
