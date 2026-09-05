using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsDispatchRunnerTests
{
    [Fact]
    public async Task RealFixtureRunnerUsesSharedProjectionPreservesUnchangedStateAndFailsClosed()
    {
        var fixture = Environment.GetEnvironmentVariable("AEVRYND_DISPATCH_FIXTURE");
        Assert.False(string.IsNullOrWhiteSpace(fixture), "AEVRYND_DISPATCH_FIXTURE is required.");
        Assert.Equal("F4CE34049212168F4F8D8C30E2694D918803EB120566F26B44A15E4D22003E4B", Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(fixture!))));
        var root = new DirectoryInfo(AppContext.BaseDirectory);
        while (root is not null && !File.Exists(Path.Combine(root.FullName, "AevryndWeb.slnx"))) root = root.Parent;
        Assert.NotNull(root);
        var directory = Path.Combine(Path.GetTempPath(), "aevrynd-dispatch-runner-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        var script = Path.Combine(root.FullName, "scripts", "Watch-OperationsDispatch.ps1");
        async Task<(int Exit, string Output)> Run(string input)
        {
            var start = new ProcessStartInfo("pwsh") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (var argument in new[] { "-NoProfile", "-NonInteractive", "-File", script, "-AssemblyPath", typeof(OperationsDispatchProjection).Assembly.Location, "-StateDirectory", directory, "-CommentsPath", input, "-Once" }) start.ArgumentList.Add(argument);
            using var process = Process.Start(start)!;
            var stdout = process.StandardOutput.ReadToEndAsync(); var stderr = process.StandardError.ReadToEndAsync();
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(25));
            try { await process.WaitForExitAsync(timeout.Token); }
            catch (OperationCanceledException) { process.Kill(true); throw; }
            return (process.ExitCode, await stdout + await stderr);
        }
        var first = await Run(fixture!); Assert.True(first.Exit == 0, first.Output);
        var path = Path.Combine(directory, "dispatch-state.json");
        var state = await File.ReadAllTextAsync(path); var stamp = File.GetLastWriteTimeUtc(path);
        Assert.Equal(102, OperationsDispatchProjection.ReadDocument(state).Tasks.Count);
        var second = await Run(fixture!); Assert.True(second.Exit == 0, second.Output); Assert.Contains("CHANGED=False", second.Output);
        Assert.Equal(stamp, File.GetLastWriteTimeUtc(path)); Assert.Equal(state, await File.ReadAllTextAsync(path));
        using (var health = JsonDocument.Parse(await File.ReadAllTextAsync(Path.Combine(directory, "dispatch-health.json"))))
        {
            Assert.Equal("offline", health.RootElement.GetProperty("status").GetString());
            Assert.Equal(JsonValueKind.Null, health.RootElement.GetProperty("lastSuccessAt").ValueKind);
        }
        var invalid = Path.Combine(directory, "invalid.json"); await File.WriteAllTextAsync(invalid, "{invalid");
        Assert.Equal(1, (await Run(invalid)).Exit); Assert.Equal(state, await File.ReadAllTextAsync(path));
        using (var held = File.Open(Path.Combine(directory, ".dispatch-sync.lock"), FileMode.Open, FileAccess.ReadWrite, FileShare.None))
            Assert.Contains("DISPATCH_SYNC_ALREADY_RUNNING", (await Run(fixture!)).Output);
        var install = await File.ReadAllTextAsync(Path.Combine(root.FullName, "scripts", "Install-OperationsDispatchSync.ps1"));
        Assert.Contains("-WindowStyle Hidden", install); Assert.Contains("-AtLogOn", install); Assert.Contains("-MultipleInstances IgnoreNew", install);
        Assert.Contains("SupportsShouldProcess", install);
    }
}
