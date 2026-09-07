. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$diagnosticPath = Join-Path $script:PublicSiteRoot 'startup-error.log'
trap {
    New-Item -ItemType Directory -Path $script:PublicSiteRoot -Force | Out-Null
    $_.Exception.Message | Set-Content -LiteralPath $diagnosticPath -Encoding utf8NoBOM
    exit 1
}

Add-PublicSiteCredentialInterop
$paths = Get-PublicSitePaths
if (-not [AevryndWebCredentialProcess]::Available($script:NgrokCredentialTarget, 20, 512)) {
    throw 'Ngrok credential is unavailable for the current Windows user.'
}
$iisError = 'IIS configuration has not been verified yet.'
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $null = Assert-IisConfiguration -Paths $paths
        if (Test-PublicSiteLocal) { $iisError = $null; break }
        $iisError = 'The IIS readiness payload did not satisfy the production credential contract.'
    } catch { $iisError = $_.Exception.Message }
    Start-Sleep -Milliseconds 1000
}
if ($iisError) {
    throw "IIS site '$script:IisSiteName' did not become healthy on exact origin http://127.0.0.1:$script:PublicSitePort within 60 seconds. $iisError"
}

$state = Get-PublicSiteRuntimeState
$resolution = Resolve-PublicSiteStartProcess -RuntimeState $state -DomainProcesses @(Get-PublicSiteDomainProcesses) `
    -VerifyStateProcess { param($candidate) Get-VerifiedPublicSiteProcess -ProcessId ([int]$candidate.ngrokPid) -Paths $paths -ExpectedHash ([string]$candidate.ngrokImageSha256) } `
    -VerifyDomainProcess { param($candidate) Get-VerifiedPublicSiteProcess -ProcessId ([int]$candidate.ProcessId) -Paths $paths -UpstreamPort 8080 } `
    -StartProcess { [AevryndWebCredentialProcess]::StartNgrok($paths.NgrokImage, $script:NgrokCredentialTarget) }
$ngrokProcess = $resolution.Process

$processId = if ($ngrokProcess.PSObject.Properties.Name -contains 'ProcessId') { [int]$ngrokProcess.ProcessId } else { [int]$ngrokProcess.Id }
$verifiedNgrok = $null
for ($attempt = 0; $attempt -lt 20 -and $null -eq $verifiedNgrok; $attempt++) {
    $verifiedNgrok = Get-VerifiedPublicSiteProcess -ProcessId $processId -Paths $paths -UpstreamPort 8080
    if ($null -eq $verifiedNgrok) { Start-Sleep -Milliseconds 250 }
}
if ($null -eq $verifiedNgrok) {
    if ($resolution.Launched) { $failed=Get-Process -Id $processId -ErrorAction SilentlyContinue; if ($null -ne $failed) { $failed.Kill($true); $null=$failed.WaitForExit(10000) } }
    throw 'The launched ngrok process did not match the trusted image and exact IIS origin arguments.'
}

for ($attempt = 0; $attempt -lt 60 -and -not (Test-PublicSiteExternal); $attempt++) { Start-Sleep -Milliseconds 500 }
if (-not (Test-PublicSiteExternal)) {
    if ($resolution.Launched) { $failed=Get-Process -Id $processId -ErrorAction SilentlyContinue; if ($null -ne $failed) { $failed.Kill($true); $null=$failed.WaitForExit(10000) } }
    throw 'The public ngrok endpoint did not expose the IIS AevryndWeb instance.'
}
Write-PublicSiteRuntimeState -NgrokPid $processId -NgrokImageSha256 $paths.NgrokHash
if (Test-Path -LiteralPath $diagnosticPath) { Remove-Item -LiteralPath $diagnosticPath -Force }
Write-Output "IIS AevryndWeb is healthy at https://$script:PublicSiteDomain/"
