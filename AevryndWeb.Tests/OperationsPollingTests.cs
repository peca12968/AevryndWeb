using System.Diagnostics;
using System.Runtime.CompilerServices;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsPollingTests
{
    [Fact]
    public async Task BrowserPollingBehaviorPassesDeterministicNodeHarness()
    {
        var repository = FindRepository();
        var nodePath = Environment.GetEnvironmentVariable("AEVRYND_NODE_PATH") ?? "node.exe";
        var resultPath = Environment.GetEnvironmentVariable("AEVRYND_OPERATIONS_POLLING_OUTPUT") ??
            Path.Combine(Path.GetTempPath(), $"aevrynd-operations-polling-{Guid.NewGuid():N}.json");
        var startInfo = new ProcessStartInfo
        {
            FileName = nodePath,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };
        startInfo.ArgumentList.Add(Path.Combine(repository, "AevryndWeb.Tests", "OperationsPollingBehavior.mjs"));
        startInfo.ArgumentList.Add(Path.Combine(repository, "AevryndWeb", "wwwroot", "js", "site.js"));
        startInfo.ArgumentList.Add(resultPath);

        using var process = Process.Start(startInfo) ?? throw new InvalidOperationException("無法啟動 Node 行為測試。");
        var standardOutputTask = process.StandardOutput.ReadToEndAsync();
        var standardErrorTask = process.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        try
        {
            await process.WaitForExitAsync(timeout.Token);
        }
        catch (OperationCanceledException)
        {
            try { process.Kill(entireProcessTree: true); }
            catch (InvalidOperationException) { }
            await process.WaitForExitAsync();
            var timedOutOutput = await standardOutputTask;
            var timedOutError = await standardErrorTask;
            Assert.Fail($"Node 行為測試逾時。{Environment.NewLine}{timedOutOutput}{Environment.NewLine}{timedOutError}");
        }
        var standardOutput = await standardOutputTask;
        var standardError = await standardErrorTask;
        Assert.True(process.ExitCode == 0, $"Node 行為測試失敗。{Environment.NewLine}{standardOutput}{Environment.NewLine}{standardError}");
    }

    private static string FindRepository([CallerFilePath] string sourcePath = "")
    {
        var starts = new[]
        {
            Environment.GetEnvironmentVariable("AEVRYND_WEB_REPOSITORY"),
            Directory.GetCurrentDirectory(),
            Path.GetDirectoryName(sourcePath),
            AppContext.BaseDirectory
        };
        foreach (var start in starts.Where(value => !string.IsNullOrWhiteSpace(value)))
        {
            var directory = new DirectoryInfo(start!);
            while (directory is not null)
            {
                if (File.Exists(Path.Combine(directory.FullName, "AevryndWeb", "wwwroot", "js", "site.js")) &&
                    File.Exists(Path.Combine(directory.FullName, "AevryndWeb.Tests", "OperationsPollingBehavior.mjs")))
                    return directory.FullName;
                directory = directory.Parent;
            }
        }
        throw new DirectoryNotFoundException("找不到 AevryndWeb repository root。");
    }
}
