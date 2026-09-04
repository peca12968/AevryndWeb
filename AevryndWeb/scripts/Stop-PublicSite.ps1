. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$state = Get-PublicSiteRuntimeState -AllowLegacy
$owned = $null
if ($null -ne $state) {
    $port = if ($state.schemaVersion -eq 1) { 8792 } else { 8080 }
    $expectedHash = if ($state.schemaVersion -eq 3) { [string]$state.ngrokImageSha256 } else { '' }
    $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.ngrokPid) -Paths (Get-PublicSitePaths) -UpstreamPort $port -ExpectedHash $expectedHash
    if ($null -eq $owned) { throw 'Runtime state exists, but ngrok process ownership cannot be proven.' }
} else {
    $domainProcesses = @(Get-CimInstance Win32_Process -Filter "Name='ngrok.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine.Contains("--domain=$script:PublicSiteDomain",[StringComparison]::Ordinal) })
    if ($domainProcesses.Count -gt 0) {
        if ($domainProcesses.Count -ne 1) { throw 'Multiple ngrok processes claim the fixed domain.' }
        $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$domainProcesses[0].ProcessId) -Paths (Get-PublicSitePaths) -UpstreamPort 8080
        if ($null -eq $owned) { throw 'Domain ngrok has an unexpected executable or upstream; nothing was stopped.' }
    }
}
if ($null -ne $owned) { $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop; $process.Kill($true); if (-not $process.WaitForExit(10000)) { throw 'Managed ngrok did not stop.' } }
if (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf) { Remove-Item -LiteralPath $script:PublicSiteState -Force }
Write-Output 'Managed ngrok stopped. IIS AevryndWeb remains available on loopback.'
