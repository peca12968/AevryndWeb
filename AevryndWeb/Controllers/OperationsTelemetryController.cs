using AevryndWeb.Security;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[ApiController]
[Route("api/operations/telemetry")]
public sealed class OperationsTelemetryController(IRemoteOperationsTelemetry telemetry) : ControllerBase
{
    [HttpPost]
    [IgnoreAntiforgeryToken]
    [RequestSizeLimit(4096)]
    public async Task<IActionResult> Post(CancellationToken cancellationToken)
    {
        if (Request.ContentLength is > 4096 || Request.ContentType is null ||
            !Request.ContentType.StartsWith("application/json", StringComparison.OrdinalIgnoreCase)) return BadRequest();
        var body = await ReadBody(cancellationToken);
        if (body is null) return BadRequest();
        var result = telemetry.Receive(
            Request.Headers["X-Aevrynd-Node"].ToString(),
            Request.Headers["X-Aevrynd-Timestamp"].ToString(),
            Request.Headers["X-Aevrynd-Nonce"].ToString(),
            Request.Headers["X-Aevrynd-Signature"].ToString(),
            HttpContext.Connection.RemoteIpAddress,
            body,
            DateTimeOffset.UtcNow);
        return result.Status switch
        {
            RemoteTelemetryStatus.Accepted => Accepted(),
            RemoteTelemetryStatus.Invalid => BadRequest(),
            RemoteTelemetryStatus.Replay => Conflict(),
            RemoteTelemetryStatus.Unavailable => StatusCode(StatusCodes.Status503ServiceUnavailable),
            _ => Unauthorized()
        };
    }

    private async Task<byte[]?> ReadBody(CancellationToken cancellationToken)
    {
        using var buffer = new MemoryStream();
        var chunk = new byte[1024];
        while (true)
        {
            var read = await Request.Body.ReadAsync(chunk, cancellationToken);
            if (read == 0) return buffer.Length == 0 ? null : buffer.ToArray();
            if (buffer.Length + read > 4096) return null;
            await buffer.WriteAsync(chunk.AsMemory(0, read), cancellationToken);
        }
    }
}
