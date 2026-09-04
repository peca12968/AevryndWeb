Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:PublicSiteDomain = 'sample-cupid-overdrawn.ngrok-free.dev'
$script:PublicSitePort = 8080
$script:IisSiteName = 'AevryndWeb-IIS'
$script:IisAppPoolName = 'AevryndWeb-IIS'
$script:IisBinding = "http/127.0.0.1:8080:$script:PublicSiteDomain"
$script:PublicSiteRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'AevryndWeb'
$script:PublicSitePublish = Join-Path $script:PublicSiteRoot 'publish'
$script:PublicSiteState = Join-Path $script:PublicSiteRoot 'runtime.json'
$script:RemoteTelemetryDirectory = Join-Path $script:PublicSiteRoot 'remote-telemetry'
$script:OperationsStateDirectory = Join-Path $script:PublicSiteRoot 'operations'
$script:GmailCredentialTarget = 'Aevrynd/AssistantPortal/GmailAppPassword'
$script:NgrokCredentialTarget = 'Aevrynd/LineGateway/NgrokAuthtoken'
$script:NgrokPackageName = 'ngrok.ngrok'
$script:NgrokPackageFamily = 'ngrok.ngrok_1g87z0zv29zzc'
$script:NgrokPackagePublisher = 'CN=933CF6B5-07F8-4D54-9831-0ADEF7F6CC73'

function Assert-PublicSiteAdministrator {
    # IIS 組態備份與還原需要提升權限；必須在任何部署異動前明確拒絕非提升程序。
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Administrator elevation is required before IIS backup or deployment. Re-run PowerShell 7 as Administrator.'
    }
}

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

    [DllImport("shell32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    private static extern IntPtr CommandLineToArgvW(string commandLine, out int count);

    [DllImport("kernel32.dll")]
    private static extern IntPtr LocalFree(IntPtr value);

    public static string[] ParseArguments(string commandLine)
    {
        int count; var pointer = CommandLineToArgvW(commandLine, out count);
        if (pointer == IntPtr.Zero || count < 1) throw new InvalidOperationException("Command line cannot be parsed.");
        try { var result = new string[count]; for (var i=0;i<count;i++) result[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(pointer,i*IntPtr.Size)); return result; }
        finally { LocalFree(pointer); }
    }

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
            info.ArgumentList.Add("http://127.0.0.1:8080");
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
    $appcmd = Join-Path $env:SystemRoot 'System32\inetsrv\appcmd.exe'
    foreach ($path in @($dotnet, $ngrok, $appcmd)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required public-site runtime is missing: $path"
        }
    }
    $packages = @(Get-AppxPackage -Name $script:NgrokPackageName -ErrorAction Stop | Where-Object { $_.PackageFamilyName -ceq $script:NgrokPackageFamily -and $_.Publisher -ceq $script:NgrokPackagePublisher })
    if ($packages.Count -ne 1) { throw 'The trusted ngrok AppX package identity is unavailable or ambiguous.' }
    $ngrokImage = Join-Path $packages[0].InstallLocation 'ngrok.exe'
    if (-not (Test-Path -LiteralPath $ngrokImage -PathType Leaf)) { throw 'The trusted ngrok AppX image is missing.' }
    $ngrokHash = (Get-FileHash -LiteralPath $ngrokImage -Algorithm SHA256).Hash.ToLowerInvariant()
    return [pscustomobject]@{ Dotnet = $dotnet; Ngrok = $ngrok; NgrokImage = $ngrokImage; NgrokHash = $ngrokHash; AppCmd = $appcmd; Assembly = (Join-Path $script:PublicSitePublish 'AevryndWeb.dll') }
}

function Initialize-OperationsDirectories {
    $icacls = Join-Path $env:SystemRoot 'System32\icacls.exe'
    if (-not (Test-Path -LiteralPath $icacls -PathType Leaf)) { throw 'icacls.exe is required for operations directory ACL provisioning.' }
    foreach ($directory in @($script:OperationsStateDirectory,$script:RemoteTelemetryDirectory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        & $icacls $directory '/inheritance:r' '/setowner' '*S-1-5-32-544' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Operations directory owner provisioning failed: $directory" }
        & $icacls $directory '/grant:r' 'IIS AppPool\AevryndWeb-IIS:(OI)(CI)(M)' '*S-1-5-18:(OI)(CI)(F)' '*S-1-5-32-544:(OI)(CI)(F)' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Operations directory ACL provisioning failed: $directory" }
    }
    $legacyState = Join-Path $script:PublicSiteRoot 'operations-state.json'
    $managedState = Join-Path $script:OperationsStateDirectory 'operations-state.json'
    if (-not (Test-Path -LiteralPath $managedState) -and (Test-Path -LiteralPath $legacyState -PathType Leaf)) {
        $legacy = Get-Item -LiteralPath $legacyState -Force
        if ($legacy.Length -le 0 -or $legacy.Length -gt 524288 -or ($legacy.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Legacy operations state is outside migration limits.' }
        $document = Get-Content -Raw -LiteralPath $legacyState | ConvertFrom-Json
        if ($document.Version -ne 1) { throw 'Legacy operations state schema is invalid.' }
        Copy-Item -LiteralPath $legacyState -Destination $managedState
        & $icacls $managedState '/inheritance:e' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Migrated operations state did not inherit the secured ACL.' }
    }
}

function Initialize-IisContentAcl {
    $icacls = Join-Path $env:SystemRoot 'System32\icacls.exe'
    & $icacls $script:PublicSiteRoot '/grant' 'IIS AppPool\AevryndWeb-IIS:(RX)' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'IIS app pool cannot traverse the managed root.' }
    & $icacls $script:PublicSitePublish '/inheritance:r' '/grant:r' 'IIS AppPool\AevryndWeb-IIS:(OI)(CI)(RX)' '*S-1-5-18:(OI)(CI)(F)' '*S-1-5-32-544:(OI)(CI)(F)' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'IIS publish ACL provisioning failed.' }
}

function Invoke-NonFatalCommittedCleanup {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Action)
    try { & $Action; return $true }
    catch { Write-Warning "Committed deployment retained $Label backup: $($_.Exception.Message)"; return $false }
}

function Test-PublicSiteLocal {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$script:PublicSitePort/health/ready" -Headers @{ Host = $script:PublicSiteDomain } -TimeoutSec 3
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
    param([switch]$AllowLegacy)
    if (-not (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf)) { return $null }
    $item = Get-Item -LiteralPath $script:PublicSiteState -Force
    if ($item.Length -lt 2 -or $item.Length -gt 4096 -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Public-site runtime state is outside policy.'
    }
    $state = Get-Content -Raw -LiteralPath $script:PublicSiteState | ConvertFrom-Json
    $current = $state.schemaVersion -eq 3 -and $state.upstream -ceq 'iis' -and ($state.ngrokPid -is [long] -or $state.ngrokPid -is [int]) -and $state.ngrokImageSha256 -cmatch '^[0-9a-f]{64}$'
    $legacy = $AllowLegacy -and (($state.schemaVersion -eq 1 -and ($state.sitePid -is [long] -or $state.sitePid -is [int])) -or $state.schemaVersion -eq 2) -and ($state.ngrokPid -is [long] -or $state.ngrokPid -is [int])
    if (-not $current -and -not $legacy) {
        throw 'Public-site runtime state is invalid.'
    }
    return $state
}

function Write-PublicSiteRuntimeState {
    param([Parameter(Mandatory)][int]$NgrokPid, [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$NgrokImageSha256)
    New-Item -ItemType Directory -Path $script:PublicSiteRoot -Force | Out-Null
    $temporary = "$script:PublicSiteState.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        @{ schemaVersion = 3; upstream = 'iis'; ngrokPid = $NgrokPid; ngrokImageSha256 = $NgrokImageSha256; updatedUtc = [DateTime]::UtcNow.ToString('O') } |
            ConvertTo-Json -Compress | Set-Content -LiteralPath $temporary -Encoding utf8NoBOM
        Move-Item -LiteralPath $temporary -Destination $script:PublicSiteState -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Get-VerifiedPublicSiteProcess {
    param([Parameter(Mandatory)][int]$ProcessId, [Parameter(Mandatory)][object]$Paths, [ValidateSet(8080,8792)][int]$UpstreamPort = 8080, [string]$ExpectedHash = '')
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $null }
    if ($process.Name -cne 'ngrok.exe' -or -not [string]::Equals($process.ExecutablePath,$Paths.NgrokImage,[StringComparison]::OrdinalIgnoreCase)) { return $null }
    $arguments = [AevryndWebCredentialProcess]::ParseArguments($process.CommandLine)
    $expected = @($Paths.Ngrok,'http',"http://127.0.0.1:$UpstreamPort","--domain=$script:PublicSiteDomain",'--scheme=https','--inspect=false','--log=false')
    if ($arguments.Count -ne $expected.Count) { return $null }
    for ($index=0;$index-lt$expected.Count;$index++) { if (-not [string]::Equals($arguments[$index],$expected[$index],[StringComparison]::OrdinalIgnoreCase)) { return $null } }
    $actualHash = (Get-FileHash -LiteralPath $process.ExecutablePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -cne $Paths.NgrokHash -or ($ExpectedHash -and $actualHash -cne $ExpectedHash)) { return $null }
    return $process
}

function Get-VerifiedLegacySiteProcess {
    param([Parameter(Mandatory)][object]$Paths, [int]$ExpectedProcessId = 0)
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8792 -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { return $null }
    if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -cne '127.0.0.1' -or ($ExpectedProcessId -gt 0 -and $listeners[0].OwningProcess -ne $ExpectedProcessId)) { throw 'Legacy 8792 listener ownership is ambiguous.' }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listeners[0].OwningProcess)" -ErrorAction SilentlyContinue
    if ($null -eq $process -or $process.Name -cne 'dotnet.exe' -or -not [string]::Equals($process.ExecutablePath,$Paths.Dotnet,[StringComparison]::OrdinalIgnoreCase)) { throw 'Legacy 8792 listener is not the expected dotnet executable.' }
    $arguments = [AevryndWebCredentialProcess]::ParseArguments($process.CommandLine)
    if ($arguments.Count -ne 2 -or -not [string]::Equals([IO.Path]::GetFullPath($arguments[0]),[IO.Path]::GetFullPath($Paths.Dotnet),[StringComparison]::OrdinalIgnoreCase) -or
        -not [string]::Equals([IO.Path]::GetFullPath($arguments[1]),[IO.Path]::GetFullPath($Paths.Assembly),[StringComparison]::OrdinalIgnoreCase)) { throw 'Legacy 8792 command line does not exactly match the managed publish.' }
    return $process
}

function Assert-IisConfiguration {
    param([Parameter(Mandatory)][object]$Paths)
    [xml]$sites = (& $Paths.AppCmd list site /xml 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $null -eq $sites.appcmd) { throw 'IIS site inventory is unavailable.' }
    $portSites = @($sites.appcmd.SITE | Where-Object { ([string]$_.'bindings').Split(',') | Where-Object { $_ -match '^http/[^:]*:8080:' } })
    $expected = @($sites.appcmd.SITE | Where-Object { $_.'SITE.NAME' -ceq $script:IisSiteName })
    if ($expected.Count -ne 1 -or $portSites.Count -ne 1 -or $portSites[0].'SITE.NAME' -cne $script:IisSiteName -or [string]$expected[0].bindings -cne $script:IisBinding) { throw 'IIS binding contract drifted from the single loopback 8080 site.' }
    $physicalPath = ((& $Paths.AppCmd list vdir "$script:IisSiteName/" /text:physicalPath 2>$null) -join '').Trim()
    if ($LASTEXITCODE -ne 0 -or -not [string]::Equals([IO.Path]::GetFullPath($physicalPath),[IO.Path]::GetFullPath($script:PublicSitePublish),[StringComparison]::OrdinalIgnoreCase)) { throw 'IIS physical path is not the managed publish directory.' }
    $runtime = ((& $Paths.AppCmd list apppool $script:IisAppPoolName /text:managedRuntimeVersion 2>$null) -join '').Trim()
    $pipeline = ((& $Paths.AppCmd list apppool $script:IisAppPoolName /text:managedPipelineMode 2>$null) -join '').Trim()
    $startMode = ((& $Paths.AppCmd list apppool $script:IisAppPoolName /text:startMode 2>$null) -join '').Trim()
    $poolState = (& $Paths.AppCmd list apppool $script:IisAppPoolName /text:state 2>$null) -join ''
    $siteState = (& $Paths.AppCmd list site $script:IisSiteName /text:state 2>$null) -join ''
    if ($LASTEXITCODE -ne 0 -or $runtime -ne '' -or $pipeline -cne 'Integrated' -or $startMode -cne 'AlwaysRunning' -or $poolState -cne 'Started' -or $siteState -cne 'Started') { throw 'IIS site or application pool contract is not healthy.' }
    return $true
}
