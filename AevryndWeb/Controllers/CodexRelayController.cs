using AevryndWeb.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AevryndWeb.Controllers;

[ApiController]
[Route("api/codex-relay")]
public sealed class CodexRelayController(ICodexEventRelay relay) : ControllerBase
{
    [HttpPost("commands")]
    [Authorize(Policy = PortalIdentity.AdminPolicy)]
    [RequestSizeLimit(16_384)]
    public IActionResult Submit([FromBody] CodexRelayCommandRequest request)
    {
        var result = relay.Submit(request, DateTimeOffset.UtcNow);
        return result switch
        {
            CodexRelayResult.Accepted => Accepted(new { request.CommandId }),
            CodexRelayResult.Duplicate => Conflict(),
            CodexRelayResult.Invalid => BadRequest(),
            _ => StatusCode(StatusCodes.Status503ServiceUnavailable)
        };
    }

    [HttpPost("publisher-commands")]
    [AllowAnonymous]
    [IgnoreAntiforgeryToken]
    [RequestSizeLimit(16_384)]
    public async Task<IActionResult> SubmitPublisher(CancellationToken cancellationToken)
    {
        if (Request.ContentLength is > 16_384 || Request.ContentType is null ||
            !Request.ContentType.StartsWith("application/json", StringComparison.OrdinalIgnoreCase)) return BadRequest();
        using var buffer = new MemoryStream();
        var chunk = new byte[2048];
        while (true)
        {
            var read = await Request.Body.ReadAsync(chunk, cancellationToken); if (read == 0) break;
            if (buffer.Length + read > 16_384) return BadRequest();
            await buffer.WriteAsync(chunk.AsMemory(0, read), cancellationToken);
        }
        if (buffer.Length == 0) return BadRequest();
        var body = buffer.ToArray();
        var auth = relay.AuthenticatePublisher(Request.Headers["X-Aevrynd-Timestamp"].ToString(),
            Request.Headers["X-Aevrynd-Nonce"].ToString(), Request.Headers["X-Aevrynd-Signature"].ToString(), body, DateTimeOffset.UtcNow);
        if (auth != CodexRelayResult.Accepted) return auth switch
        {
            CodexRelayResult.Invalid => BadRequest(), CodexRelayResult.Replay => Conflict(),
            CodexRelayResult.Unavailable => StatusCode(StatusCodes.Status503ServiceUnavailable), _ => Unauthorized()
        };
        CodexRelayCommandRequest? request;
        try
        {
            request = System.Text.Json.JsonSerializer.Deserialize<CodexRelayCommandRequest>(body, new System.Text.Json.JsonSerializerOptions
            { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow });
        }
        catch (System.Text.Json.JsonException) { return BadRequest(); }
        if (request is null) return BadRequest();
        var result = relay.Submit(request, DateTimeOffset.UtcNow);
        return result switch
        {
            CodexRelayResult.Accepted => Accepted(new { request.CommandId }), CodexRelayResult.Duplicate => Conflict(),
            CodexRelayResult.Invalid => BadRequest(), _ => StatusCode(StatusCodes.Status503ServiceUnavailable)
        };
    }

    [HttpGet("history")]
    [Authorize(Policy = PortalIdentity.AdminPolicy)]
    public IActionResult History([FromQuery] int maximum = 100) => Ok(relay.ReadHistory(Math.Clamp(maximum, 1, 200)));

    [HttpGet("connect")]
    [AllowAnonymous]
    public async Task Connect(CancellationToken cancellationToken)
    {
        if (!HttpContext.WebSockets.IsWebSocketRequest) { Response.StatusCode = StatusCodes.Status400BadRequest; return; }
        var node = Request.Headers["X-Aevrynd-Node"].ToString();
        var result = relay.Authenticate(node, Request.Headers["X-Aevrynd-Timestamp"].ToString(),
            Request.Headers["X-Aevrynd-Nonce"].ToString(), Request.Headers["X-Aevrynd-Signature"].ToString(), DateTimeOffset.UtcNow);
        if (result != CodexRelayResult.Accepted)
        {
            Response.StatusCode = result switch { CodexRelayResult.Replay => StatusCodes.Status409Conflict, CodexRelayResult.Invalid => StatusCodes.Status400BadRequest, CodexRelayResult.Unavailable => StatusCodes.Status503ServiceUnavailable, _ => StatusCodes.Status401Unauthorized };
            return;
        }
        using var socket = await HttpContext.WebSockets.AcceptWebSocketAsync();
        await relay.RunConnectionAsync(node, socket, cancellationToken);
    }
}
