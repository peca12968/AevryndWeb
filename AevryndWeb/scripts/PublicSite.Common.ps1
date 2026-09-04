Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:PublicSiteDomain = 'sample-cupid-overdrawn.ngrok-free.dev'
$script:PublicSitePort = 8792
$script:PublicSiteRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'AevryndWeb'
$script:PublicSitePublish = Join-Path $script:PublicSiteRoot 'publish'
$script:PublicSiteState = Join-Path $script:PublicSiteRoot 'runtime.json'
$script:RemoteTelemetryDirectory = Join-Path $script:PublicSiteRoot 'remote-telemetry'
$script:GmailCredentialTarget = 'Aevrynd/AssistantPortal/GmailAppPassword'
$script:NgrokCredentialTarget = 'Aevrynd/LineGateway/NgrokAuthtoken'

function Add-PublicSiteCredentialInterop {
    if ('AevryndWebCredentialProcess' -as [type]) { return }
    Add-Type @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;

public static class AevryndWebCredentialProcess
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct Credential
    {
        public uint Flags, Type;
        public IntPtr TargetName, Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint BlobSize;
        public IntPtr Blob;
        public uint Persist, AttributeCount;
        public IntPtr Attributes, Alias, User;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool Read(string target, uint type, uint flags, out IntPtr value);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr value);

    private static string Load(string target)
    {
        if (!Read(target, 1, 0, out var pointer))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        try
        {
            var credential = Marshal.PtrToStructure<Credential>(pointer);
            return Marshal.PtrToStringUni(credential.Blob, checked((int)credential.BlobSize / 2));
        }
        finally { CredFree(pointer); }
    }

    public static bool Available(string target, int minimum, int maximum)
    {
        string value = null;
        try
        {
            value = Load(target);
            return value != null && value.Length >= minimum && value.Length <= maximum;
        }
        catch { return false; }
        finally { value = null; }
    }

    public static Process StartSite(string dotnet, string assembly, string credentialTarget)
    {
        string secret = Load(credentialTarget);
        try
        {
            if (String.IsNullOrWhiteSpace(secret))
                throw new InvalidOperationException("Gmail credential is empty.");
            var info = new ProcessStartInfo(dotnet)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = System.IO.Path.GetDirectoryName(assembly)
            };
            info.ArgumentList.Add(assembly);
            info.Environment["ASPNETCORE_ENVIRONMENT"] = "Production";
            info.Environment["ASPNETCORE_URLS"] = "http://127.0.0.1:8792";
            info.Environment["AEVRYND_SMTP_PASSWORD"] = secret;
            return Process.Start(info);
        }
        finally { secret = null; }
    }

    public static Process StartNgrok(string executable, string credentialTarget)
    {
        string secret = Load(credentialTarget);
        try
        {
            if (String.IsNullOrWhiteSpace(secret))
                throw new InvalidOperationException("Ngrok credential is empty.");
            var info = new ProcessStartInfo(executable)
            {
                UseShellExecute = false,
                CreateNoWindow = true
            };
            info.ArgumentList.Add("http");
            info.ArgumentList.Add("http://127.0.0.1:8792");
            info.ArgumentList.Add("--domain=sample-cupid-overdrawn.ngrok-free.dev");
            info.ArgumentList.Add("--scheme=https");
            info.ArgumentList.Add("--inspect=false");
            info.ArgumentList.Add("--log=false");
            info.Environment["NGROK_AUTHTOKEN"] = secret;
            return Process.Start(info);
        }
        finally { secret = null; }
    }
}
'@
}

function Get-PublicSitePaths {
    $dotnet = 'C:\Program Files\dotnet\dotnet.exe'
    $ngrok = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\ngrok.exe'
    $assembly = Join-Path $script:PublicSitePublish 'AevryndWeb.dll'
    foreach ($path in @($dotnet, $ngrok, $assembly)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required public-site runtime is missing: $path"
        }
    }
    return [pscustomobject]@{ Dotnet = $dotnet; Ngrok = $ngrok; Assembly = $assembly }
}

function Initialize-RemoteTelemetryDirectory {
    New-Item -ItemType Directory -Path $script:RemoteTelemetryDirectory -Force | Out-Null
    $security = New-Object System.Security.AccessControl.DirectorySecurity
    $security.SetAccessRuleProtection($true, $false)
    $inheritance = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
    $propagation = [System.Security.AccessControl.PropagationFlags]::None
    $identities = @([System.Security.Principal.WindowsIdentity]::GetCurrent().User,
        (New-Object System.Security.Principal.SecurityIdentifier([System.Security.Principal.WellKnownSidType]::BuiltinAdministratorsSid, $null)),
        (New-Object System.Security.Principal.SecurityIdentifier([System.Security.Principal.WellKnownSidType]::LocalSystemSid, $null)))
    foreach ($identity in $identities) {
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($identity, [System.Security.AccessControl.FileSystemRights]::FullControl, $inheritance, $propagation, [System.Security.AccessControl.AccessControlType]::Allow)
        $security.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $script:RemoteTelemetryDirectory -AclObject $security
}

function Test-PublicSiteLocal {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$script:PublicSitePort/health/ready" -TimeoutSec 3
        if ($response.StatusCode -ne 200) { return $false }
        $payload = $response.Content | ConvertFrom-Json
        return $payload.status -eq 'ok' -and $payload.emailReady -eq $true
    } catch { return $false }
}

function Test-PublicSiteExternal {
    try {
        $curl = Join-Path $env:SystemRoot 'System32\curl.exe'
        if (-not (Test-Path -LiteralPath $curl -PathType Leaf)) { return $false }
        $root = (& $curl --silent --show-error --fail --max-time 10 --header 'ngrok-skip-browser-warning: AevryndWeb-HealthCheck' "https://$script:PublicSiteDomain/" 2>$null) -join "`n"
        if ($LASTEXITCODE -ne 0 -or -not $root.Contains('class="login-shell"') -or -not $root.Contains('/css/site.css')) { return $false }
        $health = (& $curl --silent --show-error --fail --max-time 10 --header 'ngrok-skip-browser-warning: AevryndWeb-HealthCheck' "https://$script:PublicSiteDomain/health/ready" 2>$null) -join "`n"
        if ($LASTEXITCODE -ne 0) { return $false }
        $payload = $health | ConvertFrom-Json
        return $payload.status -eq 'ok' -and $payload.emailReady -eq $true
    } catch { return $false }
}

function Get-PublicSiteRuntimeState {
    if (-not (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf)) { return $null }
    $item = Get-Item -LiteralPath $script:PublicSiteState -Force
    if ($item.Length -lt 2 -or $item.Length -gt 4096 -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Public-site runtime state is outside policy.'
    }
    $state = Get-Content -Raw -LiteralPath $script:PublicSiteState | ConvertFrom-Json
    if ($state.schemaVersion -ne 1 -or $state.sitePid -isnot [long] -and $state.sitePid -isnot [int] -or
        $state.ngrokPid -isnot [long] -and $state.ngrokPid -isnot [int]) {
        throw 'Public-site runtime state is invalid.'
    }
    return $state
}

function Write-PublicSiteRuntimeState {
    param([Parameter(Mandatory)][int]$SitePid, [Parameter(Mandatory)][int]$NgrokPid)
    New-Item -ItemType Directory -Path $script:PublicSiteRoot -Force | Out-Null
    $temporary = "$script:PublicSiteState.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        @{ schemaVersion = 1; sitePid = $SitePid; ngrokPid = $NgrokPid; updatedUtc = [DateTime]::UtcNow.ToString('O') } |
            ConvertTo-Json -Compress | Set-Content -LiteralPath $temporary -Encoding utf8NoBOM
        Move-Item -LiteralPath $temporary -Destination $script:PublicSiteState -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Get-VerifiedPublicSiteProcess {
    param([Parameter(Mandatory)][int]$ProcessId, [Parameter(Mandatory)][string]$Kind, [Parameter(Mandatory)][object]$Paths)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $null }
    if ($Kind -eq 'site') {
        if ($process.Name -cne 'dotnet.exe' -or -not $process.CommandLine.Contains($Paths.Assembly, [StringComparison]::OrdinalIgnoreCase)) { return $null }
    } else {
        if ($process.Name -cne 'ngrok.exe' -or -not $process.CommandLine.Contains("--domain=$script:PublicSiteDomain", [StringComparison]::Ordinal)) { return $null }
    }
    return $process
}
