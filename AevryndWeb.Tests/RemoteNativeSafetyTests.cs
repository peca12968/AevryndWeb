using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class RemoteNativeSafetyTests
{
    [Fact]
    public void PartialPrefixImmediatelyReleasesEveryAcceptedKeyDown()
    {
        var calls = new List<RemoteInjectedKeyEvent>();
        var a = new RemoteInjectedKey(0x41, '\0', false, false);
        var b = new RemoteInjectedKey(0x42, '\0', false, false);
        var ledger = new RemoteInputLedger(item => { calls.Add(item); return calls.Count != 2; });

        Assert.Throws<RemoteDesktopUnavailableException>(() => ledger.Send("session", [new(a, false), new(b, false)]));

        Assert.Equal([new(a, false), new(b, false), new(a, true)], calls);
        Assert.Empty(ledger.Snapshot("session"));
    }

    [Fact]
    public void FailedReleaseRemainsInLedgerUntilRetrySucceeds()
    {
        var releaseAttempts = 0;
        var key = new RemoteInjectedKey(0x41, '\0', false, false);
        var ledger = new RemoteInputLedger(item => !item.IsUp || ++releaseAttempts >= 2);
        ledger.Send("session", [new(key, false)]);

        ledger.Release("session");
        Assert.Single(ledger.Snapshot("session"));
        ledger.RetryPending();

        Assert.Empty(ledger.Snapshot("session"));
        Assert.Equal(2, releaseAttempts);
    }

    [Fact]
    public void UnicodePartialKeyUpIsTrackedAndPreciselyReleased()
    {
        var calls = new List<RemoteInjectedKeyEvent>();
        var key = new RemoteInjectedKey(0, '測', true, false);
        var ledger = new RemoteInputLedger(item => { calls.Add(item); return calls.Count != 2; });

        Assert.Throws<RemoteDesktopUnavailableException>(() => ledger.Send("session", [new(key, false), new(key, true)]));

        Assert.Equal([new(key, false), new(key, true), new(key, true)], calls);
        Assert.Empty(ledger.Snapshot("session"));
    }

    [Fact]
    public void MousePartialClickPrefixImmediatelyReleasesAcceptedButtonDown()
    {
        var calls = new List<RemoteInjectedMouseEvent>();
        var move = new RemoteInjectedMouseEvent(null, false, 32768, 32768, 0);
        var down = new RemoteInjectedMouseEvent(RemoteMouseButton.Left, false, 0, 0, 0);
        var up = new RemoteInjectedMouseEvent(RemoteMouseButton.Left, true, 0, 0, 0);
        var ledger = new RemoteMouseLedger(item => { calls.Add(item); return calls.Count != 3; });

        Assert.Throws<RemoteDesktopUnavailableException>(() => ledger.Send("session", [move, down, up]));

        Assert.Equal([move, down, up, up], calls);
        Assert.Empty(ledger.Snapshot("session"));
    }

    [Fact]
    public void MouseDownThenUpRemovesButtonOnlyAfterSuccessfulUp()
    {
        var ledger = new RemoteMouseLedger(_ => true);
        ledger.Send("session", [new(RemoteMouseButton.Left, false, 0, 0, 0)]);
        Assert.Contains(RemoteMouseButton.Left, ledger.Snapshot("session"));
        ledger.Send("session", [new(RemoteMouseButton.Left, true, 0, 0, 0)]);
        Assert.Empty(ledger.Snapshot("session"));
    }

    [Fact]
    public void MouseReleaseFailureStaysTrackedUntilRetry()
    {
        var releaseAttempts = 0;
        var down = new RemoteInjectedMouseEvent(RemoteMouseButton.Right, false, 0, 0, 0);
        var ledger = new RemoteMouseLedger(item => item.Button != RemoteMouseButton.Right || !item.IsUp || ++releaseAttempts >= 2);
        ledger.Send("session", [down]);

        ledger.Release("session");
        Assert.Single(ledger.Snapshot("session"));
        ledger.RetryPending();

        Assert.Empty(ledger.Snapshot("session"));
        Assert.Equal(2, releaseAttempts);
    }

    [Theory]
    [InlineData(true, false, true, false, true)]
    [InlineData(true, true, true, false, false)]
    [InlineData(true, false, true, true, false)]
    [InlineData(false, false, true, false, false)]
    [InlineData(true, false, false, false, false)]
    public void TokenSafetyRejectsElevationUiAccessAndUnknownQueries(bool elevationRead, bool elevated, bool uiRead, bool uiAccess, bool expected) =>
        Assert.Equal(expected, RemoteTokenSafety.IsSafe(elevationRead, elevated, uiRead, uiAccess));

    [Fact]
    public void DpiContractAndNormalizedCoordinatesUsePhysicalVirtualDesktopSpace()
    {
        Assert.True(RemoteDpiSafety.IsPerMonitorV2(true, true));
        Assert.False(RemoteDpiSafety.IsPerMonitorV2(true, false));
        Assert.False(RemoteDpiSafety.IsPerMonitorV2(false, true));
        Assert.Equal((0, 0), RemoteDesktopCoordinates.MapNormalized(0, 0));
        Assert.Equal((65535, 65535), RemoteDesktopCoordinates.MapNormalized(1, 1));
        Assert.Equal((32768, 32768), RemoteDesktopCoordinates.MapNormalized(.5, .5));
        Assert.Throws<RemoteDesktopUnavailableException>(() => RemoteDesktopCoordinates.MapNormalized(double.NaN, .5));
    }

    [Fact]
    public void DisplayTopologyHashChangesForDpiRotationOrBounds()
    {
        var baseline = new[] { new RemoteMonitorDescriptor("DISPLAY1", 0, 0, 1920, 1080, 96, 96, 0, true) };
        var dpi = new[] { baseline[0] with { DpiX = 144, DpiY = 144 } };
        var rotation = new[] { baseline[0] with { Rotation = 1 } };
        var bounds = new[] { baseline[0] with { Right = 1080, Bottom = 1920 } };

        Assert.NotEqual(RemoteDisplayTopology.Hash(baseline), RemoteDisplayTopology.Hash(dpi));
        Assert.NotEqual(RemoteDisplayTopology.Hash(baseline), RemoteDisplayTopology.Hash(rotation));
        Assert.NotEqual(RemoteDisplayTopology.Hash(baseline), RemoteDisplayTopology.Hash(bounds));
    }

    [Theory]
    [InlineData("ControlRight")]
    [InlineData("AltRight")]
    [InlineData("NumpadEnter")]
    [InlineData("NumpadDivide")]
    [InlineData("NumLock")]
    [InlineData("PrintScreen")]
    [InlineData("BrowserBack")]
    [InlineData("MediaPlayPause")]
    public void EnhancedKeysAlwaysCarryExtendedFlag(string code)
    {
        Assert.True(WindowsRemoteDesktopService.TryResolveKey(code, out var key));
        Assert.True(key.Extended);
    }
}
