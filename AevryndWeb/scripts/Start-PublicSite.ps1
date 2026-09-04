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
try { $null = Assert-IisConfiguration -Paths $paths } catch {
    throw "IIS site '$script:IisSiteName' is not started and healthy on 127.0.0.1:$script:PublicSitePort. The public-site task will not launch a second ASP.NET process."
}

$ngrokProcess = $null
$state = Get-PublicSiteRuntimeState
if ($null -ne $state) { $ngrokProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.ngrokPid) -Paths $paths -ExpectedHash ([string]$state.ngrokImageSha256) }
if ($null -eq $ngrokProcess) {
    $existing = @(Get-CimInstance Win32_Process -Filter "Name='ngrok.exe'" -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0) {
        if ($existing.Count -ne 1) { throw 'An unrelated ngrok process prevents deterministic public routing.' }
        $ngrokProcess = Get-VerifiedPublicSiteProcess -ProcessId ([int]$existing[0].ProcessId) -Paths $paths -UpstreamPort 8080
        if ($null -eq $ngrokProcess) { throw 'The existing ngrok executable, domain, or upstream is outside the managed contract.' }
    } else {
        $ngrokProcess = [AevryndWebCredentialProcess]::StartNgrok($paths.Ngrok, $script:NgrokCredentialTarget)
    }
}

for ($attempt = 0; $attempt -lt 60 -and -not (Test-PublicSiteExternal); $attempt++) { Start-Sleep -Milliseconds 500 }
if (-not (Test-PublicSiteExternal)) { throw 'The public ngrok endpoint did not expose the IIS AevryndWeb instance.' }
$processId = if ($ngrokProcess.PSObject.Properties.Name -contains 'ProcessId') { [int]$ngrokProcess.ProcessId } else { [int]$ngrokProcess.Id }
$verifiedNgrok = Get-VerifiedPublicSiteProcess -ProcessId $processId -Paths $paths -UpstreamPort 8080
if ($null -eq $verifiedNgrok) { throw 'The launched ngrok process did not match trusted AppX image, hash, and exact arguments.' }
Write-PublicSiteRuntimeState -NgrokPid $processId -NgrokImageSha256 $paths.NgrokHash
if (Test-Path -LiteralPath $diagnosticPath) { Remove-Item -LiteralPath $diagnosticPath -Force }
Write-Output "IIS AevryndWeb is healthy at https://$script:PublicSiteDomain/"
