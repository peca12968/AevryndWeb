using System.Diagnostics;
using System.Runtime.CompilerServices;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsDispatchSyncTests
{
    [Fact]
    public async Task OneShotDispatchFixturesPass()
    {
        var root = Repository();
        var start = new ProcessStartInfo(Environment.GetEnvironmentVariable("AEVRYND_PWSH_PATH") ?? "pwsh.exe")
        {
            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true, CreateNoWindow = true
        };
        foreach (var argument in new[] { "-NoProfile", "-File", Path.Combine(root, "AevryndWeb.Tests", "OperationsDispatchSyncBehavior.ps1"),
            "-ScriptPath", Path.Combine(root, "scripts", "Sync-OperationsDispatch.ps1"), "-ResultDirectory",
            Path.Combine(Path.GetTempPath(), "aevrynd-dispatch-sync-" + Guid.NewGuid().ToString("N")) }) start.ArgumentList.Add(argument);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("無法啟動派遣同步測試。");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        try { await process.WaitForExitAsync(timeout.Token); }
        catch (OperationCanceledException)
        {
            try { process.Kill(true); } catch (InvalidOperationException) { }
            await process.WaitForExitAsync();
            Assert.Fail("派遣同步測試逾時。" + await output + await error);
        }
        Assert.True(process.ExitCode == 0, await output + await error);
    }

    private static string Repository([CallerFilePath] string source = "") => Directory.GetParent(Path.GetDirectoryName(source)!)!.FullName;
}
