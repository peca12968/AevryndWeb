. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$diagnosticPath = Join-Path $script:PublicSiteRoot 'startup-error.log'
trap {
    New-Item -ItemType Directory -Path $script:PublicSiteRoot -Force | Out-Null
    $_.Exception.Message | Set-Content -LiteralPath $diagnosticPath -Encoding utf8NoBOM
    exit 1
}

Add-PublicSiteCredentialInterop
$paths = Get-PublicSitePaths
if (-not [AevryndWebCredentialProcess]::Available($script:GmailCredentialTarget, 16, 64)) {
    throw 'Gmail credential is unavailable for the current Windows user.'
}
if (-not [AevryndWebCredentialProcess]::Available($script:NgrokCredentialTarget, 20, 512)) {
    throw 'Ngrok credential is unavailable for the current Windows user.'
}

$siteProcess = $null
$ngrokProcess = $null
$state = Get-PublicSiteRuntimeState
if ($null -ne $state) {
    $siteProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.sitePid) -Kind site -Paths $paths
    $ngrokProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.ngrokPid) -Kind ngrok -Paths $paths
}

if ($null -eq $siteProcess) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $script:PublicSitePort -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        $candidate = Get-CimInstance Win32_Process -Filter "ProcessId=$($listeners[0].OwningProcess)" -ErrorAction SilentlyContinue
        if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -cne '127.0.0.1' -or $null -eq $candidate -or
            $candidate.Name -cne 'dotnet.exe' -or -not (Test-PublicSiteLocal)) {
            throw 'Port 8792 is occupied by an unmanaged service.'
        }
        $siteProcess = $candidate
    } else {
        $siteProcess = [AevryndWebCredentialProcess]::StartSite($paths.Dotnet, $paths.Assembly, $script:GmailCredentialTarget)
        for ($attempt = 0; $attempt -lt 60 -and -not (Test-PublicSiteLocal); $attempt++) { Start-Sleep -Milliseconds 500 }
        if (-not (Test-PublicSiteLocal)) {
            if ($null -ne $siteProcess -and -not $siteProcess.HasExited) { $siteProcess.Kill($true) }
            throw 'AevryndWeb did not become locally healthy.'
        }
    }
}

if ($null -eq $ngrokProcess) {
    $existing = @(Get-CimInstance Win32_Process -Filter "Name='ngrok.exe'" -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0) {
        if ($existing.Count -ne 1 -or -not $existing[0].CommandLine.Contains("--domain=$script:PublicSiteDomain", [StringComparison]::Ordinal)) {
            throw 'An unrelated ngrok process prevents deterministic public routing.'
        }
        $ngrokProcess = $existing[0]
    } else {
        $ngrokProcess = [AevryndWebCredentialProcess]::StartNgrok($paths.Ngrok, $script:NgrokCredentialTarget)
    }
}

for ($attempt = 0; $attempt -lt 60 -and -not (Test-PublicSiteExternal); $attempt++) { Start-Sleep -Milliseconds 500 }
if (-not (Test-PublicSiteExternal)) { throw 'The public ngrok endpoint did not expose the AevryndWeb instance.' }

function Get-OwnedProcessId {
    param([Parameter(Mandatory)][object]$Process)
    if ($Process.PSObject.Properties.Name -contains 'ProcessId') { return [int]$Process.ProcessId }
    if ($Process.PSObject.Properties.Name -contains 'Id') { return [int]$Process.Id }
    throw 'A managed process did not expose a process identifier.'
}

Write-PublicSiteRuntimeState -SitePid (Get-OwnedProcessId $siteProcess) -NgrokPid (Get-OwnedProcessId $ngrokProcess)
if (Test-Path -LiteralPath $diagnosticPath) { Remove-Item -LiteralPath $diagnosticPath -Force }
Write-Output "AevryndWeb is healthy at https://$script:PublicSiteDomain/"
