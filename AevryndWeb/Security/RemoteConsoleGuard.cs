using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;

namespace AevryndWeb.Security;

public enum RemoteCapability
{
    Screen,
    Text,
    Keyboard,
    Mouse,
    BrowserInput,
    Shell
}

public sealed record RemoteConsoleEnablement(
    string ActivationId,
    DateTimeOffset EnabledUntilUtc,
    IReadOnlySet<RemoteCapability> Capabilities,
    string PairingNonceHash,
    bool PairingNonceConsumed);

public interface IRemoteConsoleGuard
{
    bool TryRead(DateTimeOffset now, out RemoteConsoleEnablement enablement);
    bool VerifyPairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement);
    bool ConsumePairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement);
    void ResetOnStartup();
}

public sealed class RemoteConsoleGuard(IConfiguration configuration) : IRemoteConsoleGuard
{
    private readonly object sync = new();
    private bool startupResetComplete;
    private string StatePath => configuration["RemoteConsole:StatePath"] ?? @"C:\ProgramData\AevryndWeb\remote-console-state.json";

    public bool TryRead(DateTimeOffset now, out RemoteConsoleEnablement enablement)
    {
        lock (sync) return TryReadCore(now, out enablement, out _);
    }

    public bool VerifyPairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement)
    {
        lock (sync)
        {
            if (!TryReadCore(now, out enablement, out _ ) || enablement.PairingNonceConsumed) return false;
            return FixedHash(nonce, enablement.PairingNonceHash);
        }
    }

    public bool ConsumePairingNonce(string nonce, DateTimeOffset now, out RemoteConsoleEnablement enablement)
    {
        lock (sync)
        {
            if (!TryReadCore(now, out enablement, out var state) || enablement.PairingNonceConsumed || !FixedHash(nonce, enablement.PairingNonceHash)) return false;
            state!.PairingNonceConsumed = true;
            var temporary = StatePath + ".tmp";
            File.WriteAllText(temporary, JsonSerializer.Serialize(state), new UTF8Encoding(false));
            File.Move(temporary, StatePath, true);
            if (!HasSafeAcl(StatePath)) { File.Delete(StatePath); return false; }
            enablement = enablement with { PairingNonceConsumed = true };
            return true;
        }
    }

    private bool TryReadCore(DateTimeOffset now, out RemoteConsoleEnablement enablement, out StateDocument? document)
    {
        enablement = new(string.Empty, DateTimeOffset.MinValue, new HashSet<RemoteCapability>(), string.Empty, true);
        document = null;
        try
        {
            var stateDirectory = Path.GetDirectoryName(StatePath);
            if (!startupResetComplete || !OperatingSystem.IsWindows() || stateDirectory is null || !Directory.Exists(stateDirectory) ||
                !File.Exists(StatePath) || !HasSafeAcl(stateDirectory) || !HasSafeAcl(StatePath) || !HasSafeDataProtectionAcl()) return false;
            var info = new FileInfo(StatePath);
            if (info.Length is <= 0 or > 4096) return false;
            document = JsonSerializer.Deserialize<StateDocument>(File.ReadAllText(StatePath));
            if (document is null || document.Version != 1 || !IsHex64(document.ActivationId) || document.EnabledUntilUtc <= now || document.EnabledUntilUtc > now.AddMinutes(MaximumEnableMinutes()) ||
                !IsHex64(document.PairingNonceHash) || document.Capabilities is null || document.Capabilities.Count == 0) return false;
            var capabilities = new HashSet<RemoteCapability>();
            foreach (var value in document.Capabilities)
                if (!TryParseCapability(value, out var capability) || capability == RemoteCapability.Shell || !capabilities.Add(capability)) return false;
            if (capabilities.Contains(RemoteCapability.Mouse) && !capabilities.Contains(RemoteCapability.Screen)) return false;
            enablement = new(document.ActivationId, document.EnabledUntilUtc, capabilities, document.PairingNonceHash.ToUpperInvariant(), document.PairingNonceConsumed);
            return true;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or CryptographicException)
        {
            return false;
        }
    }

    public void ResetOnStartup()
    {
        lock (sync)
        {
            foreach (var path in new[] { StatePath, StatePath + ".tmp" })
                try { if (File.Exists(path)) File.Delete(path); } catch (Exception exception) when (exception is IOException or UnauthorizedAccessException) { }
            startupResetComplete = !File.Exists(StatePath) && !File.Exists(StatePath + ".tmp");
        }
    }

    private bool HasSafeDataProtectionAcl()
    {
        var path = configuration["DataProtection:KeyPath"] ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AevryndWeb", "keys");
        if (!Directory.Exists(path) || !HasSafeAcl(path)) return false;
        foreach (var file in Directory.EnumerateFiles(path))
            if (!HasSafeAcl(file)) return false;
        return true;
    }

    private static bool HasSafeAcl(string path)
    {
        if (!OperatingSystem.IsWindows()) return false;
        var attributes = File.GetAttributes(path);
        if ((attributes & FileAttributes.ReparsePoint) != 0) return false;
        var current = WindowsIdentity.GetCurrent().User;
        if (current is null) return false;
        FileSystemSecurity security = File.Exists(path)
            ? FileSystemAclExtensions.GetAccessControl(new FileInfo(path))
            : FileSystemAclExtensions.GetAccessControl(new DirectoryInfo(path));
        var owner = (SecurityIdentifier?)security.GetOwner(typeof(SecurityIdentifier));
        var administrators = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null);
        var system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
        if (owner is null || (!owner.Equals(current) && !owner.Equals(administrators) && !owner.Equals(system))) return false;
        foreach (FileSystemAccessRule rule in security.GetAccessRules(true, true, typeof(SecurityIdentifier)))
        {
            if (rule.AccessControlType != AccessControlType.Allow) continue;
            var sid = (SecurityIdentifier)rule.IdentityReference;
            if (sid.Equals(current) || sid.Equals(administrators) || sid.Equals(system)) continue;
            const FileSystemRights dangerous = FileSystemRights.Read | FileSystemRights.ReadData | FileSystemRights.ReadAttributes | FileSystemRights.ReadExtendedAttributes |
                FileSystemRights.Write | FileSystemRights.Modify | FileSystemRights.FullControl |
                FileSystemRights.CreateFiles | FileSystemRights.CreateDirectories | FileSystemRights.WriteData | FileSystemRights.AppendData |
                FileSystemRights.WriteAttributes | FileSystemRights.WriteExtendedAttributes | FileSystemRights.ChangePermissions | FileSystemRights.TakeOwnership;
            if ((rule.FileSystemRights & dangerous) != 0) return false;
        }
        return true;
    }

    private int MaximumEnableMinutes() => Math.Clamp(configuration.GetValue("RemoteConsole:MaximumEnableMinutes", 480), 5, 480);
    private static bool TryParseCapability(string value, out RemoteCapability capability)
    {
        capability = value switch
        {
            "screen.read" => RemoteCapability.Screen,
            "input.text" => RemoteCapability.Text,
            "keyboard.write" => RemoteCapability.Keyboard,
            "mouse.write" => RemoteCapability.Mouse,
            "browser.input" => RemoteCapability.BrowserInput,
            "shell.execute" => RemoteCapability.Shell,
            _ => (RemoteCapability)(-1)
        };
        return Enum.IsDefined(capability);
    }
    private static bool FixedHash(string nonce, string expected)
    {
        if (string.IsNullOrWhiteSpace(nonce) || nonce.Length > 256) return false;
        var actual = SHA256.HashData(Encoding.UTF8.GetBytes(nonce));
        try
        {
            var expectedBytes = Convert.FromHexString(expected);
            return expectedBytes.Length == 32 && CryptographicOperations.FixedTimeEquals(actual, expectedBytes);
        }
        catch (FormatException)
        {
            return false;
        }
    }
    private static bool IsHex64(string value) => value.Length == 64 && value.All(character => char.IsAsciiHexDigit(character));

    private sealed class StateDocument
    {
        public int Version { get; set; }
        public string ActivationId { get; set; } = string.Empty;
        public DateTimeOffset EnabledUntilUtc { get; set; }
        public List<string>? Capabilities { get; set; }
        public string PairingNonceHash { get; set; } = string.Empty;
        public bool PairingNonceConsumed { get; set; }
    }
}
