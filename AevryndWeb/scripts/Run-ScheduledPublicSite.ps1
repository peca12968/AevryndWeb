$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$diagnosticPath = Join-Path $root 'scheduled-startup-error.log'
try {
    & (Join-Path $PSScriptRoot 'Start-PublicSite.ps1')
    if ($LASTEXITCODE -notin @(0, $null)) { throw "Public-site startup returned exit code $LASTEXITCODE." }
    if (Test-Path -LiteralPath $diagnosticPath) { Remove-Item -LiteralPath $diagnosticPath -Force }
} catch {
    $_.Exception.Message | Set-Content -LiteralPath $diagnosticPath -Encoding utf8NoBOM
    throw
}
