using System.Collections.Concurrent;
using System.Globalization;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace AevryndWeb.Security;

public enum CodexRelayResult { Accepted, Invalid, Unauthorized, Replay, Duplicate, Conflict, Unavailable }
public enum CodexRelayCommandStatus { Queued, Running, Completed, Failed }

public sealed class CodexRelayCommandRequest
{
    [JsonRequired, JsonPropertyName("commandId")] public string CommandId { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("nodeId")] public string NodeId { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("ownedFiles")] public List<string> OwnedFiles { get; set; } = [];
    [JsonRequired, JsonPropertyName("task")] public string Task { get; set; } = string.Empty;
}

public sealed class CodexRelayAck
{
    [JsonRequired, JsonPropertyName("version")] public int Version { get; set; }
    [JsonRequired, JsonPropertyName("type")] public string Type { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("commandId")] public string CommandId { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("nodeId")] public string NodeId { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("state")] public string State { get; set; } = string.Empty;
    [JsonRequired, JsonPropertyName("occurredAtUtc")] public DateTimeOffset OccurredAtUtc { get; set; }
    [JsonPropertyName("exitCode")] public int? ExitCode { get; set; }
    [JsonPropertyName("summary")] public string? Summary { get; set; }
}

public sealed class CodexRelayCommandState
{
    public string CommandId { get; set; } = string.Empty;
    public string NodeId { get; set; } = string.Empty;
    public List<string> OwnedFiles { get; set; } = [];
    public string Task { get; set; } = string.Empty;
    public CodexRelayCommandStatus Status { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }
    public int? ExitCode { get; set; }
    public string? Summary { get; set; }
}

public interface ICodexEventRelayStore
{
    CodexRelayResult TryCreate(CodexRelayCommandState command);
    IReadOnlyList<CodexRelayCommandState> ReadPending(string nodeId);
    IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum);
    CodexRelayResult TryAcknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now);
}

public interface ICodexEventRelayReplayStore
{
    CodexRelayResult TryConsume(string scope, string nonce, DateTimeOffset now);
}

public interface ICodexEventRelay
{
    CodexRelayResult Authenticate(string nodeId, string timestamp, string nonce, string signature, DateTimeOffset now);
    CodexRelayResult AuthenticatePublisher(string timestamp, string nonce, string signature, ReadOnlySpan<byte> body, DateTimeOffset now);
    CodexRelayResult Submit(CodexRelayCommandRequest request, DateTimeOffset now);
    CodexRelayResult Acknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now);
    IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum);
    Task RunConnectionAsync(string nodeId, WebSocket socket, CancellationToken cancellationToken);
}

public sealed class CodexEventRelay(
    IConfiguration configuration,
    ICodexEventRelayStore store,
    ICodexEventRelayReplayStore replayStore) : ICodexEventRelay
{
    public const string EndpointPath = "/api/codex-relay/connect";
    public const string PublishEndpointPath = "/api/codex-relay/publisher-commands";
    private const int MaximumMessageBytes = 16_384;
    private static readonly HashSet<string> AllowedNodes = new(StringComparer.Ordinal) { "taichung", "taoyuan" };
    private static readonly Regex CommandIdShape = new("^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$", RegexOptions.CultureInvariant);
    private static readonly Regex NonceShape = new("^[A-Za-z0-9_-]{22,64}$", RegexOptions.CultureInvariant);
    private static readonly Regex RelativePathShape = new("^[A-Za-z0-9._/*?\\[\\]-]+$", RegexOptions.CultureInvariant);
    private readonly ConcurrentDictionary<string, Connection> _connections = new(StringComparer.Ordinal);

    public CodexRelayResult Authenticate(string nodeId, string timestamp, string nonce, string signature, DateTimeOffset now)
    {
        if (!AllowedNodes.Contains(nodeId) || !NonceShape.IsMatch(nonce) ||
            !long.TryParse(timestamp, NumberStyles.None, CultureInfo.InvariantCulture, out var seconds)) return CodexRelayResult.Invalid;
        DateTimeOffset signedAt;
        try { signedAt = DateTimeOffset.FromUnixTimeSeconds(seconds); }
        catch (ArgumentOutOfRangeException) { return CodexRelayResult.Invalid; }
        if (signedAt > now.AddSeconds(30) || now - signedAt > TimeSpan.FromMinutes(2)) return CodexRelayResult.Unauthorized;
        var secretText = configuration[$"Operations:CodexRelay:Nodes:{nodeId}:Secret"] ??
            configuration[$"Operations:RemoteTelemetry:Nodes:{nodeId}:Secret"];
        if (!TrySecret(secretText, out var secret)) return CodexRelayResult.Unauthorized;
        if (!TrySignature(signature, out var supplied)) { CryptographicOperations.ZeroMemory(secret); return CodexRelayResult.Unauthorized; }
        try
        {
            var signed = Encoding.UTF8.GetBytes($"GET\n{EndpointPath}\n{nodeId}\n{timestamp}\n{nonce}\n");
            var expected = HMACSHA256.HashData(secret, signed);
            if (!CryptographicOperations.FixedTimeEquals(expected, supplied)) return CodexRelayResult.Unauthorized;
        }
        finally { CryptographicOperations.ZeroMemory(secret); CryptographicOperations.ZeroMemory(supplied); }
        return replayStore.TryConsume("node-" + nodeId, nonce, now);
    }

    public CodexRelayResult AuthenticatePublisher(string timestamp, string nonce, string signature, ReadOnlySpan<byte> body, DateTimeOffset now)
    {
        if (body is { Length: <= 0 or > MaximumMessageBytes } || !NonceShape.IsMatch(nonce) ||
            !long.TryParse(timestamp, NumberStyles.None, CultureInfo.InvariantCulture, out var seconds)) return CodexRelayResult.Invalid;
        DateTimeOffset signedAt;
        try { signedAt = DateTimeOffset.FromUnixTimeSeconds(seconds); }
        catch (ArgumentOutOfRangeException) { return CodexRelayResult.Invalid; }
        if (signedAt > now.AddSeconds(30) || now - signedAt > TimeSpan.FromMinutes(2)) return CodexRelayResult.Unauthorized;
        if (!TrySecret(configuration["Operations:CodexRelay:PublisherSecret"], out var secret)) return CodexRelayResult.Unauthorized;
        if (!TrySignature(signature, out var supplied)) { CryptographicOperations.ZeroMemory(secret); return CodexRelayResult.Unauthorized; }
        try
        {
            var prefix = Encoding.UTF8.GetBytes($"POST\n{PublishEndpointPath}\n{timestamp}\n{nonce}\n");
            var signed = new byte[prefix.Length + body.Length]; prefix.CopyTo(signed, 0); body.CopyTo(signed.AsSpan(prefix.Length));
            if (!CryptographicOperations.FixedTimeEquals(HMACSHA256.HashData(secret, signed), supplied)) return CodexRelayResult.Unauthorized;
        }
        finally { CryptographicOperations.ZeroMemory(secret); CryptographicOperations.ZeroMemory(supplied); }
        return replayStore.TryConsume("publisher", nonce, now);
    }

    public CodexRelayResult Submit(CodexRelayCommandRequest request, DateTimeOffset now)
    {
        if (!ValidRequest(request)) return CodexRelayResult.Invalid;
        var command = new CodexRelayCommandState
        {
            CommandId = request.CommandId,
            NodeId = request.NodeId,
            OwnedFiles = request.OwnedFiles.ToList(),
            Task = request.Task,
            Status = CodexRelayCommandStatus.Queued,
            CreatedAt = now,
            UpdatedAt = now
        };
        var result = store.TryCreate(command);
        if (result == CodexRelayResult.Accepted && _connections.TryGetValue(request.NodeId, out var connection) && connection.Signal.CurrentCount == 0) connection.Signal.Release();
        return result;
    }

    public CodexRelayResult Acknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now)
    {
        if (!AllowedNodes.Contains(nodeId) || ack.Version != 1 || ack.Type != "ack" || ack.NodeId != nodeId ||
            !CommandIdShape.IsMatch(ack.CommandId) || ack.OccurredAtUtc == default || ack.OccurredAtUtc > now.AddSeconds(30) || now - ack.OccurredAtUtc > TimeSpan.FromDays(7) ||
            ack.OccurredAtUtc.Offset != TimeSpan.Zero || ack.ExitCode is < 0 or > 65_535 ||
            string.IsNullOrWhiteSpace(ack.Summary) || ack.Summary.Length > 240 || ack.Summary.Any(char.IsControl) ||
            !Enum.TryParse<CodexRelayCommandStatus>(ack.State, true, out var status) || status == CodexRelayCommandStatus.Queued ||
            status == CodexRelayCommandStatus.Running && ack.ExitCode is not null ||
            status == CodexRelayCommandStatus.Completed && ack.ExitCode != 0 ||
            status == CodexRelayCommandStatus.Failed && ack.ExitCode is null or 0) return CodexRelayResult.Invalid;
        return store.TryAcknowledge(nodeId, ack, now);
    }

    public IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum) => store.ReadHistory(Math.Clamp(maximum, 1, 200));

    public async Task RunConnectionAsync(string nodeId, WebSocket socket, CancellationToken cancellationToken)
    {
        var connection = new Connection(Guid.NewGuid().ToString("N"));
        if (!_connections.TryAdd(nodeId, connection))
        {
            try { await CloseSocket(socket, WebSocketCloseStatus.PolicyViolation, "node already connected", cancellationToken); }
            catch (RelayTransportClosedException) { }
            return;
        }
        try
        {
            using var stopped = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            var sender = SendLoop(nodeId, connection, socket, stopped.Token);
            var receiver = ReceiveLoop(nodeId, connection, socket, stopped.Token);
            await Task.WhenAny(sender, receiver); stopped.Cancel();
            try { await Task.WhenAll(sender, receiver); }
            catch (OperationCanceledException) when (stopped.IsCancellationRequested) { }
        }
        catch (RelayTransportClosedException) { }
        finally { _connections.TryRemove(new KeyValuePair<string, Connection>(nodeId, connection)); }
    }

    private async Task SendLoop(string nodeId, Connection connection, WebSocket socket, CancellationToken cancellationToken)
    {
        while (socket.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
        {
            await SendPending(nodeId, connection, socket, cancellationToken);
            await connection.Signal.WaitAsync(cancellationToken);
        }
    }

    private async Task ReceiveLoop(string nodeId, Connection connection, WebSocket socket, CancellationToken cancellationToken)
    {
        while (socket.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
        {
            var payload = await ReceiveOne(socket, cancellationToken); if (payload is null) return;
            CodexRelayAck? ack;
            try { ack = JsonSerializer.Deserialize<CodexRelayAck>(payload, StrictJson); }
            catch (JsonException) { await ClosePolicy(socket, "invalid ack", cancellationToken); return; }
            if (ack is null || Acknowledge(nodeId, ack, DateTimeOffset.UtcNow) != CodexRelayResult.Accepted)
            { await ClosePolicy(socket, "invalid transition", cancellationToken); return; }
            connection.Delivered.TryRemove(ack.CommandId, out _);
        }
    }

    private async Task SendPending(string nodeId, Connection connection, WebSocket socket, CancellationToken cancellationToken)
    {
        foreach (var command in store.ReadPending(nodeId))
        {
            // 同一連線只送一次；斷線後新 session 會以相同 commandId 補送，client 必須依 commandId 冪等。
            if (!connection.Delivered.TryAdd(command.CommandId, 0)) continue;
            var bytes = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, type = "command", commandId = command.CommandId, nodeId = command.NodeId, ownedFiles = command.OwnedFiles, task = command.Task, createdAtUtc = command.CreatedAt });
            if (bytes.Length > MaximumMessageBytes) throw new InvalidOperationException("Stored relay payload exceeded its bound.");
            try { await socket.SendAsync(bytes, WebSocketMessageType.Text, true, cancellationToken); }
            catch (Exception exception) when (IsSocketTransportException(exception)) { throw new RelayTransportClosedException(exception); }
        }
    }

    private static async Task<byte[]?> ReceiveOne(WebSocket socket, CancellationToken cancellationToken)
    {
        using var buffer = new MemoryStream(); var chunk = new byte[2048];
        while (true)
        {
            WebSocketReceiveResult result;
            try { result = await socket.ReceiveAsync(chunk, cancellationToken); }
            catch (Exception exception) when (IsSocketTransportException(exception)) { throw new RelayTransportClosedException(exception); }
            if (result.MessageType == WebSocketMessageType.Close)
            {
                await CloseSocket(socket, result.CloseStatus ?? WebSocketCloseStatus.NormalClosure,
                    result.CloseStatusDescription ?? "peer closed", cancellationToken);
                return null;
            }
            if (result.MessageType != WebSocketMessageType.Text || buffer.Length + result.Count > MaximumMessageBytes) return [];
            await buffer.WriteAsync(chunk.AsMemory(0, result.Count), cancellationToken);
            if (result.EndOfMessage) return buffer.Length == 0 ? [] : buffer.ToArray();
        }
    }

    private static async Task ClosePolicy(WebSocket socket, string reason, CancellationToken cancellationToken)
    {
        if (socket.State == WebSocketState.Open) await CloseSocket(socket, WebSocketCloseStatus.PolicyViolation, reason, cancellationToken);
    }

    private static async Task CloseSocket(WebSocket socket, WebSocketCloseStatus status, string reason, CancellationToken cancellationToken)
    {
        try
        {
            if (socket.State == WebSocketState.CloseReceived) await socket.CloseOutputAsync(status, reason, cancellationToken);
            else if (socket.State == WebSocketState.Open) await socket.CloseAsync(status, reason, cancellationToken);
        }
        catch (Exception exception) when (IsSocketTransportException(exception)) { throw new RelayTransportClosedException(exception); }
    }

    private static bool IsSocketTransportException(Exception exception) =>
        exception is WebSocketException or IOException or ObjectDisposedException;

    private static bool ValidRequest(CodexRelayCommandRequest request)
    {
        if (!AllowedNodes.Contains(request.NodeId) || !CommandIdShape.IsMatch(request.CommandId) ||
            string.IsNullOrWhiteSpace(request.Task) || request.Task.Length > 8192 || request.OwnedFiles.Count is < 1 or > 32 ||
            request.Task.IndexOf('\0') >= 0) return false;
        var normalized = new List<string>(request.OwnedFiles.Count);
        foreach (var item in request.OwnedFiles)
        {
            var path = item.Replace('\\', '/');
            if (path.Length is < 1 or > 256 || !RelativePathShape.IsMatch(path) || Path.IsPathRooted(path) ||
                path.Split('/').Any(part => part is "" or "." or "..") ||
                path.Split('/').Any(part => StringComparer.OrdinalIgnoreCase.Equals(part, ".git"))) return false;
            normalized.Add(path);
        }
        if (normalized.Distinct(StringComparer.OrdinalIgnoreCase).Count() != normalized.Count) return false;
        request.OwnedFiles = normalized;
        return JsonSerializer.SerializeToUtf8Bytes(request).Length <= MaximumMessageBytes;
    }

    private static bool TrySecret(string? value, out byte[] secret)
    {
        secret = [];
        if (string.IsNullOrWhiteSpace(value) || value.Length > 128) return false;
        try
        {
            secret = Convert.FromBase64String(value);
            if (secret.Length is >= 32 and <= 64) return true;
            CryptographicOperations.ZeroMemory(secret); secret = []; return false;
        }
        catch (FormatException) { return false; }
    }

    private static bool TrySignature(string value, out byte[] signature)
    {
        signature = [];
        const string prefix = "sha256=";
        if (!value.StartsWith(prefix, StringComparison.Ordinal) || value.Length != prefix.Length + 64) return false;
        try { signature = Convert.FromHexString(value[prefix.Length..]); return true; }
        catch (FormatException) { return false; }
    }

    private static readonly JsonSerializerOptions StrictJson = new() { PropertyNameCaseInsensitive = false, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private sealed record Connection(string SessionId)
    {
        public SemaphoreSlim Signal { get; } = new(0, 1);
        public ConcurrentDictionary<string, byte> Delivered { get; } = new(StringComparer.Ordinal);
    }
    private sealed class RelayTransportClosedException(Exception innerException) : Exception("WebSocket transport closed.", innerException);
}
