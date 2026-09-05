using System.Globalization;

namespace AevryndWeb.Security;

public static class PortalTime
{
    private static readonly TimeZoneInfo Taipei = TimeZoneInfo.FindSystemTimeZoneById("Asia/Taipei");
    private static readonly CultureInfo Culture = CultureInfo.GetCultureInfo("zh-TW");

    // 僅轉換畫面文字；來源時間、簽章及排序仍保留原始時刻。
    public static string Format(DateTimeOffset? value) => value.HasValue
        ? TimeZoneInfo.ConvertTime(value.Value, Taipei).ToString("yyyy-MM-dd HH:mm:ss", Culture) + " 台北時間 (UTC+8)"
        : "unavailable";
}
