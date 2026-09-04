using System.Collections.Concurrent;
using System.Net;
using System.Net.Mail;
using System.Security.Cryptography;
using System.Text;

namespace AevryndWeb.Security;

public static class PortalIdentity
{
    // 登入白名單與角色；資料庫也以相同的 email/role 種子資料維護。
    public const string AllowedEmail = "slime12968@gmail.com";
    public const string AdminRole = "Admin";
    public const string UserRole = "User";
    private static readonly IReadOnlyDictionary<string, string> Accounts = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
    {
        ["slime12968@gmail.com"] = AdminRole,
        ["peca12968@gmail.com"] = AdminRole,
        ["en531@livemail.tw"] = UserRole,
        ["tokkinjoey@gmail.com"] = UserRole,
        ["geminjjj@gmail.com"] = UserRole
    };
    public static IReadOnlyCollection<string> AllowedEmails => Accounts.Keys.ToArray();
    public static bool IsAllowed(string email) => Accounts.ContainsKey(Normalize(email));
    public static bool IsAdmin(string email) => Accounts.TryGetValue(Normalize(email), out var role) && role == AdminRole;
    public static string? RoleFor(string email) => Accounts.TryGetValue(Normalize(email), out var role) ? role : null;
    public const string PortalOwnerPolicy = "PortalOwner";
    public const string AdminPolicy = "PortalAdmin";
    public const string OperationsPolicy = "PortalOperations";
    public static string CapabilityPolicy(RemoteCapability capability) => $"RemoteConsole:{capability}";
    private static string Normalize(string value) => (value ?? string.Empty).Trim().ToLowerInvariant();
}

public interface IOtpService
{
    Task RequestAsync(string email, string clientKey, CancellationToken cancellationToken);
    bool Verify(string email, string code, string clientKey);
}

public interface IEmailSender
{
    bool IsReady { get; }
    Task SendAsync(string recipient, string code, CancellationToken cancellationToken);
}

public sealed class OtpService(IEmailSender sender) : IOtpService
{
    private const string Alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    private readonly ConcurrentDictionary<string, Record> records = new();
    private readonly ConcurrentDictionary<string, DateTimeOffset> cooldowns = new();
    private readonly ConcurrentDictionary<string, Window> requestLimits = new();
    private readonly ConcurrentDictionary<string, Window> verifyLimits = new();
    private readonly object globalLimitLock = new();
    private Window globalRequestLimit = new(DateTimeOffset.MinValue, 0);
    private Window globalVerifyLimit = new(DateTimeOffset.MinValue, 0);

    public async Task RequestAsync(string email, string clientKey, CancellationToken cancellationToken)
    {
        var normalized = Normalize(email);
        if (!PortalIdentity.IsAllowed(normalized)) return;
        PruneAndBound(requestLimits, DateTimeOffset.UtcNow);
        EnforceGlobalLimit(ref globalRequestLimit, 100, TimeSpan.FromMinutes(10));
        EnforceLimit(requestLimits, "ip:" + clientKey, 10, TimeSpan.FromMinutes(10));
        EnforceLimit(requestLimits, "account:" + HashKey(normalized), 5, TimeSpan.FromMinutes(10));
        var now = DateTimeOffset.UtcNow;
        if (cooldowns.TryGetValue(HashKey(normalized), out var next) && next > now) throw new OtpRejectedException();
        cooldowns[HashKey(normalized)] = now.AddSeconds(60);

        var code = string.Create(8, 0, (span, _) => { for (var i = 0; i < span.Length; i++) span[i] = Alphabet[RandomNumberGenerator.GetInt32(Alphabet.Length)]; });
        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Rfc2898DeriveBytes.Pbkdf2(code, salt, 120_000, HashAlgorithmName.SHA256, 32);
        await sender.SendAsync(normalized, code, cancellationToken);
        records[normalized] = new Record(salt, hash, now.AddMinutes(10), 0);
    }

    public bool Verify(string email, string code, string clientKey)
    {
        var normalized = Normalize(email);
        if (!PortalIdentity.IsAllowed(normalized)) return false;
        PruneAndBound(verifyLimits, DateTimeOffset.UtcNow);
        EnforceGlobalLimit(ref globalVerifyLimit, 200, TimeSpan.FromMinutes(10));
        EnforceLimit(verifyLimits, "ip:" + clientKey, 20, TimeSpan.FromMinutes(10));
        EnforceLimit(verifyLimits, "account:" + HashKey(normalized), 10, TimeSpan.FromMinutes(10));
        if (code.Length != 8 || !records.TryGetValue(normalized, out var record)) return false;
        if (record.Expires <= DateTimeOffset.UtcNow || record.Attempts >= 5) { records.TryRemove(normalized, out _); return false; }
        var actual = Rfc2898DeriveBytes.Pbkdf2(code.ToUpperInvariant(), record.Salt, 120_000, HashAlgorithmName.SHA256, 32);
        if (!CryptographicOperations.FixedTimeEquals(actual, record.Hash)) { var updated = record with { Attempts = record.Attempts + 1 }; if (updated.Attempts >= 5) records.TryRemove(normalized, out _); else records[normalized] = updated; return false; }
        return records.TryRemove(normalized, out _);
    }

    private static string Normalize(string value) => (value ?? string.Empty).Trim().ToLowerInvariant();
    private static string HashKey(string value) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)));
    private static void EnforceLimit(ConcurrentDictionary<string, Window> limits, string key, int maximum, TimeSpan duration)
    {
        var now = DateTimeOffset.UtcNow;
        var current = limits.AddOrUpdate(key, _ => new Window(now.Add(duration), 1), (_, old) => old.Until <= now ? new Window(now.Add(duration), 1) : old with { Count = old.Count + 1 });
        if (current.Count > maximum) throw new OtpRejectedException();
    }
    private void EnforceGlobalLimit(ref Window window, int maximum, TimeSpan duration)
    {
        lock (globalLimitLock)
        {
            var now = DateTimeOffset.UtcNow;
            window = window.Until <= now ? new Window(now.Add(duration), 1) : window with { Count = window.Count + 1 };
            if (window.Count > maximum) throw new OtpRejectedException();
        }
    }
    private static void PruneAndBound(ConcurrentDictionary<string, Window> limits, DateTimeOffset now)
    {
        foreach (var item in limits)
            if (item.Value.Until <= now) limits.TryRemove(item.Key, out _);
        if (limits.Count >= 2048) throw new OtpRejectedException();
    }
    private sealed record Record(byte[] Salt, byte[] Hash, DateTimeOffset Expires, int Attempts);
    private sealed record Window(DateTimeOffset Until, int Count);
}

public sealed class GmailEmailSender(IConfiguration configuration) : IEmailSender
{
    private string Username => configuration["Email:Gmail:Username"]?.Trim() ?? string.Empty;
    private string Password => (configuration["Email:Gmail:AppPassword"] ?? Environment.GetEnvironmentVariable("AEVRYND_SMTP_PASSWORD") ?? string.Empty).Replace(" ", string.Empty, StringComparison.Ordinal);
    public bool IsReady => Username.Equals("slime12968@gmail.com", StringComparison.OrdinalIgnoreCase) && Password.Length == 16 && Password.All(char.IsAsciiLetterOrDigit);
    public async Task SendAsync(string recipient, string code, CancellationToken cancellationToken)
    {
        if (!IsReady) throw new InvalidOperationException("Email delivery is not configured.");
        using var message = new MailMessage(Username, recipient, "Aevrynd 登入驗證碼", $"您的驗證碼是：{code}\n有效期限 10 分鐘，且只能使用一次。");
        using var client = new SmtpClient("smtp.gmail.com", 587) { EnableSsl = true, Credentials = new NetworkCredential(Username, Password) };
        await client.SendMailAsync(message, cancellationToken);
    }
}

public sealed class OtpRejectedException : Exception;
