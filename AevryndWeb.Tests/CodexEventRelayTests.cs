using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class CodexEventRelayTests
{
    private static readonly DateTimeOffset Now = DateTimeOffset.FromUnixTimeSeconds(1_788_480_000);
    private static readonly byte[] Secret = Enumerable.Range(1, 32).Select(value => (byte)value).ToArray();

    [Fact]
    public void HandshakeCanonicalBytesAndHmacVectorAreStable()
    {
        const string timestamp = "1788480000";
        const string nonce = "abcdefghijklmnopqrstuv";
        var canonical = Encoding.UTF8.GetBytes("GET\n/api/codex-relay/connect\ntaichung\n1788480000\nabcdefghijklmnopqrstuv\n");
        Assert.Equal("803fe4e934f04e2af869b1c510ab5f9e87a9a5eb060d94d8dbf101c0675ef5e7",
            Convert.ToHexString(HMACSHA256.HashData(Secret, canonical)).ToLowerInvariant());
        var relay = CreateRelay();
        var signature = "sha256=" + Convert.ToHexString(HMACSHA256.HashData(Secret, canonical)).ToLowerInvariant();
        Assert.Equal(CodexRelayResult.Accepted, relay.Authenticate("taichung", timestamp, nonce, signature, Now));
        Assert.Equal(CodexRelayResult.Replay, relay.Authenticate("taichung", timestamp, nonce, signature, Now));
    }

    [Fact]
    public void HandshakeRejectsInvalidNodeStaleTimestampAndTampering()
    {
        var relay = CreateRelay();
        Assert.Equal(CodexRelayResult.Invalid, Authenticate(relay, "unknown", Now));
        Assert.Equal(CodexRelayResult.Unauthorized, Authenticate(relay, "taichung", Now.AddMinutes(-3)));
        var timestamp = Now.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture);
        Assert.Equal(CodexRelayResult.Unauthorized, relay.Authenticate("taichung", timestamp, "abcdefghijklmnopqrstuv", "sha256=" + new string('0', 64), Now));
    }

    [Fact]
    public void PublisherHmacAuthenticatesExactRawBodyAndRejectsReplay()
    {
        var relay = CreateRelay(); var body = Encoding.UTF8.GetBytes("{\"commandId\":\"work-1\"}");
        var timestamp = Now.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture); const string nonce = "publishernonce1234567890";
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/codex-relay/publisher-commands\n{timestamp}\n{nonce}\n");
        var signature = Sign(prefix.Concat(body).ToArray());
        Assert.Equal(CodexRelayResult.Accepted, relay.AuthenticatePublisher(timestamp, nonce, signature, body, Now));
        Assert.Equal(CodexRelayResult.Replay, relay.AuthenticatePublisher(timestamp, nonce, signature, body, Now));
        body[^1] ^= 1;
        Assert.Equal(CodexRelayResult.Unauthorized, relay.AuthenticatePublisher(timestamp, nonce + "x", signature, body, Now));
    }

    [Fact]
    public void PayloadBoundsAndDuplicateCommandIdsFailClosed()
    {
        var relay = CreateRelay();
        Assert.Equal(CodexRelayResult.Invalid, relay.Submit(Command("bad", "unknown"), Now));
        Assert.Equal(CodexRelayResult.Invalid, relay.Submit(Command("bad:id"), Now));
        Assert.Equal(CodexRelayResult.Invalid, relay.Submit(Command("bad-path", task: "work", ownedFiles: ["../secret"]), Now));
        Assert.Equal(CodexRelayResult.Invalid, relay.Submit(Command("git-path", task: "work", ownedFiles: [".git/config"]), Now));
        Assert.Equal(CodexRelayResult.Invalid, relay.Submit(Command("huge", task: new string('x', 8193)), Now));
        Assert.Equal(CodexRelayResult.Accepted, relay.Submit(Command("glob", ownedFiles: ["engine/native/**/*.cpp"]), Now));
        var command = Command("same-id");
        Assert.Equal(CodexRelayResult.Accepted, relay.Submit(command, Now));
        Assert.Equal(CodexRelayResult.Duplicate, relay.Submit(command, Now.AddSeconds(1)));
        Assert.Equal(2, relay.ReadHistory(100).Count);
        Assert.Equal("engine/native/**/*.cpp", relay.ReadHistory(100).Single(item => item.CommandId == "glob").OwnedFiles.Single());
    }

    [Fact]
    public void AckTransitionsAreStrictAndRecordedForOperationsHistory()
    {
        var relay = CreateRelay(); Assert.Equal(CodexRelayResult.Accepted, relay.Submit(Command("lost-running"), Now));
        // running ACK 可能已離開 client、但在 server 持久化前斷線；terminal 必須能封口 queued，而不能永久卡住 outbox。
        Assert.Equal(CodexRelayResult.Accepted, relay.Acknowledge("taichung", Ack("lost-running", "completed", Now.AddSeconds(1), 0), Now.AddSeconds(1)));
        Assert.Equal(CodexRelayResult.Accepted, relay.Submit(Command("ack-1"), Now));
        Assert.Equal(CodexRelayResult.Invalid, relay.Acknowledge("taichung", Ack("ack-1", "failed", Now.AddSeconds(1), 0), Now.AddSeconds(1)));
        Assert.Equal(CodexRelayResult.Invalid, relay.Acknowledge("taoyuan", Ack("ack-1", "running", Now.AddSeconds(1)), Now.AddSeconds(1)));
        Assert.Equal(CodexRelayResult.Accepted, relay.Acknowledge("taichung", Ack("ack-1", "running", Now.AddSeconds(1)), Now.AddSeconds(1)));
        Assert.Equal(CodexRelayResult.Accepted, relay.Acknowledge("taichung", Ack("ack-1", "completed", Now.AddSeconds(2), 0), Now.AddSeconds(2)));
        var completed = relay.ReadHistory(100).Single(item => item.CommandId == "ack-1"); Assert.Equal(CodexRelayCommandStatus.Completed, completed.Status); Assert.Equal(0, completed.ExitCode);
    }

    [Fact]
    public async Task ReconnectRedeliversIncompleteCommandWithSameIdentity()
    {
        var relay = CreateRelay(); relay.Submit(Command("resume-1"), Now);
        using var first = FakeWebSocket.CloseAfterOneReceive(); await relay.RunConnectionAsync("taichung", first, CancellationToken.None);
        using var second = FakeWebSocket.CloseAfterOneReceive(); await relay.RunConnectionAsync("taichung", second, CancellationToken.None);
        Assert.Equal("resume-1", JsonDocument.Parse(Assert.Single(first.Sent)).RootElement.GetProperty("commandId").GetString());
        var redelivered = JsonDocument.Parse(Assert.Single(second.Sent)).RootElement;
        Assert.Equal(1, redelivered.GetProperty("version").GetInt32()); Assert.Equal("resume-1", redelivered.GetProperty("commandId").GetString());
        Assert.Equal("command", redelivered.GetProperty("type").GetString()); Assert.True(redelivered.TryGetProperty("createdAtUtc", out _));
    }

    [Fact]
    public async Task ConcurrentConnectionsAllowOnlyOneNodeClaim()
    {
        var relay = CreateRelay(); relay.Submit(Command("claim-1"), Now);
        using var cancellation = new CancellationTokenSource(); using var first = FakeWebSocket.Blocking();
        var active = relay.RunConnectionAsync("taichung", first, cancellation.Token); await first.WaitForSend();
        using var contender = FakeWebSocket.CloseAfterOneReceive(); await relay.RunConnectionAsync("taichung", contender, CancellationToken.None);
        Assert.Equal(WebSocketCloseStatus.PolicyViolation, contender.CloseStatus);
        cancellation.Cancel(); await active;
        Assert.Single(first.Sent);
    }

    [Fact]
    public async Task RealWebSocketPublisherCommandAndAckRoundTrip()
    {
        using var factory = new CodexRelayFactory();
        var webSocketClient = factory.Server.CreateWebSocketClient();
        var signedAt = DateTimeOffset.UtcNow; var timestamp = signedAt.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture);
        const string nodeNonce = "realtimehandshakenonce01";
        webSocketClient.ConfigureRequest = request =>
        {
            request.Headers["X-Aevrynd-Node"] = "taichung";
            request.Headers["X-Aevrynd-Timestamp"] = timestamp;
            request.Headers["X-Aevrynd-Nonce"] = nodeNonce;
            request.Headers["X-Aevrynd-Signature"] = Sign(Encoding.UTF8.GetBytes($"GET\n/api/codex-relay/connect\ntaichung\n{timestamp}\n{nodeNonce}\n"));
        };
        using var socket = await webSocketClient.ConnectAsync(new Uri("ws://localhost/api/codex-relay/connect"), CancellationToken.None);

        var body = Encoding.UTF8.GetBytes("{\"commandId\":\"roundtrip-1\",\"nodeId\":\"taichung\",\"ownedFiles\":[\"engine/native/**/*.cpp\"],\"task\":\"Read the bounded source\"}");
        const string publisherNonce = "publisherroundtripnonce01";
        var prefix = Encoding.UTF8.GetBytes($"POST\n/api/codex-relay/publisher-commands\n{timestamp}\n{publisherNonce}\n");
        using var request = new HttpRequestMessage(HttpMethod.Post, "/api/codex-relay/publisher-commands") { Content = new ByteArrayContent(body) };
        request.Content.Headers.ContentType = new("application/json");
        request.Headers.Add("X-Aevrynd-Timestamp", timestamp); request.Headers.Add("X-Aevrynd-Nonce", publisherNonce);
        request.Headers.Add("X-Aevrynd-Signature", Sign(prefix.Concat(body).ToArray()));
        using var http = factory.CreateClient(new WebApplicationFactoryClientOptions { BaseAddress = new Uri("https://localhost"), AllowAutoRedirect = false });
        using var response = await http.SendAsync(request); Assert.Equal(System.Net.HttpStatusCode.Accepted, response.StatusCode);

        var commandBytes = new byte[16_384]; var received = await socket.ReceiveAsync(commandBytes, CancellationToken.None);
        var command = JsonDocument.Parse(commandBytes.AsMemory(0, received.Count));
        Assert.Equal("roundtrip-1", command.RootElement.GetProperty("commandId").GetString());
        var running = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, type = "ack", commandId = "roundtrip-1", nodeId = "taichung", state = "running", occurredAtUtc = DateTimeOffset.UtcNow, exitCode = (int?)null, summary = "Command claimed before execution" });
        var split = running.Length / 2;
        await socket.SendAsync(running.AsMemory(0, split), WebSocketMessageType.Text, false, CancellationToken.None);
        await socket.SendAsync(running.AsMemory(split), WebSocketMessageType.Text, true, CancellationToken.None);
        var completed = JsonSerializer.SerializeToUtf8Bytes(new { version = 1, type = "ack", commandId = "roundtrip-1", nodeId = "taichung", state = "completed", occurredAtUtc = DateTimeOffset.UtcNow.AddMilliseconds(1), exitCode = 0, summary = "Codex completed" });
        await socket.SendAsync(completed, WebSocketMessageType.Text, true, CancellationToken.None);
        for (var attempt = 0; attempt < 50 && factory.Relay.ReadHistory(10).Single().Status != CodexRelayCommandStatus.Completed; attempt++) await Task.Delay(10);
        Assert.Equal(CodexRelayCommandStatus.Completed, factory.Relay.ReadHistory(10).Single().Status);
        await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "test complete", CancellationToken.None);
        Assert.Empty(factory.Logs.Errors);
    }

    [Fact]
    public async Task RealWebSocketNormalAndAbruptCloseAreCleanAndReleaseNodeClaim()
    {
        using var factory = new CodexRelayFactory();
        using (var normal = await Connect(factory, "normalclosehandshake01"))
            await normal.CloseAsync(WebSocketCloseStatus.NormalClosure, "normal", CancellationToken.None);

        var abrupt = await Connect(factory, "abruptclosehandshake01"); abrupt.Dispose();
        await Task.Delay(50);
        using var replacement = await Connect(factory, "replacementhandshake01");
        Assert.Equal(CodexRelayResult.Accepted, factory.Relay.Submit(Command("after-abrupt"), DateTimeOffset.UtcNow));
        var bytes = new byte[16_384]; var received = await replacement.ReceiveAsync(bytes, CancellationToken.None);
        Assert.Equal(WebSocketMessageType.Text, received.MessageType);
        Assert.Equal("after-abrupt", JsonDocument.Parse(bytes.AsMemory(0, received.Count)).RootElement.GetProperty("commandId").GetString());
        await replacement.CloseAsync(WebSocketCloseStatus.NormalClosure, "replacement complete", CancellationToken.None);
        await Task.Delay(25);
        Assert.Empty(factory.Logs.Errors);
    }

    [Fact]
    public async Task RealWebSocketBinaryAndOversizedMessagesUsePolicyCloseWithoutErrorLogs()
    {
        using var factory = new CodexRelayFactory();
        using (var binary = await Connect(factory, "binaryframehandshake01"))
        {
            await binary.SendAsync(new byte[] { 1, 2, 3 }, WebSocketMessageType.Binary, true, CancellationToken.None);
            var result = await binary.ReceiveAsync(new byte[64], CancellationToken.None);
            Assert.Equal(WebSocketMessageType.Close, result.MessageType); Assert.Equal(WebSocketCloseStatus.PolicyViolation, result.CloseStatus);
        }
        using (var oversized = await Connect(factory, "oversizeframehandshake1"))
        {
            var chunk = new byte[2048];
            for (var index = 0; index < 8; index++) await oversized.SendAsync(chunk, WebSocketMessageType.Text, false, CancellationToken.None);
            await oversized.SendAsync(new byte[] { (byte)'x' }, WebSocketMessageType.Text, true, CancellationToken.None);
            var result = await oversized.ReceiveAsync(new byte[64], CancellationToken.None);
            Assert.Equal(WebSocketMessageType.Close, result.MessageType); Assert.Equal(WebSocketCloseStatus.PolicyViolation, result.CloseStatus);
        }
        await Task.Delay(25);
        Assert.Empty(factory.Logs.Errors);
    }

    [Fact]
    public async Task OnlySocketBoundaryTransportExceptionsAreAbsorbed()
    {
        foreach (var exception in new Exception[] { new WebSocketException("transport"), new IOException("transport"), new ObjectDisposedException("socket") })
        {
            var relay = CreateRelay(); using var socket = new ThrowingWebSocket(exception);
            await relay.RunConnectionAsync("taichung", socket, CancellationToken.None);
        }

        var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        { ["Operations:CodexRelay:Nodes:taichung:Secret"] = Convert.ToBase64String(Secret) }).Build();
        var faulty = new CodexEventRelay(configuration, new ThrowingStore(), new MemoryCodexEventRelayReplayStore());
        using var blocking = FakeWebSocket.Blocking();
        await Assert.ThrowsAsync<IOException>(() => faulty.RunConnectionAsync("taichung", blocking, CancellationToken.None));
    }

    [Fact]
    public void ConcurrentDuplicateSubmissionHasExactlyOneWinner()
    {
        var relay = CreateRelay(); var results = new CodexRelayResult[32];
        Parallel.For(0, results.Length, index => results[index] = relay.Submit(Command("atomic-id"), Now));
        Assert.Single(results.Where(result => result == CodexRelayResult.Accepted));
        Assert.Equal(31, results.Count(result => result == CodexRelayResult.Duplicate));
    }

    [Fact]
    public void BoundedHistoryRetainsExactlyOnceTombstonesAfterEviction()
    {
        var relay = CreateRelay();
        for (var index = 0; index < 201; index++)
        {
            var id = $"history-{index}"; var runningAt = Now.AddSeconds(index * 2 + 1); var endedAt = runningAt.AddSeconds(1);
            Assert.Equal(CodexRelayResult.Accepted, relay.Submit(Command(id), Now.AddSeconds(index * 2)));
            Assert.Equal(CodexRelayResult.Accepted, relay.Acknowledge("taichung", Ack(id, "running", runningAt), runningAt));
            Assert.Equal(CodexRelayResult.Accepted, relay.Acknowledge("taichung", Ack(id, index == 200 ? "failed" : "completed", endedAt, index == 200 ? 7 : 0), endedAt));
        }
        Assert.Equal(200, relay.ReadHistory(200).Count);
        Assert.Equal(CodexRelayResult.Duplicate, relay.Submit(Command("history-0"), Now.AddHours(1)));
        var failed = relay.ReadHistory(200).Single(item => item.CommandId == "history-200");
        Assert.Equal(CodexRelayCommandStatus.Failed, failed.Status); Assert.Equal(7, failed.ExitCode);
    }

    [Fact]
    public void FileStorePersistsPendingExactlyOnceAndFailsClosedOnCorruption()
    {
        if (!OperatingSystem.IsWindows()) return;
        var directory = SecureTemporaryDirectory();
        try
        {
            var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
            { ["Operations:CodexRelay:StateDirectory"] = directory }).Build();
            var first = new FileCodexEventRelayStore(configuration);
            var state = new CodexRelayCommandState { CommandId = "durable-1", NodeId = "taichung", OwnedFiles = ["Engine/Test.cs"], Task = "Durable task", Status = CodexRelayCommandStatus.Queued, CreatedAt = Now, UpdatedAt = Now };
            Assert.Equal(CodexRelayResult.Accepted, first.TryCreate(state));
            Assert.Empty(Directory.GetFiles(directory, "*.tmp"));
            var restarted = new FileCodexEventRelayStore(configuration);
            Assert.Equal("durable-1", Assert.Single(restarted.ReadPending("taichung")).CommandId);
            Assert.Equal(CodexRelayResult.Duplicate, restarted.TryCreate(state));
            var replay = new FileCodexEventRelayReplayStore(configuration);
            Assert.Equal(CodexRelayResult.Accepted, replay.TryConsume("node-taichung", "abcdefghijklmnopqrstuv", Now));
            Assert.Equal(CodexRelayResult.Replay, new FileCodexEventRelayReplayStore(configuration).TryConsume("node-taichung", "abcdefghijklmnopqrstuv", Now.AddSeconds(1)));
            File.WriteAllText(Path.Combine(directory, "commands.json"), "{broken");
            Assert.Equal(CodexRelayResult.Unavailable, restarted.TryCreate(WithId(state, "durable-2")));
            File.WriteAllText(Path.Combine(directory, "codex-relay-replay.json"), "{broken");
            Assert.Equal(CodexRelayResult.Unavailable, replay.TryConsume("node-taichung", "differentnonce1234567890", Now.AddSeconds(2)));
        }
        finally { Directory.Delete(directory, true); }
    }

    private static ICodexEventRelay CreateRelay()
    {
        var values = new Dictionary<string, string?>
        {
            ["Operations:CodexRelay:Nodes:taichung:Secret"] = Convert.ToBase64String(Secret),
            ["Operations:CodexRelay:Nodes:taoyuan:Secret"] = Convert.ToBase64String(Secret),
            ["Operations:CodexRelay:PublisherSecret"] = Convert.ToBase64String(Secret)
        };
        return new CodexEventRelay(new ConfigurationBuilder().AddInMemoryCollection(values).Build(), new MemoryCodexEventRelayStore(), new MemoryCodexEventRelayReplayStore());
    }

    private static CodexRelayResult Authenticate(ICodexEventRelay relay, string node, DateTimeOffset signedAt)
    {
        var timestamp = signedAt.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture); const string nonce = "abcdefghijklmnopqrstuv";
        var canonical = Encoding.UTF8.GetBytes($"GET\n/api/codex-relay/connect\n{node}\n{timestamp}\n{nonce}\n");
        return relay.Authenticate(node, timestamp, nonce, Sign(canonical), Now);
    }

    private static string Sign(byte[] bytes) => "sha256=" + Convert.ToHexString(HMACSHA256.HashData(Secret, bytes)).ToLowerInvariant();
    private static async Task<WebSocket> Connect(CodexRelayFactory factory, string nonce)
    {
        var signedAt = DateTimeOffset.UtcNow; var timestamp = signedAt.ToUnixTimeSeconds().ToString(System.Globalization.CultureInfo.InvariantCulture);
        var client = factory.Server.CreateWebSocketClient();
        client.ConfigureRequest = request =>
        {
            request.Headers["X-Aevrynd-Node"] = "taichung"; request.Headers["X-Aevrynd-Timestamp"] = timestamp;
            request.Headers["X-Aevrynd-Nonce"] = nonce;
            request.Headers["X-Aevrynd-Signature"] = Sign(Encoding.UTF8.GetBytes($"GET\n/api/codex-relay/connect\ntaichung\n{timestamp}\n{nonce}\n"));
        };
        return await client.ConnectAsync(new Uri("ws://localhost/api/codex-relay/connect"), CancellationToken.None);
    }
    private static CodexRelayCommandRequest Command(string id, string node = "taichung", string task = "Run bounded validation", List<string>? ownedFiles = null) =>
        new() { CommandId = id, NodeId = node, OwnedFiles = ownedFiles ?? ["Engine/Renderer.cs"], Task = task };
    private static CodexRelayAck Ack(string id, string state, DateTimeOffset occurred, int? exitCode = null) =>
        new() { Version = 1, Type = "ack", CommandId = id, NodeId = "taichung", State = state, OccurredAtUtc = occurred, ExitCode = exitCode, Summary = "bounded result" };

    [SupportedOSPlatform("windows")]
    private static string SecureTemporaryDirectory()
    {
        var path = Path.Combine(Path.GetTempPath(), "AevryndWeb-relay-tests-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(path);
        var security = new DirectorySecurity(); security.SetAccessRuleProtection(true, false);
        var inheritance = InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit;
        foreach (var sid in new[] { WindowsIdentity.GetCurrent().User!, new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null), new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null) })
            security.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, inheritance, PropagationFlags.None, AccessControlType.Allow));
        new DirectoryInfo(path).SetAccessControl(security); return path;
    }

    private static CodexRelayCommandState WithId(CodexRelayCommandState state, string id) => new() { CommandId = id, NodeId = state.NodeId, OwnedFiles = state.OwnedFiles, Task = state.Task, Status = state.Status, CreatedAt = state.CreatedAt, UpdatedAt = state.UpdatedAt };

    private sealed class FakeWebSocket(bool block) : WebSocket
    {
        private readonly TaskCompletionSource _sent = new(TaskCreationOptions.RunContinuationsAsynchronously);
        private WebSocketState _state = WebSocketState.Open;
        private WebSocketCloseStatus? _closeStatus;
        private string? _closeDescription;
        public List<byte[]> Sent { get; } = [];
        public override WebSocketCloseStatus? CloseStatus => _closeStatus;
        public override string? CloseStatusDescription => _closeDescription;
        public override string? SubProtocol => null;
        public override WebSocketState State => _state;
        public static FakeWebSocket Blocking() => new(true);
        public static FakeWebSocket CloseAfterOneReceive() => new(false);
        public Task WaitForSend() => _sent.Task;
        public override void Abort() => _state = WebSocketState.Aborted;
        public override Task CloseAsync(WebSocketCloseStatus closeStatus, string? statusDescription, CancellationToken cancellationToken) { _closeStatus = closeStatus; _closeDescription = statusDescription; _state = WebSocketState.Closed; return Task.CompletedTask; }
        public override Task CloseOutputAsync(WebSocketCloseStatus closeStatus, string? statusDescription, CancellationToken cancellationToken) => CloseAsync(closeStatus, statusDescription, cancellationToken);
        public override void Dispose() => _state = WebSocketState.Closed;
        public override async Task<WebSocketReceiveResult> ReceiveAsync(ArraySegment<byte> buffer, CancellationToken cancellationToken)
        {
            if (block) { await Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken); }
            _state = WebSocketState.CloseReceived; return new WebSocketReceiveResult(0, WebSocketMessageType.Close, true, WebSocketCloseStatus.NormalClosure, "test");
        }
        public override Task SendAsync(ArraySegment<byte> buffer, WebSocketMessageType messageType, bool endOfMessage, CancellationToken cancellationToken)
        {
            Sent.Add(buffer.ToArray()); _sent.TrySetResult(); return Task.CompletedTask;
        }
    }

    private sealed class ThrowingWebSocket(Exception exception) : WebSocket
    {
        public override WebSocketCloseStatus? CloseStatus => null;
        public override string? CloseStatusDescription => null;
        public override string? SubProtocol => null;
        public override WebSocketState State => WebSocketState.Open;
        public override void Abort() { }
        public override Task CloseAsync(WebSocketCloseStatus closeStatus, string? statusDescription, CancellationToken cancellationToken) => Task.CompletedTask;
        public override Task CloseOutputAsync(WebSocketCloseStatus closeStatus, string? statusDescription, CancellationToken cancellationToken) => Task.CompletedTask;
        public override void Dispose() { }
        public override Task<WebSocketReceiveResult> ReceiveAsync(ArraySegment<byte> buffer, CancellationToken cancellationToken) => Task.FromException<WebSocketReceiveResult>(exception);
        public override Task SendAsync(ArraySegment<byte> buffer, WebSocketMessageType messageType, bool endOfMessage, CancellationToken cancellationToken) => Task.CompletedTask;
    }

    private sealed class ThrowingStore : ICodexEventRelayStore
    {
        public CodexRelayResult TryCreate(CodexRelayCommandState command) => CodexRelayResult.Accepted;
        public IReadOnlyList<CodexRelayCommandState> ReadPending(string nodeId) => throw new IOException("persistent store failure");
        public IReadOnlyList<CodexRelayCommandState> ReadHistory(int maximum) => [];
        public CodexRelayResult TryAcknowledge(string nodeId, CodexRelayAck ack, DateTimeOffset now) => CodexRelayResult.Unavailable;
    }

    private sealed class CodexRelayFactory : WebApplicationFactory<Program>
    {
        public ICodexEventRelay Relay => Services.GetRequiredService<ICodexEventRelay>();
        public RelayLogSink Logs { get; } = new();
        protected override void ConfigureWebHost(IWebHostBuilder builder)
        {
            builder.UseEnvironment("Testing");
            builder.ConfigureAppConfiguration((_, configuration) => configuration.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Operations:CodexRelay:Nodes:taichung:Secret"] = Convert.ToBase64String(Secret),
                ["Operations:CodexRelay:Nodes:taoyuan:Secret"] = Convert.ToBase64String(Secret),
                ["Operations:CodexRelay:PublisherSecret"] = Convert.ToBase64String(Secret)
            }));
            builder.ConfigureTestServices(services =>
            {
                services.RemoveAll<ICodexEventRelayStore>(); services.AddSingleton<ICodexEventRelayStore, MemoryCodexEventRelayStore>();
                services.RemoveAll<ICodexEventRelayReplayStore>(); services.AddSingleton<ICodexEventRelayReplayStore, MemoryCodexEventRelayReplayStore>();
                services.AddLogging(logging => logging.AddProvider(Logs));
            });
        }
    }

    private sealed class RelayLogSink : ILoggerProvider
    {
        public ConcurrentQueue<string> Errors { get; } = new();
        public ILogger CreateLogger(string categoryName) => new SinkLogger(this, categoryName);
        public void Dispose() { }
        private sealed class SinkLogger(RelayLogSink sink, string category) : ILogger
        {
            public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;
            public bool IsEnabled(LogLevel logLevel) => logLevel >= LogLevel.Error;
            public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
            { if (logLevel >= LogLevel.Error) sink.Errors.Enqueue(category + ": " + formatter(state, exception)); }
        }
    }
}
