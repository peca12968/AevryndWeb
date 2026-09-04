$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$diagnosticPath = Join-Path $root 'scheduled-startup-error.log'
try {
    $assembly = Join-Path $root 'publish\AevryndWeb.dll'
    if (-not (Test-Path -LiteralPath $assembly -PathType Leaf)) {
        throw "Scheduled startup cannot access the published assembly: $assembly"
    }
    & (Join-Path $PSScriptRoot 'Start-PublicSite.ps1')
    if ($LASTEXITCODE -notin @(0, $null)) { throw "Public-site startup returned exit code $LASTEXITCODE." }
    if (Test-Path -LiteralPath $diagnosticPath) { Remove-Item -LiteralPath $diagnosticPath -Force }
} catch {
    $_.Exception.Message | Set-Content -LiteralPath $diagnosticPath -Encoding utf8NoBOM
    throw
}
