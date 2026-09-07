. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$state = Get-PublicSiteRuntimeState -AllowLegacy
$paths = Get-PublicSitePaths
$owned = Resolve-PublicSiteStopProcess -RuntimeState $state -DomainProcesses @(Get-PublicSiteDomainProcesses) `
    -VerifyStateProcess {
        param($candidate)
        $port = if ($candidate.schemaVersion -eq 1) { 8792 } else { 8080 }
        $expectedHash = if ($candidate.schemaVersion -eq 3) { [string]$candidate.ngrokImageSha256 } else { '' }
        Get-VerifiedPublicSiteProcess -ProcessId ([int]$candidate.ngrokPid) -Paths $paths -UpstreamPort $port -ExpectedHash $expectedHash
    } `
    -VerifyDomainProcess { param($candidate) Get-VerifiedPublicSiteProcess -ProcessId ([int]$candidate.ProcessId) -Paths $paths -UpstreamPort 8080 }
if ($null -ne $owned) { $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop; $process.Kill($true); if (-not $process.WaitForExit(10000)) { throw 'Managed ngrok did not stop.' } }
if (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf) { Remove-Item -LiteralPath $script:PublicSiteState -Force }
Write-Output 'Managed ngrok stopped. IIS AevryndWeb remains available on loopback.'
