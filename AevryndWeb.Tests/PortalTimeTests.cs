using AevryndWeb.Security;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class PortalTimeTests
{
    [Theory]
    [InlineData("2026-09-05T00:00:00Z", "2026-09-05 08:00:00 台北時間 (UTC+8)")]
    [InlineData("2026-09-05T15:59:59Z", "2026-09-05 23:59:59 台北時間 (UTC+8)")]
    [InlineData("2026-09-05T16:00:00Z", "2026-09-06 00:00:00 台北時間 (UTC+8)")]
    [InlineData("2026-12-31T23:59:59Z", "2027-01-01 07:59:59 台北時間 (UTC+8)")]
    public void DisplayChangesDateAtTaipeiMidnightWithoutChangingInstant(string source, string expected)
    {
        var instant = DateTimeOffset.Parse(source, System.Globalization.CultureInfo.InvariantCulture);
        var epoch = instant.ToUnixTimeMilliseconds();
        Assert.Equal(expected, PortalTime.Format(instant));
        Assert.Equal(epoch, instant.ToUnixTimeMilliseconds());
    }

    [Fact]
    public void MissingTimeRemainsUnavailable() => Assert.Equal("unavailable", PortalTime.Format(null));
}
