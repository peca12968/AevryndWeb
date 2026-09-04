[CmdletBinding()]
param([string]$ValidationRoot = '')
$ErrorActionPreference = 'Stop'
$statePath = if ($ValidationRoot) { Join-Path (Join-Path $ValidationRoot 'ProgramData') 'remote-console-state.json' } else { 'C:\ProgramData\AevryndWeb\remote-console-state.json' }
$temporaryPath = "$statePath.tmp"
foreach ($path in @($statePath, $temporaryPath)) {
    if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force }
}
Write-Output 'Remote Console disabled. The website monitor revokes existing grants and releases injected modifiers within 500 ms.'
