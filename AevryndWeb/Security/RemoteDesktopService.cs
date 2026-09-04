using System.Collections.Concurrent;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

#pragma warning disable CA1416
namespace AevryndWeb.Security;

public interface IRemoteDesktopService
{
    RemoteDesktopAvailability GetAvailability();
    Task<RemoteDesktopFrame> CaptureJpegAsync(CancellationToken cancellationToken);
    Task SendTextAsync(string sessionId, string text, CancellationToken cancellationToken);
    Task SendKeyboardAsync(string sessionId, IReadOnlyList<RemoteKeyStroke> strokes, CancellationToken cancellationToken);
    Task SendMouseAsync(string sessionId, RemoteMouseAction action, CancellationToken cancellationToken);
    void ReleaseInjectedModifiers(string? sessionId);
    void ReleaseAllInjectedModifiers();
    void RetryPendingReleases();
}

public sealed record RemoteDesktopAvailability(bool Available, string Reason);
public sealed record RemoteDesktopFrame(byte[] Jpeg, long Generation, DateTimeOffset CapturedAt, int Width, int Height);
public sealed record RemoteKeyStroke(string Code, string Action);
public sealed record RemoteMouseAction(long FrameGeneration, double X, double Y, string Action, int Delta = 0);
public sealed class RemoteDesktopUnavailableException(string message) : Exception(message);

public static class RemoteTokenSafety
{
    public static bool IsSafe(bool elevationQuerySucceeded, bool elevated, bool uiAccessQuerySucceeded, bool uiAccess) =>
        elevationQuerySucceeded && !elevated && uiAccessQuerySucceeded && !uiAccess;
}

public sealed record RemoteMonitorDescriptor(string Device, int Left, int Top, int Right, int Bottom, uint DpiX, uint DpiY, uint Rotation, bool Primary);
public static class RemoteDisplayTopology
{
    public static string Hash(IEnumerable<RemoteMonitorDescriptor> monitors)
    {
        var canonical = string.Join("\n", monitors.OrderBy(item => item.Device, StringComparer.Ordinal).ThenBy(item => item.Left).ThenBy(item => item.Top)
            .Select(item => string.Join('|', item.Device, item.Left, item.Top, item.Right, item.Bottom, item.DpiX, item.DpiY, item.Rotation, item.Primary ? 1 : 0)));
        if (canonical.Length == 0) throw new RemoteDesktopUnavailableException("無法確認顯示器拓樸。");
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)));
    }
}

public readonly record struct RemoteInjectedKey(ushort VirtualKey, char UnicodeCharacter, bool Unicode, bool Extended);
public readonly record struct RemoteInjectedKeyEvent(RemoteInjectedKey Key, bool IsUp);

public sealed class RemoteInputLedger(Func<RemoteInjectedKeyEvent, bool> injector)
{
    private readonly Dictionary<string, HashSet<RemoteInjectedKey>> pressed = new(StringComparer.Ordinal);
    private readonly HashSet<string> releasing = new(StringComparer.Ordinal);

    public void Send(string sessionId, IReadOnlyList<RemoteInjectedKeyEvent> events)
    {
        if (sessionId.Length == 0 || events.Count == 0) throw new RemoteDesktopUnavailableException("輸入工作階段或事件無效。");
        var ledger = GetLedger(sessionId);
        foreach (var item in events)
        {
            if (!injector(item))
            {
                // 已接受的 prefix 由逐事件送出精確得知；立即釋放該工作階段所有已按下按鍵。
                Release(sessionId);
                throw new RemoteDesktopUnavailableException("Windows 未接受輸入事件；已進入按鍵釋放流程。");
            }
            if (item.IsUp) ledger.Remove(item.Key); else ledger.Add(item.Key);
        }
        if (ledger.Count == 0) pressed.Remove(sessionId);
    }

    public void Release(string? sessionId)
    {
        if (string.IsNullOrEmpty(sessionId) || !pressed.ContainsKey(sessionId)) return;
        releasing.Add(sessionId);
        Retry(sessionId);
    }

    public void ReleaseAll()
    {
        foreach (var sessionId in pressed.Keys.ToArray()) releasing.Add(sessionId);
        RetryPending();
    }

    public void RetryPending()
    {
        foreach (var sessionId in releasing.ToArray()) Retry(sessionId);
    }

    public IReadOnlyCollection<RemoteInjectedKey> Snapshot(string sessionId) =>
        pressed.TryGetValue(sessionId, out var ledger) ? ledger.ToArray() : [];

    private HashSet<RemoteInjectedKey> GetLedger(string sessionId)
    {
        if (!pressed.TryGetValue(sessionId, out var ledger)) pressed[sessionId] = ledger = [];
        return ledger;
    }

    private void Retry(string sessionId)
    {
        if (!pressed.TryGetValue(sessionId, out var ledger)) { releasing.Remove(sessionId); return; }
        foreach (var key in ledger.ToArray())
            if (injector(new RemoteInjectedKeyEvent(key, true))) ledger.Remove(key);
        if (ledger.Count == 0) { pressed.Remove(sessionId); releasing.Remove(sessionId); }
    }
}

public enum RemoteMouseButton { Left, Right }
public readonly record struct RemoteInjectedMouseEvent(RemoteMouseButton? Button, bool IsUp, int X, int Y, int Delta);

public sealed class RemoteMouseLedger(Func<RemoteInjectedMouseEvent, bool> injector)
{
    private readonly Dictionary<string, HashSet<RemoteMouseButton>> pressed = new(StringComparer.Ordinal);
    private readonly HashSet<string> releasing = new(StringComparer.Ordinal);

    public void Send(string sessionId, IReadOnlyList<RemoteInjectedMouseEvent> events)
    {
        if (sessionId.Length == 0 || events.Count == 0) throw new RemoteDesktopUnavailableException("滑鼠工作階段或事件無效。");
        var ledger = GetLedger(sessionId);
        foreach (var item in events)
        {
            if (!injector(item))
            {
                // 每次只送一個原生事件，因此可精確釋放已接受 prefix 中仍按下的按鈕。
                Release(sessionId);
                throw new RemoteDesktopUnavailableException("Windows 未接受滑鼠事件；已進入按鈕釋放流程。");
            }
            if (item.Button is { } button)
            {
                if (item.IsUp) ledger.Remove(button); else ledger.Add(button);
            }
        }
        if (ledger.Count == 0) pressed.Remove(sessionId);
    }

    public void Release(string? sessionId)
    {
        if (string.IsNullOrEmpty(sessionId) || !pressed.ContainsKey(sessionId)) return;
        releasing.Add(sessionId); Retry(sessionId);
    }
    public void ReleaseAll() { foreach (var sessionId in pressed.Keys.ToArray()) releasing.Add(sessionId); RetryPending(); }
    public void RetryPending() { foreach (var sessionId in releasing.ToArray()) Retry(sessionId); }
    public IReadOnlyCollection<RemoteMouseButton> Snapshot(string sessionId) => pressed.TryGetValue(sessionId, out var ledger) ? ledger.ToArray() : [];
    private HashSet<RemoteMouseButton> GetLedger(string sessionId) { if (!pressed.TryGetValue(sessionId, out var ledger)) pressed[sessionId] = ledger = []; return ledger; }
    private void Retry(string sessionId)
    {
        if (!pressed.TryGetValue(sessionId, out var ledger)) { releasing.Remove(sessionId); return; }
        foreach (var button in ledger.ToArray())
            if (injector(new(button, true, 0, 0, 0))) ledger.Remove(button);
        if (ledger.Count == 0) { pressed.Remove(sessionId); releasing.Remove(sessionId); }
    }
}

public static class RemoteDesktopCoordinates
{
    public static (int X, int Y) MapNormalized(double x, double y)
    {
        if (!double.IsFinite(x) || !double.IsFinite(y) || x is < 0 or > 1 || y is < 0 or > 1) throw new RemoteDesktopUnavailableException("滑鼠座標不正確。");
        return ((int)Math.Round(x * 65535), (int)Math.Round(y * 65535));
    }
}

public static class RemoteDpiSafety
{
    public static bool IsPerMonitorV2(bool querySucceeded, bool matchesPerMonitorV2) => querySucceeded && matchesPerMonitorV2;
}

public static class RemoteBrowserTargetSafety
{
    private static readonly HashSet<string> Processes = new(StringComparer.OrdinalIgnoreCase) { "chrome", "msedge" };
    private static readonly HashSet<string> Classes = new(StringComparer.Ordinal) { "Chrome_WidgetWin_1", "Chrome_RenderWidgetHostHWND" };
    public static bool IsKnownBrowser(string processName, string className) => Processes.Contains(processName) && Classes.Contains(className);
}

public interface IRemoteDpiNative
{
    bool SetPerMonitorV2();
    bool IsCurrentPerMonitorV2();
    int LastError { get; }
}

public interface IRemoteDpiBootstrap
{
    bool Ready { get; }
    string Reason { get; }
}

public sealed record RemoteDpiBootstrap(bool Ready, string Reason) : IRemoteDpiBootstrap
{
    public static RemoteDpiBootstrap Initialize(IRemoteDpiNative native)
    {
        try
        {
            if (!native.SetPerMonitorV2()) return new(false, $"SetProcessDpiAwarenessContext failed ({native.LastError}).");
            if (!native.IsCurrentPerMonitorV2()) return new(false, "Process DPI awareness verification failed.");
            return new(true, string.Empty);
        }
        catch (Exception exception) when (exception is DllNotFoundException or EntryPointNotFoundException)
        { return new(false, "Per-Monitor-V2 API is unavailable."); }
    }
}

public sealed class WindowsRemoteDpiNative : IRemoteDpiNative
{
    private static readonly IntPtr PerMonitorV2 = new(-4);
    public int LastError => Marshal.GetLastWin32Error();
    public bool SetPerMonitorV2() => SetProcessDpiAwarenessContext(PerMonitorV2);
    public bool IsCurrentPerMonitorV2()
    {
        var context = GetThreadDpiAwarenessContext();
        return context != IntPtr.Zero && AreDpiAwarenessContextsEqual(context, PerMonitorV2);
    }
    [DllImport("user32.dll", SetLastError = true)] private static extern bool SetProcessDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll")] private static extern IntPtr GetThreadDpiAwarenessContext();
    [DllImport("user32.dll")] private static extern bool AreDpiAwarenessContextsEqual(IntPtr left, IntPtr right);
}

public sealed class WindowsRemoteDesktopService(IRemoteConsoleGuard guard, IRemoteDpiBootstrap dpiBootstrap) : IRemoteDesktopService
{
    private const uint InputMouse = 0, InputKeyboard = 1;
    private const uint KeyEventExtended = 0x0001, KeyEventKeyUp = 0x0002, KeyEventUnicode = 0x0004;
    private const uint MouseMove = 0x0001, MouseLeftDown = 0x0002, MouseLeftUp = 0x0004, MouseRightDown = 0x0008, MouseRightUp = 0x0010;
    private const uint MouseWheel = 0x0800, MouseAbsolute = 0x8000, MouseVirtualDesk = 0x4000;
    private const int SmXVirtualScreen = 76, SmYVirtualScreen = 77, SmCxVirtualScreen = 78, SmCyVirtualScreen = 79;
    private const uint DesktopReadObjects = 0x0001, DesktopSwitchDesktop = 0x0100;
    private static readonly HashSet<string> AllowedFocusClasses = new(StringComparer.Ordinal)
    {
        "Edit", "RichEdit20W", "RichEdit50W", "RICHEDIT50W"
    };
    private static readonly HashSet<ushort> ModifierKeys = [0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5];
    private static readonly Dictionary<string, RemoteInjectedKey> KeyCodes = CreateKeyCodes();
    private readonly SemaphoreSlim captureLock = new(1, 1);
    private readonly object inputLock = new();
    private readonly RemoteInputLedger inputLedger = new(SendKeyEvent);
    private readonly RemoteMouseLedger mouseLedger = new(SendMouseEvent);
    private long generation;
    private FrameBinding? latestFrame;

    public static bool TryResolveKey(string code, out RemoteInjectedKey key) => KeyCodes.TryGetValue(code, out key);

    public RemoteDesktopAvailability GetAvailability()
    {
        try
        {
            var requireInputTarget = guard.TryRead(DateTimeOffset.UtcNow, out var enablement) &&
                enablement.Capabilities.Any(capability => capability is RemoteCapability.Text or RemoteCapability.Keyboard or RemoteCapability.Mouse);
            EnsureInteractiveSession(requireInputTarget);
            var width = GetSystemMetrics(SmCxVirtualScreen); var height = GetSystemMetrics(SmCyVirtualScreen);
            if (width <= 0 || height <= 0 || (long)width * height > 40_000_000) throw new RemoteDesktopUnavailableException("DESKTOP_GEOMETRY_INVALID：互動式桌面範圍不符合安全限制。");
            _ = GetTopologyHash();
            return new(true, string.Empty);
        }
        catch (RemoteDesktopUnavailableException exception) { return new(false, exception.Message); }
    }

    public async Task<RemoteDesktopFrame> CaptureJpegAsync(CancellationToken cancellationToken)
    {
        if (!await captureLock.WaitAsync(0, cancellationToken)) throw new RemoteDesktopUnavailableException("已有畫面擷取正在執行。");
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            EnsureCapability(RemoteCapability.Screen);
            var foreground = EnsureInteractiveSession(false);
            var left = GetSystemMetrics(SmXVirtualScreen); var top = GetSystemMetrics(SmYVirtualScreen);
            var width = GetSystemMetrics(SmCxVirtualScreen); var height = GetSystemMetrics(SmCyVirtualScreen);
            if (width <= 0 || height <= 0 || (long)width * height > 40_000_000) throw new RemoteDesktopUnavailableException("互動式桌面範圍不符合安全限制。");
            var topologyHash = GetTopologyHash();
            var scale = Math.Min(1d, Math.Min(1280d / width, 720d / height));
            var targetWidth = Math.Max(1, (int)Math.Round(width * scale)); var targetHeight = Math.Max(1, (int)Math.Round(height * scale));
            using var source = new Bitmap(width, height, PixelFormat.Format24bppRgb);
            using (var graphics = Graphics.FromImage(source)) graphics.CopyFromScreen(left, top, 0, 0, new Size(width, height), CopyPixelOperation.SourceCopy);
            using var output = new Bitmap(targetWidth, targetHeight, PixelFormat.Format24bppRgb);
            using (var graphics = Graphics.FromImage(output)) { graphics.CompositingMode = CompositingMode.SourceCopy; graphics.InterpolationMode = InterpolationMode.HighQualityBilinear; graphics.DrawImage(source, 0, 0, targetWidth, targetHeight); }
            using var stream = new MemoryStream();
            var codec = ImageCodecInfo.GetImageEncoders().Single(item => item.FormatID == ImageFormat.Jpeg.Guid);
            using var parameters = new EncoderParameters(1); parameters.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, 55L); output.Save(stream, codec, parameters);
            var jpeg = stream.ToArray();
            if (jpeg.Length > 1_572_864) throw new RemoteDesktopUnavailableException("畫面超過安全大小限制。");
            if (!StringComparer.Ordinal.Equals(topologyHash, GetTopologyHash())) throw new RemoteDesktopUnavailableException("擷取期間顯示器拓樸已變更。");
            var currentGeneration = Interlocked.Increment(ref generation); var capturedAt = DateTimeOffset.UtcNow;
            latestFrame = new FrameBinding(currentGeneration, capturedAt, left, top, width, height, foreground, topologyHash);
            return new(jpeg, currentGeneration, capturedAt, targetWidth, targetHeight);
        }
        finally { captureLock.Release(); }
    }

    public Task SendTextAsync(string sessionId, string text, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        EnsureCapability(RemoteCapability.Text);
        lock (inputLock)
        {
            var foreground = EnsureInteractiveSession(true); EnsureNoPhysicalModifiers();
            if (GetForegroundWindow() != foreground) throw new RemoteDesktopUnavailableException("前景視窗已變更。");
            var events = new List<RemoteInjectedKeyEvent>(text.Length * 2);
            foreach (var character in text) { var key = new RemoteInjectedKey(0, character, true, false); events.Add(new(key, false)); events.Add(new(key, true)); }
            inputLedger.Send(sessionId, events);
        }
        return Task.CompletedTask;
    }

    public Task SendKeyboardAsync(string sessionId, IReadOnlyList<RemoteKeyStroke> strokes, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        EnsureCapability(RemoteCapability.Keyboard);
        if (strokes.Count is < 1 or > 12) throw new RemoteDesktopUnavailableException("按鍵批次大小不正確。");
        lock (inputLock)
        {
            var foreground = EnsureInteractiveSession(true); EnsureNoPhysicalModifiers(inputLedger.Snapshot(sessionId).Where(key => !key.Unicode).Select(key => key.VirtualKey).ToHashSet());
            var events = new List<RemoteInjectedKeyEvent>(strokes.Count * 2);
            foreach (var stroke in strokes)
            {
                if (!TryResolveKey(stroke.Code, out var key)) throw new RemoteDesktopUnavailableException("不支援此按鍵代碼。");
                switch (stroke.Action)
                {
                    case "down": events.Add(new(key, false)); break;
                    case "up": events.Add(new(key, true)); break;
                    case "press" when !ModifierKeys.Contains(key.VirtualKey): events.Add(new(key, false)); events.Add(new(key, true)); break;
                    default: throw new RemoteDesktopUnavailableException("不支援此按鍵動作。");
                }
            }
            if (GetForegroundWindow() != foreground) throw new RemoteDesktopUnavailableException("前景視窗已變更。");
            inputLedger.Send(sessionId, events);
        }
        return Task.CompletedTask;
    }

    public Task SendMouseAsync(string sessionId, RemoteMouseAction action, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        EnsureCapability(RemoteCapability.Mouse);
        lock (inputLock)
        {
            var foreground = EnsureInteractiveSession(true); EnsureNoPhysicalModifiers(); var frame = latestFrame;
            if (frame is null || frame.Generation != action.FrameGeneration || DateTimeOffset.UtcNow - frame.CapturedAt > TimeSpan.FromSeconds(2) || foreground != frame.Foreground) throw new RemoteDesktopUnavailableException("畫面座標已過期。");
            if (GetSystemMetrics(SmXVirtualScreen) != frame.Left || GetSystemMetrics(SmYVirtualScreen) != frame.Top || GetSystemMetrics(SmCxVirtualScreen) != frame.Width || GetSystemMetrics(SmCyVirtualScreen) != frame.Height) throw new RemoteDesktopUnavailableException("桌面幾何已變更。");
            if (!CryptographicOperations.FixedTimeEquals(Convert.FromHexString(frame.TopologyHash), Convert.FromHexString(GetTopologyHash()))) throw new RemoteDesktopUnavailableException("顯示器拓樸已變更。");
            var coordinates = RemoteDesktopCoordinates.MapNormalized(action.X, action.Y);
            var move = new RemoteInjectedMouseEvent(null, false, coordinates.X, coordinates.Y, 0);
            RemoteInjectedMouseEvent[] events = action.Action switch
            {
                "move" => [move], "leftClick" => [move, new(RemoteMouseButton.Left, false, 0, 0, 0), new(RemoteMouseButton.Left, true, 0, 0, 0)],
                "rightClick" => [move, new(RemoteMouseButton.Right, false, 0, 0, 0), new(RemoteMouseButton.Right, true, 0, 0, 0)],
                "wheel" when action.Delta is >= -1200 and <= 1200 and not 0 => [move, new(null, false, 0, 0, action.Delta)],
                _ => throw new RemoteDesktopUnavailableException("不支援此滑鼠動作。")
            };
            if (GetForegroundWindow() != foreground) throw new RemoteDesktopUnavailableException("前景視窗已變更。");
            mouseLedger.Send(sessionId, events);
        }
        return Task.CompletedTask;
    }

    public void ReleaseInjectedModifiers(string? sessionId) { lock (inputLock) { inputLedger.Release(sessionId); mouseLedger.Release(sessionId); } }
    public void ReleaseAllInjectedModifiers() { lock (inputLock) { inputLedger.ReleaseAll(); mouseLedger.ReleaseAll(); } }
    public void RetryPendingReleases() { lock (inputLock) { inputLedger.RetryPending(); mouseLedger.RetryPending(); } }

    private IntPtr EnsureInteractiveSession(bool requireInputTarget)
    {
        if (!dpiBootstrap.Ready) throw new RemoteDesktopUnavailableException($"DPI_BOOTSTRAP_UNAVAILABLE：{dpiBootstrap.Reason}");
        if (!OperatingSystem.IsWindows()) throw new RemoteDesktopUnavailableException("WINDOWS_REQUIRED：遠端桌面僅支援 Windows。");
        if (!Environment.UserInteractive) throw new RemoteDesktopUnavailableException("PROCESS_NOT_INTERACTIVE：網站程序不是互動式程序。");
        var processSession = Process.GetCurrentProcess().SessionId;
        if (processSession == 0) throw new RemoteDesktopUnavailableException("SESSION_ZERO：網站程序位於非互動 Session 0。");
        if (WTSGetActiveConsoleSessionId() != processSession) throw new RemoteDesktopUnavailableException("CONSOLE_SESSION_MISMATCH：網站程序不在目前登入的主控台工作階段。");
        if (IsProcessElevated()) throw new RemoteDesktopUnavailableException("PROCESS_TOKEN_UNSAFE：網站程序為 elevated、UIAccess 或無法驗證的權杖。");
        try
        {
            var context = GetThreadDpiAwarenessContext();
            if (!RemoteDpiSafety.IsPerMonitorV2(context != IntPtr.Zero, context != IntPtr.Zero && AreDpiAwarenessContextsEqual(context, new IntPtr(-4))))
                throw new RemoteDesktopUnavailableException("DPI_THREAD_MISMATCH：程序未使用 Per-Monitor-V2 實體座標模式。");
        }
        catch (Exception exception) when (exception is DllNotFoundException or EntryPointNotFoundException)
        { throw new RemoteDesktopUnavailableException("DPI_API_UNAVAILABLE：無法驗證 Per-Monitor-V2 DPI 模式。"); }
        var desktop = OpenInputDesktop(0, false, DesktopReadObjects | DesktopSwitchDesktop); if (desktop == IntPtr.Zero) throw new RemoteDesktopUnavailableException("INPUT_DESKTOP_UNAVAILABLE：輸入桌面不可用。");
        try { if (!GetDesktopName(desktop).Equals("Default", StringComparison.Ordinal)) throw new RemoteDesktopUnavailableException("SECURE_DESKTOP_ACTIVE：目前不是 Default 輸入桌面。"); } finally { CloseDesktop(desktop); }
        var foreground = GetForegroundWindow(); if (foreground == IntPtr.Zero) throw new RemoteDesktopUnavailableException("FOREGROUND_UNAVAILABLE：沒有可驗證的前景視窗。");
        _ = GetWindowThreadProcessId(foreground, out var processId);
        try { if (processId == 0 || Process.GetProcessById((int)processId).SessionId != processSession || IsProcessElevated(processId)) throw new RemoteDesktopUnavailableException("FOREGROUND_TOKEN_UNSAFE：前景視窗工作階段或權限不安全。"); } catch (ArgumentException) { throw new RemoteDesktopUnavailableException("FOREGROUND_CLOSED：前景視窗已關閉。"); }
        if (requireInputTarget) EnsureAllowedFocusTarget(foreground);
        return foreground;
    }
    private void EnsureCapability(RemoteCapability capability)
    {
        if (!guard.TryRead(DateTimeOffset.UtcNow, out var enablement) || !enablement.Capabilities.Contains(capability))
            throw new RemoteDesktopUnavailableException("本機遠端控制能力目前為關閉狀態。");
    }

    private void EnsureAllowedFocusTarget(IntPtr foreground)
    {
        var thread = GetWindowThreadProcessId(foreground, out var processId); var info = new GUITHREADINFO { cbSize = Marshal.SizeOf<GUITHREADINFO>() };
        if (!GetGUIThreadInfo(thread, ref info) || info.hwndFocus == IntPtr.Zero) throw new RemoteDesktopUnavailableException("FOREGROUND_FOCUS_UNAVAILABLE：無法確認輸入目標。");
        var className = new StringBuilder(256); if (GetClassName(info.hwndFocus, className, className.Capacity) <= 0) throw new RemoteDesktopUnavailableException("FOREGROUND_TARGET_UNSUPPORTED：無法辨識目前前景控制項。");
        if (!AllowedFocusClasses.Contains(className.ToString()))
        {
            string processName;
            try { processName = Process.GetProcessById((int)processId).ProcessName; }
            catch (ArgumentException) { throw new RemoteDesktopUnavailableException("FOREGROUND_CLOSED：前景視窗已關閉。"); }
            if (!RemoteBrowserTargetSafety.IsKnownBrowser(processName, className.ToString())) throw new RemoteDesktopUnavailableException("FOREGROUND_TARGET_UNSUPPORTED：目前前景控制項不在安全允許清單。");
            if (!guard.TryRead(DateTimeOffset.UtcNow, out var enablement) || !enablement.Capabilities.Contains(RemoteCapability.BrowserInput))
                throw new RemoteDesktopUnavailableException("BROWSER_INPUT_CONFIRMATION_REQUIRED：Chrome 或 Edge 輸入需要額外 browser.input 本機能力。");
        }
        var style = GetWindowLongPtr(info.hwndFocus, -16).ToInt64(); if ((style & 0x20) != 0) throw new RemoteDesktopUnavailableException("PASSWORD_TARGET_BLOCKED：密碼欄位不允許遠端輸入。");
    }
    private static void EnsureNoPhysicalModifiers(IReadOnlySet<ushort>? injected = null) { foreach (var key in ModifierKeys) if ((injected is null || !injected.Contains(key)) && (GetAsyncKeyState(key) & 0x8000) != 0) throw new RemoteDesktopUnavailableException("實體修飾鍵目前按下。"); }
    private static bool SendKeyEvent(RemoteInjectedKeyEvent item)
    {
        var input = item.Key.Unicode ? UnicodeInput(item.Key.UnicodeCharacter, item.IsUp) : KeyInput(item.Key.VirtualKey, item.IsUp, item.Key.Extended);
        return SendInput(1, [input], Marshal.SizeOf<INPUT>()) == 1;
    }
    private static bool SendMouseEvent(RemoteInjectedMouseEvent item)
    {
        var flags = item.Button switch
        {
            RemoteMouseButton.Left => item.IsUp ? MouseLeftUp : MouseLeftDown,
            RemoteMouseButton.Right => item.IsUp ? MouseRightUp : MouseRightDown,
            _ when item.Delta != 0 => MouseWheel,
            _ => MouseMove | MouseAbsolute | MouseVirtualDesk
        };
        var data = item.Delta == 0 ? 0u : unchecked((uint)item.Delta);
        var input = MouseInput(item.X, item.Y, flags, data);
        return SendInput(1, [input], Marshal.SizeOf<INPUT>()) == 1;
    }
    private static INPUT UnicodeInput(char value, bool up) => new() { type = InputKeyboard, U = new InputUnion { ki = new KEYBDINPUT { wScan = value, dwFlags = KeyEventUnicode | (up ? KeyEventKeyUp : 0) } } };
    private static INPUT KeyInput(ushort key, bool up, bool extended) => new() { type = InputKeyboard, U = new InputUnion { ki = new KEYBDINPUT { wVk = key, dwFlags = (up ? KeyEventKeyUp : 0) | (extended ? KeyEventExtended : 0) } } };
    private static INPUT MouseInput(int x, int y, uint flags, uint data) => new() { type = InputMouse, U = new InputUnion { mi = new MOUSEINPUT { dx = x, dy = y, dwFlags = flags, mouseData = data } } };
    private static Dictionary<string, RemoteInjectedKey> CreateKeyCodes()
    {
        var result = new Dictionary<string, RemoteInjectedKey>(StringComparer.Ordinal);
        static RemoteInjectedKey Key(ushort value, bool extended = false) => new(value, '\0', false, extended);
        for (var value = 0; value < 26; value++) result[$"Key{(char)('A' + value)}"] = Key((ushort)(0x41 + value));
        for (var value = 0; value < 10; value++) { result[$"Digit{value}"] = Key((ushort)(0x30 + value)); result[$"Numpad{value}"] = Key((ushort)(0x60 + value)); }
        for (var value = 1; value <= 24; value++) result[$"F{value}"] = Key((ushort)(0x6F + value));
        foreach (var item in new Dictionary<string, ushort> { ["Backspace"] = 0x08, ["Tab"] = 0x09, ["Enter"] = 0x0D, ["ShiftLeft"] = 0xA0, ["ShiftRight"] = 0xA1, ["ControlLeft"] = 0xA2, ["AltLeft"] = 0xA4, ["Pause"] = 0x13, ["CapsLock"] = 0x14, ["Escape"] = 0x1B, ["Space"] = 0x20, ["NumpadMultiply"] = 0x6A, ["NumpadAdd"] = 0x6B, ["NumpadSubtract"] = 0x6D, ["NumpadDecimal"] = 0x6E, ["ScrollLock"] = 0x91, ["Semicolon"] = 0xBA, ["Equal"] = 0xBB, ["Comma"] = 0xBC, ["Minus"] = 0xBD, ["Period"] = 0xBE, ["Slash"] = 0xBF, ["Backquote"] = 0xC0, ["BracketLeft"] = 0xDB, ["Backslash"] = 0xDC, ["BracketRight"] = 0xDD, ["Quote"] = 0xDE }) result[item.Key] = Key(item.Value);
        foreach (var item in new Dictionary<string, ushort> { ["ControlRight"] = 0xA3, ["AltRight"] = 0xA5, ["PageUp"] = 0x21, ["PageDown"] = 0x22, ["End"] = 0x23, ["Home"] = 0x24, ["ArrowLeft"] = 0x25, ["ArrowUp"] = 0x26, ["ArrowRight"] = 0x27, ["ArrowDown"] = 0x28, ["Insert"] = 0x2D, ["Delete"] = 0x2E, ["MetaLeft"] = 0x5B, ["MetaRight"] = 0x5C, ["ContextMenu"] = 0x5D, ["NumpadEnter"] = 0x0D, ["NumpadDivide"] = 0x6F, ["NumLock"] = 0x90, ["PrintScreen"] = 0x2C, ["BrowserBack"] = 0xA6, ["BrowserForward"] = 0xA7, ["BrowserRefresh"] = 0xA8, ["BrowserStop"] = 0xA9, ["BrowserSearch"] = 0xAA, ["BrowserFavorites"] = 0xAB, ["BrowserHome"] = 0xAC, ["AudioVolumeMute"] = 0xAD, ["AudioVolumeDown"] = 0xAE, ["AudioVolumeUp"] = 0xAF, ["MediaTrackNext"] = 0xB0, ["MediaTrackPrevious"] = 0xB1, ["MediaStop"] = 0xB2, ["MediaPlayPause"] = 0xB3, ["LaunchMail"] = 0xB4, ["MediaSelect"] = 0xB5, ["LaunchApp1"] = 0xB6, ["LaunchApp2"] = 0xB7 }) result[item.Key] = Key(item.Value, true);
        return result;
    }
    private static string GetDesktopName(IntPtr desktop) { _ = GetUserObjectInformation(desktop, 2, IntPtr.Zero, 0, out var needed); if (needed == 0) return string.Empty; var buffer = Marshal.AllocHGlobal((int)needed); try { return GetUserObjectInformation(desktop, 2, buffer, needed, out _) ? Marshal.PtrToStringUni(buffer) ?? string.Empty : string.Empty; } finally { Marshal.FreeHGlobal(buffer); } }
    private static bool IsProcessElevated(uint processId = 0)
    {
        var process = processId == 0 ? GetCurrentProcessHandle() : OpenProcess(0x1000, false, processId);
        if (process == IntPtr.Zero) return true;
        if (!OpenProcessToken(process, 0x0008, out var token)) { if (processId != 0) CloseHandle(process); return true; }
        try
        {
            var elevation = new TOKEN_ELEVATION();
            var elevationRead = GetTokenInformation(token, 20, ref elevation, Marshal.SizeOf<TOKEN_ELEVATION>(), out _);
            // UIAccess 可跨越一般桌面完整性邊界；遠端輸入程序與目標均不得具備此權杖能力。
            var uiAccessRead = GetTokenInformationUiAccess(token, 26, out var uiAccess, sizeof(uint), out _);
            return !RemoteTokenSafety.IsSafe(elevationRead, elevation.TokenIsElevated != 0, uiAccessRead, uiAccess != 0);
        }
        finally { CloseHandle(token); if (processId != 0) CloseHandle(process); }
    }
    private static string GetTopologyHash()
    {
        var monitors = new List<RemoteMonitorDescriptor>();
        MonitorEnumProc callback = (monitor, _, _, _) =>
        {
            var info = new MONITORINFOEX { cbSize = Marshal.SizeOf<MONITORINFOEX>(), szDevice = string.Empty };
            if (!GetMonitorInfo(monitor, ref info) || GetDpiForMonitor(monitor, 0, out var dpiX, out var dpiY) != 0) return false;
            var mode = new DEVMODE { dmSize = (ushort)Marshal.SizeOf<DEVMODE>(), dmDeviceName = string.Empty, dmFormName = string.Empty };
            if (!EnumDisplaySettings(info.szDevice, -1, ref mode)) return false;
            monitors.Add(new(info.szDevice, info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom, dpiX, dpiY, mode.dmDisplayOrientation, (info.dwFlags & 1) != 0));
            return true;
        };
        try
        {
            if (!EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, callback, IntPtr.Zero)) throw new RemoteDesktopUnavailableException("無法確認顯示器拓樸。");
            return RemoteDisplayTopology.Hash(monitors);
        }
        catch (Exception exception) when (exception is DllNotFoundException or EntryPointNotFoundException)
        { throw new RemoteDesktopUnavailableException("無法確認顯示器 DPI 拓樸。"); }
    }
    private sealed record FrameBinding(long Generation, DateTimeOffset CapturedAt, int Left, int Top, int Width, int Height, IntPtr Foreground, string TopologyHash);
    [StructLayout(LayoutKind.Sequential)] private struct INPUT { public uint type; public InputUnion U; }
    [StructLayout(LayoutKind.Explicit)] private struct InputUnion { [FieldOffset(0)] public KEYBDINPUT ki; [FieldOffset(0)] public MOUSEINPUT mi; }
    [StructLayout(LayoutKind.Sequential)] private struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public UIntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] private struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public UIntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] private struct GUITHREADINFO { public int cbSize; public uint flags; public IntPtr hwndActive, hwndFocus, hwndCapture, hwndMenuOwner, hwndMoveSize, hwndCaret; public RECT rcCaret; }
    [StructLayout(LayoutKind.Sequential)] private struct RECT { public int left, top, right, bottom; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] private struct MONITORINFOEX { public int cbSize; public RECT rcMonitor, rcWork; public uint dwFlags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szDevice; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] private struct DEVMODE
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;
        public ushort dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra; public uint dmFields;
        public int dmPositionX, dmPositionY; public uint dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;
        public ushort dmLogPixels; public uint dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }
    [StructLayout(LayoutKind.Sequential)] private struct TOKEN_ELEVATION { public int TokenIsElevated; }
    [DllImport("kernel32.dll")] private static extern uint WTSGetActiveConsoleSessionId();
    [DllImport("kernel32.dll", EntryPoint = "GetCurrentProcess")] private static extern IntPtr GetCurrentProcessHandle();
    [DllImport("kernel32.dll", SetLastError = true)] private static extern IntPtr OpenProcess(uint access, bool inherit, uint processId);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    [DllImport("advapi32.dll", SetLastError = true)] private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true)] private static extern bool GetTokenInformation(IntPtr token, int infoClass, ref TOKEN_ELEVATION info, int length, out int returnLength);
    [DllImport("advapi32.dll", EntryPoint = "GetTokenInformation", SetLastError = true)] private static extern bool GetTokenInformationUiAccess(IntPtr token, int infoClass, out uint info, int length, out int returnLength);
    [DllImport("user32.dll")] private static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint access);
    [DllImport("user32.dll")] private static extern bool CloseDesktop(IntPtr desktop);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern bool GetUserObjectInformation(IntPtr handle, int index, IntPtr info, uint length, out uint needed);
    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    [DllImport("user32.dll")] private static extern bool GetGUIThreadInfo(uint threadId, ref GUITHREADINFO info);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr window, StringBuilder className, int maximum);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] private static extern IntPtr GetWindowLongPtr(IntPtr window, int index);
    [DllImport("user32.dll")] private static extern short GetAsyncKeyState(int key);
    [DllImport("user32.dll")] private static extern int GetSystemMetrics(int index);
    [DllImport("user32.dll")] private static extern IntPtr GetThreadDpiAwarenessContext();
    [DllImport("user32.dll")] private static extern bool AreDpiAwarenessContextsEqual(IntPtr left, IntPtr right);
    private delegate bool MonitorEnumProc(IntPtr monitor, IntPtr deviceContext, IntPtr rectangle, IntPtr data);
    [DllImport("user32.dll")] private static extern bool EnumDisplayMonitors(IntPtr deviceContext, IntPtr clip, MonitorEnumProc callback, IntPtr data);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern bool GetMonitorInfo(IntPtr monitor, ref MONITORINFOEX info);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern bool EnumDisplaySettings(string deviceName, int modeNumber, ref DEVMODE mode);
    [DllImport("shcore.dll")] private static extern int GetDpiForMonitor(IntPtr monitor, int dpiType, out uint dpiX, out uint dpiY);
    [DllImport("user32.dll", SetLastError = true)] private static extern uint SendInput(uint count, INPUT[] inputs, int size);
}

public interface IRemoteShellBroker { Task<RemoteShellResult> ExecuteAsync(string sessionId, string command, CancellationToken cancellationToken); }
public sealed record RemoteShellResult(int ExitCode, string Output, bool Truncated);
public sealed class UnavailableRemoteShellBroker : IRemoteShellBroker
{
    public Task<RemoteShellResult> ExecuteAsync(string sessionId, string command, CancellationToken cancellationToken) => throw new RemoteDesktopUnavailableException("獨立低權限 Shell broker 尚未完成安全驗證。");
}
#pragma warning restore CA1416
