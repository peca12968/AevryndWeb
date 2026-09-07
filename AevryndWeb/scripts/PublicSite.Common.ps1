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

    public static string LoadValue(string target)
    {
        return Load(target);
    }

    public static Process StartNgrok(string executable, string credentialTarget)
    {
        return StartNgrok(executable, credentialTarget, 8080);
    }

    public static Process StartNgrok(string executable, string credentialTarget, int upstreamPort)
    {
        if (upstreamPort != 8080 && upstreamPort != 8792)
            throw new ArgumentOutOfRangeException(nameof(upstreamPort));
        string secret = Load(credentialTarget);
        try
        {
            if (String.IsNullOrWhiteSpace(secret))
                throw new InvalidOperationException("Ngrok credential is empty.");
            var info = new ProcessStartInfo(executable)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            info.ArgumentList.Add("http");
            info.ArgumentList.Add("http://127.0.0.1:" + upstreamPort.ToString(System.Globalization.CultureInfo.InvariantCulture));
            info.ArgumentList.Add("--domain=sample-cupid-overdrawn.ngrok-free.dev");
            info.ArgumentList.Add("--scheme=https");
            info.ArgumentList.Add("--inspect=false");
            info.ArgumentList.Add("--log=false");
            info.Environment["NGROK_AUTHTOKEN"] = secret;
            var process = Process.Start(info);
            if (process == null) throw new InvalidOperationException("Ngrok process did not start.");
            // 背景程序不得繼承部署管線；持續排空輸出，避免父程序在 IIS 切換後永久等待。
            process.OutputDataReceived += delegate { };
            process.ErrorDataReceived += delegate { };
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return process;
        }
        finally { secret = null; }
    }

    public static Process StartLegacySite(string executable, string assembly)
    {
        var info = new ProcessStartInfo(executable)
        {
            UseShellExecute = false,
            CreateNoWindow = true
        };
        info.ArgumentList.Add(assembly);
        info.Environment["ASPNETCORE_ENVIRONMENT"] = "Production";
        info.Environment["ASPNETCORE_URLS"] = "http://127.0.0.1:8792";
        return Process.Start(info);
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
        # 部分 Windows 版本不接受把 /setowner 與 /inheritance 合併在同一次 icacls 呼叫。
        & $icacls $directory '/setowner' '*S-1-5-32-544' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Operations directory owner provisioning failed: $directory" }
        & $icacls $directory '/grant:r' 'IIS AppPool\AevryndWeb-IIS:(OI)(CI)(M)' '*S-1-5-18:(OI)(CI)(F)' '*S-1-5-32-544:(OI)(CI)(F)' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Operations directory ACL provisioning failed: $directory" }
        & $icacls $directory '/inheritance:r' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Operations directory inheritance removal failed: $directory" }
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
    param([string]$PublishPath = $script:PublicSitePublish, [switch]$SkipRoot)
    $icacls = Join-Path $env:SystemRoot 'System32\icacls.exe'
    if (-not $SkipRoot) {
        & $icacls $script:PublicSiteRoot '/grant' 'IIS AppPool\AevryndWeb-IIS:(RX)' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'IIS app pool cannot traverse the managed root.' }
    }
    & $icacls $PublishPath '/grant:r' 'IIS AppPool\AevryndWeb-IIS:(OI)(CI)(RX)' '*S-1-5-18:(OI)(CI)(F)' '*S-1-5-32-544:(OI)(CI)(F)' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'IIS publish ACL provisioning failed.' }
    & $icacls $PublishPath '/inheritance:r' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'IIS publish ACL inheritance removal failed.' }
    $acl = Get-Acl -LiteralPath $PublishPath
    if (-not $acl.AreAccessRulesProtected) { throw 'IIS publish ACL still inherits permissions.' }
    $rules = @($acl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier]))
    $appPoolSid = [Security.Principal.NTAccount]::new('IIS AppPool\AevryndWeb-IIS').Translate([Security.Principal.SecurityIdentifier]).Value
    foreach ($required in @(
        [pscustomobject]@{ Identity='S-1-5-18'; Rights=[Security.AccessControl.FileSystemRights]::FullControl },
        [pscustomobject]@{ Identity='S-1-5-32-544'; Rights=[Security.AccessControl.FileSystemRights]::FullControl },
        [pscustomobject]@{ Identity=$appPoolSid; Rights=[Security.AccessControl.FileSystemRights]::ReadAndExecute }
    )) {
        $matched = @($rules | Where-Object { $_.IdentityReference.Value -ceq $required.Identity -and $_.AccessControlType -eq 'Allow' -and ($_.FileSystemRights -band $required.Rights) -eq $required.Rights })
        if ($matched.Count -eq 0) { throw "IIS publish ACL readback failed for $($required.Identity)." }
    }
}

function Initialize-ManagedScriptsAcl {
    param(
        [Parameter(Mandatory)][string]$ScriptsPath,
        [Parameter(Mandatory)][string]$TaskPrincipal,
        [string]$OwnerPrincipal = '*S-1-5-32-544',
        [scriptblock]$InvokeAcl = $null,
        [scriptblock]$ReadAcl = $null
    )
    if ([string]::IsNullOrWhiteSpace($TaskPrincipal)) { throw 'Scheduled-task principal is required for scripts ACL provisioning.' }
    if ($null -eq $InvokeAcl) {
        $icacls = Join-Path $env:SystemRoot 'System32\icacls.exe'
        $InvokeAcl = {
            param([string]$Path, [string[]]$Arguments)
            & $icacls $Path @Arguments | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Managed scripts ACL command failed for $Path." }
        }.GetNewClosure()
    }
    if ($null -eq $ReadAcl) { $ReadAcl = { param([string]$Path) Get-Acl -LiteralPath $Path } }

    & $InvokeAcl $ScriptsPath @('/setowner',$OwnerPrincipal)
    & $InvokeAcl $ScriptsPath @('/grant:r','*S-1-5-18:(OI)(CI)(F)','*S-1-5-32-544:(OI)(CI)(F)',"$TaskPrincipal`:(OI)(CI)(RX)")
    & $InvokeAcl $ScriptsPath @('/inheritance:r')
    $acl = & $ReadAcl $ScriptsPath
    if ($null -eq $acl -or -not $acl.AreAccessRulesProtected) { throw 'Managed scripts ACL still inherits permissions.' }
    $expectedOwnerSid = if ($OwnerPrincipal.StartsWith('*S-1-',[StringComparison]::OrdinalIgnoreCase)) { $OwnerPrincipal.Substring(1) } else { [Security.Principal.NTAccount]::new($OwnerPrincipal).Translate([Security.Principal.SecurityIdentifier]).Value }
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne $expectedOwnerSid) { throw 'Managed scripts ACL owner readback failed.' }
    $accessRules = @($acl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier]))

    $required = @{
        'S-1-5-18' = [Security.AccessControl.FileSystemRights]::FullControl
        'S-1-5-32-544' = [Security.AccessControl.FileSystemRights]::FullControl
        ([Security.Principal.NTAccount]::new($TaskPrincipal).Translate([Security.Principal.SecurityIdentifier]).Value) = [Security.AccessControl.FileSystemRights]::ReadAndExecute
    }
    foreach ($sid in $required.Keys) {
        $matching = @($accessRules | Where-Object {
            $_.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
            $_.IdentityReference.Value -ceq $sid -and
            ($_.FileSystemRights -band $required[$sid]) -eq $required[$sid]
        })
        if ($matching.Count -eq 0) { throw "Managed scripts ACL is missing required access for $sid." }
    }
    $taskSid = [Security.Principal.NTAccount]::new($TaskPrincipal).Translate([Security.Principal.SecurityIdentifier]).Value
    $writeRights = [Security.AccessControl.FileSystemRights]::WriteData -bor
        [Security.AccessControl.FileSystemRights]::AppendData -bor
        [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes -bor
        [Security.AccessControl.FileSystemRights]::WriteAttributes -bor
        [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor
        [Security.AccessControl.FileSystemRights]::Delete -bor
        [Security.AccessControl.FileSystemRights]::ChangePermissions -bor
        [Security.AccessControl.FileSystemRights]::TakeOwnership
    $writable = @($accessRules | Where-Object {
        $_.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
        $_.IdentityReference.Value -ceq $taskSid -and
        ($_.FileSystemRights -band $writeRights) -ne 0
    })
    if ($writable.Count -gt 0) { throw 'Scheduled-task principal retains write access to elevated scripts.' }
    return $true
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
        return Test-PublicSiteReadinessPayload -Payload $payload
    } catch { return $false }
}

function Test-PublicSiteReadinessPayload {
    param([Parameter(Mandatory)][object]$Payload)
    return $Payload.status -ceq 'ok' -and $Payload.emailReady -is [bool] -and $Payload.emailReady -eq $true
}

function Test-PublicSiteOriginHealthy {
    param([Parameter(Mandatory)][ValidateSet(8080,8792)][int]$Port)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health/ready" -Headers @{ Host = $script:PublicSiteDomain } -TimeoutSec 3
        if ($response.StatusCode -ne 200) { return $false }
        $payload = $response.Content | ConvertFrom-Json
        return Test-PublicSiteReadinessPayload -Payload $payload
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
        return Test-PublicSiteReadinessPayload -Payload $payload
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

function Restore-PreviousPublicSiteRuntimeState {
    param([Parameter(Mandatory)][object]$Contract, [string]$StatePath = $script:PublicSiteState)
    if (-not $Contract.RuntimeStatePresent) {
        if (Test-Path -LiteralPath $StatePath -PathType Leaf) { Remove-Item -LiteralPath $StatePath -Force }
        return
    }
    if ($null -eq $Contract.RuntimeState) { throw 'Saved runtime-state contract is missing its validated document.' }
    $state = $Contract.RuntimeState | ConvertTo-Json -Depth 8 -Compress | ConvertFrom-Json
    switch ([int]$state.schemaVersion) {
        1 {
            if ([int]$Contract.SiteProcessId -le 0 -or [int]$Contract.NgrokProcessId -le 0) { throw 'Schema 1 rollback state requires restored site and ngrok process identities.' }
            $state.sitePid = [int]$Contract.SiteProcessId
            $state.ngrokPid = [int]$Contract.NgrokProcessId
        }
        2 {
            if ([int]$Contract.NgrokProcessId -le 0) { throw 'Schema 2 rollback state requires a restored ngrok process identity.' }
            $state.ngrokPid = [int]$Contract.NgrokProcessId
        }
        3 {
            if ([int]$Contract.NgrokProcessId -le 0) { throw 'Schema 3 rollback state requires a restored ngrok process identity.' }
            $state.ngrokPid = [int]$Contract.NgrokProcessId
            # schema 3 的 image hash 已在 previous-route admission 驗證；重建時不得降級或替換。
            $state.ngrokImageSha256 = [string]$Contract.RuntimeState.ngrokImageSha256
        }
        default { throw 'Saved runtime-state schema is outside the rollback contract.' }
    }
    $parent = Split-Path -Parent $StatePath
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $temporary = "$StatePath.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        $state | ConvertTo-Json -Depth 8 -Compress | Set-Content -LiteralPath $temporary -Encoding utf8NoBOM
        Move-Item -LiteralPath $temporary -Destination $StatePath -Force
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Get-VerifiedPublicSiteProcess {
    param([Parameter(Mandatory)][int]$ProcessId, [Parameter(Mandatory)][object]$Paths, [ValidateSet(8080,8792)][int]$UpstreamPort = 8080, [string]$ExpectedHash = '')
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $null }
    if ($process.Name -cne 'ngrok.exe' -or -not [string]::Equals($process.ExecutablePath,$Paths.NgrokImage,[StringComparison]::OrdinalIgnoreCase)) { return $null }
    $arguments = [AevryndWebCredentialProcess]::ParseArguments($process.CommandLine)
    $expected = @($Paths.NgrokImage,'http',"http://127.0.0.1:$UpstreamPort","--domain=$script:PublicSiteDomain",'--scheme=https','--inspect=false','--log=false')
    if ($arguments.Count -ne $expected.Count) { return $null }
    # 舊版以受信任 WindowsApps alias 啟動；新版直接啟動已驗證映像，兩者的其餘參數必須完全一致。
    if (-not [string]::Equals($arguments[0],$Paths.NgrokImage,[StringComparison]::OrdinalIgnoreCase) -and
        -not [string]::Equals($arguments[0],$Paths.Ngrok,[StringComparison]::OrdinalIgnoreCase)) { return $null }
    for ($index=1;$index-lt$expected.Count;$index++) { if (-not [string]::Equals($arguments[$index],$expected[$index],[StringComparison]::OrdinalIgnoreCase)) { return $null } }
    $actualHash = (Get-FileHash -LiteralPath $process.ExecutablePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -cne $Paths.NgrokHash -or ($ExpectedHash -and $actualHash -cne $ExpectedHash)) { return $null }
    return $process
}

function Test-PublicSiteDomainClaim {
    param([Parameter(Mandatory)][string]$CommandLine)
    try { $arguments = [AevryndWebCredentialProcess]::ParseArguments($CommandLine) } catch { return $false }
    foreach ($argument in $arguments) {
        if ([string]::Equals($argument,"--domain=$script:PublicSiteDomain",[StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Get-PublicSiteDomainProcesses {
    param([object[]]$Processes = @())
    if ($PSBoundParameters.ContainsKey('Processes')) { $candidates = @($Processes) }
    else { $candidates = @(Get-CimInstance Win32_Process -Filter "Name='ngrok.exe'" -ErrorAction SilentlyContinue) }
    return @($candidates | Where-Object {
        $_.Name -ceq 'ngrok.exe' -and $_.CommandLine -and (Test-PublicSiteDomainClaim -CommandLine ([string]$_.CommandLine))
    })
}

function Resolve-PublicSiteStartProcess {
    param(
        [object]$RuntimeState,
        [object[]]$DomainProcesses,
        [Parameter(Mandatory)][scriptblock]$VerifyStateProcess,
        [Parameter(Mandatory)][scriptblock]$VerifyDomainProcess,
        [Parameter(Mandatory)][scriptblock]$StartProcess
    )
    if ($null -ne $RuntimeState) {
        $stateProcess = & $VerifyStateProcess $RuntimeState
        if ($null -ne $stateProcess) { return [pscustomobject]@{ Process=$stateProcess; Launched=$false; Source='state' } }
    }
    if ($DomainProcesses.Count -gt 1) { throw 'Multiple ngrok processes claim the public-site domain.' }
    if ($DomainProcesses.Count -eq 1) {
        $claimed = & $VerifyDomainProcess $DomainProcesses[0]
        if ($null -eq $claimed) { throw 'The public-site domain claimant is outside the managed IIS contract.' }
        return [pscustomobject]@{ Process=$claimed; Launched=$false; Source='claim' }
    }
    $started = & $StartProcess
    if ($null -eq $started) { throw 'Managed ngrok did not return a process.' }
    return [pscustomobject]@{ Process=$started; Launched=$true; Source='new' }
}

function Resolve-PublicSiteStopProcess {
    param(
        [object]$RuntimeState,
        [object[]]$DomainProcesses,
        [Parameter(Mandatory)][scriptblock]$VerifyStateProcess,
        [Parameter(Mandatory)][scriptblock]$VerifyDomainProcess
    )
    if ($null -ne $RuntimeState) {
        $owned = & $VerifyStateProcess $RuntimeState
        if ($null -eq $owned) { throw 'Runtime state exists, but ngrok process ownership cannot be proven.' }
        return $owned
    }
    if ($DomainProcesses.Count -gt 1) { throw 'Multiple ngrok processes claim the fixed domain.' }
    if ($DomainProcesses.Count -eq 0) { return $null }
    $owned = & $VerifyDomainProcess $DomainProcesses[0]
    if ($null -eq $owned) { throw 'Domain ngrok has an unexpected executable or upstream; nothing was stopped.' }
    return $owned
}

function Get-VerifiedLegacySiteProcess {
    param([Parameter(Mandatory)][object]$Paths, [int]$ExpectedProcessId = 0)
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8792 -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { return $null }
    if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -cne '127.0.0.1' -or ($ExpectedProcessId -gt 0 -and $listeners[0].OwningProcess -ne $ExpectedProcessId)) { throw 'Legacy 8792 listener ownership is ambiguous.' }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listeners[0].OwningProcess)" -ErrorAction SilentlyContinue
    if ($null -eq $process -or $process.Name -cne 'dotnet.exe' -or -not [string]::Equals($process.ExecutablePath,$Paths.Dotnet,[StringComparison]::OrdinalIgnoreCase)) { throw 'Legacy 8792 listener is not the expected dotnet executable.' }
    $arguments = [AevryndWebCredentialProcess]::ParseArguments($process.CommandLine)
    $exactExecutable = $arguments.Count -ge 2 -and [string]::Equals([IO.Path]::GetFullPath($arguments[0]),[IO.Path]::GetFullPath($Paths.Dotnet),[StringComparison]::OrdinalIgnoreCase)
    $exactAssembly = $arguments.Count -ge 2 -and [string]::Equals([IO.Path]::GetFullPath($arguments[1]),[IO.Path]::GetFullPath($Paths.Assembly),[StringComparison]::OrdinalIgnoreCase)
    $exactEnvironmentForm = $arguments.Count -eq 2
    $exactArgumentForm = $arguments.Count -eq 4 -and $arguments[2] -ceq '--Hosting:Url' -and $arguments[3] -ceq 'http://127.0.0.1:8792'
    if (-not $exactExecutable -or -not $exactAssembly -or (-not $exactEnvironmentForm -and -not $exactArgumentForm)) { throw 'Legacy 8792 command line does not exactly match the managed publish.' }
    return $process
}

function Get-PreviousPublicSiteRouteContract {
    param(
        [Parameter(Mandatory)][object]$Paths,
        [object]$RuntimeState = $null,
        [object[]]$DomainProcesses = @(),
        [scriptblock]$ResolveLegacy = $null,
        [scriptblock]$VerifyNgrok = $null,
        [scriptblock]$TestOrigin = $null,
        [scriptblock]$TestExternal = $null
    )
    if (-not $PSBoundParameters.ContainsKey('RuntimeState')) { $RuntimeState = Get-PublicSiteRuntimeState -AllowLegacy }
    if (-not $PSBoundParameters.ContainsKey('DomainProcesses')) { $DomainProcesses = @(Get-PublicSiteDomainProcesses) }
    if ($null -eq $ResolveLegacy) {
        # GetNewClosure 會進入動態模組；必須捕捉 FunctionInfo，否則提升程序找不到同檔案的私有函式。
        $legacyVerifier = Get-Command Get-VerifiedLegacySiteProcess -CommandType Function
        $ResolveLegacy = { param($Expected) & $legacyVerifier -Paths $Paths -ExpectedProcessId $Expected }.GetNewClosure()
    }
    if ($null -eq $VerifyNgrok) {
        $ngrokVerifier = Get-Command Get-VerifiedPublicSiteProcess -CommandType Function
        $VerifyNgrok = { param($ProcessIdentifier,$Port,$Hash) & $ngrokVerifier -ProcessId $ProcessIdentifier -Paths $Paths -UpstreamPort $Port -ExpectedHash $Hash }.GetNewClosure()
    }
    if ($null -eq $TestOrigin) { $TestOrigin = { param($Port) Test-PublicSiteOriginHealthy -Port $Port } }
    if ($null -eq $TestExternal) { $TestExternal = { Test-PublicSiteExternal } }

    if ($DomainProcesses.Count -gt 1) { throw 'Multiple ngrok processes claim the fixed domain before deployment.' }
    $legacyExpected = if ($null -ne $RuntimeState -and $RuntimeState.schemaVersion -eq 1) { [int]$RuntimeState.sitePid } else { 0 }
    $legacy = & $ResolveLegacy $legacyExpected
    $port = if ($null -ne $RuntimeState -and $RuntimeState.schemaVersion -in @(2,3)) { 8080 } elseif ($null -ne $legacy -or ($null -ne $RuntimeState -and $RuntimeState.schemaVersion -eq 1)) { 8792 } else { 8080 }
    $kind = if ($port -eq 8792) { 'Legacy' } elseif ($DomainProcesses.Count -eq 1 -or $null -ne $RuntimeState) { 'Iis' } else { 'None' }
    if ($kind -eq 'None') {
        return [pscustomobject]@{ Kind='None'; UpstreamPort=0; SiteProcessId=0; NgrokProcessId=0; NgrokImageSha256=''; WasHealthy=$false; SiteStopped=$false; NgrokStopped=$false; RuntimeStatePresent=$false; RuntimeState=$null }
    }
    if ($DomainProcesses.Count -ne 1) { throw 'The previous public route does not have exactly one fixed-domain ngrok process.' }
    $ngrokPid = if ($null -ne $RuntimeState) { [int]$RuntimeState.ngrokPid } else { [int]$DomainProcesses[0].ProcessId }
    if ([int]$DomainProcesses[0].ProcessId -ne $ngrokPid) { throw 'Runtime state and fixed-domain ngrok process disagree.' }
    $expectedHash = if ($null -ne $RuntimeState -and $RuntimeState.schemaVersion -eq 3) { [string]$RuntimeState.ngrokImageSha256 } else { '' }
    $ngrok = & $VerifyNgrok $ngrokPid $port $expectedHash
    if ($null -eq $ngrok) { throw 'The previous fixed-domain ngrok executable, image hash, or upstream is outside the exact contract.' }
    if ($kind -eq 'Legacy' -and $null -eq $legacy) { throw 'The previous legacy site process could not be proven.' }
    if (-not (& $TestOrigin $port) -or -not (& $TestExternal)) { throw 'The previous public route is not healthy enough to preserve for rollback.' }
    return [pscustomobject]@{
        Kind = $kind
        UpstreamPort = $port
        SiteProcessId = if ($null -ne $legacy) { [int]$legacy.ProcessId } else { 0 }
        NgrokProcessId = [int]$ngrok.ProcessId
        NgrokImageSha256 = $Paths.NgrokHash
        SiteExecutable = $Paths.Dotnet
        SiteAssembly = $Paths.Assembly
        WasHealthy = $true
        SiteStopped = $false
        NgrokStopped = $false
        RuntimeStatePresent = $null -ne $RuntimeState
        RuntimeState = $RuntimeState
    }
}

function Stop-ProvenPreviousPublicSiteRoute {
    param(
        [Parameter(Mandatory)][object]$Contract,
        [Parameter(Mandatory)][object]$Paths,
        [scriptblock]$VerifyNgrok = $null,
        [scriptblock]$VerifyLegacy = $null,
        [scriptblock]$StopProcess = $null,
        [string]$StatePath = $script:PublicSiteState
    )
    if ($Contract.Kind -eq 'None') { return }
    if ($null -eq $VerifyNgrok) {
        $ngrokVerifier = Get-Command Get-VerifiedPublicSiteProcess -CommandType Function
        $VerifyNgrok = { & $ngrokVerifier -ProcessId ([int]$Contract.NgrokProcessId) -Paths $Paths -UpstreamPort ([int]$Contract.UpstreamPort) -ExpectedHash ([string]$Contract.NgrokImageSha256) }.GetNewClosure()
    }
    if ($null -eq $VerifyLegacy) {
        $legacyVerifier = Get-Command Get-VerifiedLegacySiteProcess -CommandType Function
        $VerifyLegacy = { & $legacyVerifier -Paths $Paths -ExpectedProcessId ([int]$Contract.SiteProcessId) }.GetNewClosure()
    }
    if ($null -eq $StopProcess) {
        $StopProcess = {
            param([int]$ProcessIdentifier,[string]$Label)
            $process = Get-Process -Id $ProcessIdentifier -ErrorAction Stop
            $process.Kill($true)
            if (-not $process.WaitForExit(10000)) { throw "$Label did not stop." }
        }
    }
    $ngrok = & $VerifyNgrok
    if ($null -eq $ngrok) { throw 'The saved previous ngrok contract changed before transition stop.' }
    $legacy = $null
    if ($Contract.Kind -eq 'Legacy') {
        $legacy = & $VerifyLegacy
        if ($null -eq $legacy) { throw 'The saved previous legacy site contract changed before transition stop.' }
    }
    # 所有 ownership 都在第一次 Kill 前再次驗證，避免驗證半套後破壞舊路由。
    & $StopProcess ([int]$Contract.NgrokProcessId) 'Previous ngrok'
    $Contract.NgrokStopped = $true
    if ($Contract.Kind -eq 'Legacy') {
        & $StopProcess ([int]$Contract.SiteProcessId) 'Previous legacy site'
        $Contract.SiteStopped = $true
    }
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) { Remove-Item -LiteralPath $StatePath -Force }
}

function Restore-PreviousPublicSiteRoute {
    param(
        [Parameter(Mandatory)][object]$Contract,
        [Parameter(Mandatory)][object]$Paths,
        [scriptblock]$StartLegacy = $null,
        [scriptblock]$StartNgrok = $null,
        [scriptblock]$TestOrigin = $null,
        [scriptblock]$VerifyLegacy = $null,
        [scriptblock]$VerifyNgrok = $null,
        [scriptblock]$TestExternal = $null,
        [scriptblock]$StopFailedProcess = $null
    )
    if ($Contract.Kind -eq 'None') { return $true }
    if ($null -eq $StartLegacy) { $StartLegacy = { [AevryndWebCredentialProcess]::StartLegacySite($Contract.SiteExecutable,$Contract.SiteAssembly) }.GetNewClosure() }
    if ($null -eq $StartNgrok) { $StartNgrok = { [AevryndWebCredentialProcess]::StartNgrok($Paths.NgrokImage,$script:NgrokCredentialTarget,[int]$Contract.UpstreamPort) }.GetNewClosure() }
    if ($null -eq $TestOrigin) { $TestOrigin = { Test-PublicSiteOriginHealthy -Port 8792 } }
    if ($null -eq $VerifyLegacy) {
        $legacyVerifier = Get-Command Get-VerifiedLegacySiteProcess -CommandType Function
        $VerifyLegacy = { param($ProcessIdentifier) & $legacyVerifier -Paths $Paths -ExpectedProcessId $ProcessIdentifier }.GetNewClosure()
    }
    if ($null -eq $VerifyNgrok) {
        $ngrokVerifier = Get-Command Get-VerifiedPublicSiteProcess -CommandType Function
        $VerifyNgrok = { param($ProcessIdentifier) & $ngrokVerifier -ProcessId $ProcessIdentifier -Paths $Paths -UpstreamPort ([int]$Contract.UpstreamPort) -ExpectedHash ([string]$Contract.NgrokImageSha256) }.GetNewClosure()
    }
    if ($null -eq $TestExternal) { $TestExternal = { Test-PublicSiteExternal } }
    if ($null -eq $StopFailedProcess) {
        $StopFailedProcess = { param($ProcessIdentifier) $process=Get-Process -Id $ProcessIdentifier -ErrorAction SilentlyContinue; if ($null -ne $process) { $process.Kill($true); $null=$process.WaitForExit(10000) } }
    }
    $launchedSitePid = 0; $launchedNgrokPid = 0
    try {
        if ($Contract.Kind -eq 'Legacy' -and $Contract.SiteStopped) {
            $site = & $StartLegacy
            $launchedSitePid = [int]$site.Id
            for ($attempt=0; $attempt-lt 40 -and -not (& $TestOrigin); $attempt++) { Start-Sleep -Milliseconds 500 }
            if (-not (& $TestOrigin)) { throw 'Rollback legacy site did not become healthy.' }
            $restoredSite = & $VerifyLegacy $launchedSitePid
            if ($null -eq $restoredSite) { throw 'Rollback legacy health did not belong to the newly started exact process.' }
            $Contract.SiteProcessId = [int]$restoredSite.ProcessId
        }
        if ($Contract.NgrokStopped) {
            $ngrok = & $StartNgrok
            $launchedNgrokPid = [int]$ngrok.Id
            $ngrokPid = $launchedNgrokPid
        } else { $ngrokPid = [int]$Contract.NgrokProcessId }
        $verified = $null
        for ($attempt=0; $attempt-lt 20 -and $null -eq $verified; $attempt++) {
            $verified = & $VerifyNgrok $ngrokPid
            if ($null -eq $verified) { Start-Sleep -Milliseconds 250 }
        }
        if ($null -eq $verified -or -not (& $TestExternal)) { throw 'Rollback previous public route did not pass exact external verification.' }
        $Contract.NgrokProcessId = $ngrokPid
        return $true
    } catch {
        $restoreError = $_
        if ($launchedNgrokPid -gt 0) { & $StopFailedProcess $launchedNgrokPid }
        if ($launchedSitePid -gt 0) { & $StopFailedProcess $launchedSitePid }
        throw $restoreError
    }
}

function Invoke-PublicSiteRollbackTransaction {
    param(
        [Parameter(Mandatory)][scriptblock]$StopNewIis,
        [Parameter(Mandatory)][scriptblock]$RestoreIis,
        [Parameter(Mandatory)][scriptblock]$RestoreDirectories,
        [Parameter(Mandatory)][scriptblock]$RestoreTaskAndAcl,
        [Parameter(Mandatory)][scriptblock]$RestartPreviousRoute,
        [Parameter(Mandatory)][scriptblock]$VerifyPreviousRoute
    )
    & $StopNewIis
    & $RestoreIis
    & $RestoreDirectories
    & $RestoreTaskAndAcl
    & $RestartPreviousRoute
    & $VerifyPreviousRoute
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
