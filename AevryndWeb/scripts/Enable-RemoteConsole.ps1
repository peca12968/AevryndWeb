[CmdletBinding()]
param(
    [ValidateRange(5, 480)][int]$Minutes = 15,
    [ValidateSet('screen.read', 'input.text', 'keyboard.write', 'mouse.write', 'browser.input')]
    [string[]]$Capabilities = @('screen.read', 'input.text'),
    [string]$ValidationRoot = ''
)
$ErrorActionPreference = 'Stop'
$stateDirectory = if ($ValidationRoot) { Join-Path $ValidationRoot 'ProgramData' } else { 'C:\ProgramData\AevryndWeb' }
$statePath = Join-Path $stateDirectory 'remote-console-state.json'
$dataProtectionPath = if ($ValidationRoot) { Join-Path $ValidationRoot 'DataProtection' } else { Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'AevryndWeb\keys' }
$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
if ($Capabilities -contains 'mouse.write' -and $Capabilities -notcontains 'screen.read') { throw 'mouse.write requires screen.read.' }

foreach ($directory in @($stateDirectory, $dataProtectionPath)) {
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    & icacls.exe $directory /inheritance:r /grant:r "${currentIdentity}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Unable to secure directory: $directory" }
}
Get-ChildItem -LiteralPath $dataProtectionPath -File | ForEach-Object {
    & icacls.exe $_.FullName /inheritance:r /grant:r "${currentIdentity}:F" '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Unable to secure data protection key: $($_.FullName)" }
}

$nonceBytes = [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
$pairingNonce = [Convert]::ToHexString($nonceBytes)
$nonceHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($pairingNonce)))
$document = [ordered]@{
    Version = 1
    ActivationId = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    EnabledUntilUtc = [DateTimeOffset]::UtcNow.AddMinutes($Minutes)
    Capabilities = @($Capabilities | Sort-Object -Unique)
    PairingNonceHash = $nonceHash
    PairingNonceConsumed = $false
}
$temporaryPath = "$statePath.tmp"
$document | ConvertTo-Json -Compress | Set-Content -LiteralPath $temporaryPath -Encoding utf8NoBOM
Move-Item -LiteralPath $temporaryPath -Destination $statePath -Force
& icacls.exe $statePath /inheritance:r /grant:r "${currentIdentity}:F" '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
if ($LASTEXITCODE -ne 0) { Remove-Item -LiteralPath $statePath -Force; throw 'Unable to secure remote console state.' }

Write-Output "Remote Console enabled until $($document.EnabledUntilUtc.ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss zzz'))."
Write-Output "Capabilities: $([string]::Join(', ', $document.Capabilities))"
Write-Output "One-time pairing code: $pairingNonce"
Write-Warning 'The pairing code is displayed once. Disable immediately after use.'
