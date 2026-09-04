using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text.Json;

namespace AevryndWeb.Security;

/// <summary>以低頻率發布本機可驗證的基本遙測；遠端節點與 GPU 不猜測。</summary>
[SupportedOSPlatform("windows")]
public sealed class OperationsTelemetryPublisher(
    IConfiguration configuration,
    ILogger<OperationsTelemetryPublisher> logger) : BackgroundService
{
    private readonly string _statePath = configuration["Operations:StatePath"] ?? @"C:\ProgramData\AevryndWeb\operations-state.json";
    private ulong _previousIdle;
    private ulong _previousKernel;
    private ulong _previousUser;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (!OperatingSystem.IsWindows()) return;
        Directory.CreateDirectory(Path.GetDirectoryName(_statePath)!);
        while (!stoppingToken.IsCancellationRequested)
        {
            try { Publish(DateTimeOffset.UtcNow); }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or ExternalException)
            { logger.LogWarning(exception, "Operations telemetry publish skipped."); }
            await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
        }
    }

    private void Publish(DateTimeOffset now)
    {
        var cpu = ReadCpuPercent();
        var memory = new MemoryStatus();
        GlobalMemoryStatusEx(ref memory);
        var previous = ReadPrevious();
        var nodes = previous?.Nodes?.Where(node => !string.Equals(node.Id, "local", StringComparison.Ordinal)).ToList()
            ?? [];
        nodes.Insert(0, new OperationsNodeState
        {
            Id = "local", CpuPercent = cpu, RamPercent = memory.Total > 0 ? 100d * (memory.Total - memory.Available) / memory.Total : null,
            GpuPercent = ReadGpuPercent(), SampledAt = now
        });
        var document = new OperationsStateDocument
        {
            Version = 1,
            SnapshotAt = now,
            Nodes = nodes,
            ActiveWork = previous?.ActiveWork ?? [],
            History = previous?.History ?? []
        };
        var temporary = _statePath + ".tmp";
        File.WriteAllText(temporary, JsonSerializer.Serialize(document, new JsonSerializerOptions { WriteIndented = true }));
        File.Move(temporary, _statePath, true);
    }

    private OperationsStateDocument? ReadPrevious()
    {
        try
        {
            if (!File.Exists(_statePath)) return null;
            return JsonSerializer.Deserialize<OperationsStateDocument>(File.ReadAllText(_statePath));
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        { return null; }
    }

    private double? ReadCpuPercent()
    {
        if (!GetSystemTimes(out var idle, out var kernel, out var user)) return null;
        var idleTicks = ToUInt64(idle); var kernelTicks = ToUInt64(kernel); var userTicks = ToUInt64(user);
        if (_previousKernel == 0) { _previousIdle = idleTicks; _previousKernel = kernelTicks; _previousUser = userTicks; return null; }
        var total = (kernelTicks - _previousKernel) + (userTicks - _previousUser);
        var busy = total > 0 ? total - (idleTicks - _previousIdle) : 0;
        _previousIdle = idleTicks; _previousKernel = kernelTicks; _previousUser = userTicks;
        return total > 0 ? Math.Round(100d * busy / total, 1) : null;
    }

    private static double? ReadGpuPercent()
    {
        try
        {
            using var process = Process.Start(new ProcessStartInfo
            {
                FileName = "nvidia-smi",
                Arguments = "--query-gpu=utilization.gpu --format=csv,noheader,nounits",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            });
            if (process is null) return null;
            var output = process.StandardOutput.ReadToEnd();
            if (!process.WaitForExit(1500)) { try { process.Kill(); } catch { } return null; }
            var values = output.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries)
                .Select(value => double.TryParse(value.Trim(), System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out var parsed) ? parsed : (double?)null)
                .Where(value => value.HasValue).Select(value => value!.Value).ToArray();
            return values.Length == 0 ? null : Math.Round(values.Average(), 1);
        }
        catch (Exception exception) when (exception is InvalidOperationException or System.ComponentModel.Win32Exception)
        { return null; }
    }

    private static ulong ToUInt64(System.Runtime.InteropServices.ComTypes.FILETIME value) => ((ulong)(uint)value.dwHighDateTime << 32) | (uint)value.dwLowDateTime;

    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GetSystemTimes(out System.Runtime.InteropServices.ComTypes.FILETIME idle, out System.Runtime.InteropServices.ComTypes.FILETIME kernel, out System.Runtime.InteropServices.ComTypes.FILETIME user);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    [StructLayout(LayoutKind.Sequential)] private struct MemoryStatus { public uint Length; public uint MemoryLoad; public ulong Total; public ulong Available; public ulong PageFile; public ulong AvailablePageFile; public ulong Virtual; public ulong AvailableVirtual; public ulong AvailableExtended; public MemoryStatus() { Length = (uint)Marshal.SizeOf<MemoryStatus>(); } }
}
