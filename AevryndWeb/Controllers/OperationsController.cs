using AevryndWeb.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[Authorize(Policy = PortalIdentity.OperationsPolicy)]
[Route("Operations")]
public sealed class OperationsController(IOperationsSnapshotProvider snapshots, NodeHardwareCatalog hardware, OperationsScheduleProvider schedule) : Controller
{
    private AevryndWeb.Models.OperationsViewModel Read()
    {
        var now = DateTimeOffset.UtcNow;
        var model = OperationsScheduleProvider.ReconcileWork(snapshots.Read(now));
        return model with { Hardware = hardware.Read(), Schedule = schedule.Read(now, model) };
    }
    [HttpGet("")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Index() => View(Read());

    [HttpGet("snapshot")]
    [Produces("application/json")]
    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Snapshot() => Ok(Read());
}
