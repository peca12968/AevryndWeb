[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$productionSettingsPath = Join-Path $repoRoot 'artifacts\iis\appsettings.Production.json'

if (-not (Test-Path $productionSettingsPath)) { return }

sqllocaldb start MSSQLLocalDB | Out-Null
$instanceInfo = sqllocaldb info MSSQLLocalDB
$pipeName = [regex]::Match(($instanceInfo -join "`n"), 'np:\\\\.\\pipe\\[^\r\n]+').Value.Trim()
if (-not $pipeName) { throw '無法取得 LocalDB 具名管道。' }

$settings = Get-Content -LiteralPath $productionSettingsPath -Raw | ConvertFrom-Json
$settings.ConnectionStrings.Aevrynd = [regex]::Replace(
    $settings.ConnectionStrings.Aevrynd,
    '^Server=[^;]+;',
    "Server=$pipeName;")
$settings |
    ConvertTo-Json -Depth 3 |
    Set-Content -LiteralPath $productionSettingsPath -Encoding utf8
