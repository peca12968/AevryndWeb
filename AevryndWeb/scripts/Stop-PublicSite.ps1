. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$paths = Get-PublicSitePaths
$state = Get-PublicSiteRuntimeState
if ($null -eq $state) {
    Write-Output 'AevryndWeb has no managed runtime state.'
    return
}

$ngrokProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.ngrokPid) -Kind ngrok -Paths $paths
$siteProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.sitePid) -Kind site -Paths $paths
foreach ($process in @($ngrokProcess, $siteProcess)) {
    if ($null -ne $process) {
        $owned = Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue
        if ($null -ne $owned) {
            $owned.Kill($true)
            $owned.WaitForExit(10000)
        }
    }
}
Remove-Item -LiteralPath $script:PublicSiteState -Force
Write-Output 'AevryndWeb managed processes stopped.'
