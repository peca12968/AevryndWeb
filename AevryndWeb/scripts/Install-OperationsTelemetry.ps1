#requires -Version 7.0
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][ValidateSet('taichung','taoyuan')][string]$NodeId,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')][string]$KeyName = "Aevrynd-OperationsTelemetry-$NodeId-v1",
    [switch]$EnrollOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot 'Publish-OperationsTelemetry.ps1'
$root = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'Aevrynd\OperationsTelemetry'
$publisher = Join-Path $root 'Publish-OperationsTelemetry.ps1'
$settingsPath = Join-Path $root "$NodeId-settings.json"
$enrollmentPath = Join-Path $root "$NodeId-enrollment.json"
$taskName = "Aevrynd Operations Telemetry ($NodeId)"
$pwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Telemetry publisher source is missing.' }
if (-not (Test-Path -LiteralPath $pwsh -PathType Leaf)) { throw "PowerShell 7 is required at the fixed path: $pwsh" }
if ($WhatIfPreference) {
    Write-Output "What if: create or reuse a non-exportable ECDSA P-256 key for $NodeId and write a public enrollment document$(if (-not $EnrollOnly) { ', then stage the publisher and task' })."
    return
}
if (-not $PSCmdlet.ShouldProcess($taskName, 'Install outbound-only ECDSA telemetry publisher and create public enrollment')) { return }

if (Test-Path -LiteralPath $root) {
    $rootItem = Get-Item -LiteralPath $root -Force
    if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Telemetry directory is not a safe physical directory.' }
} else { New-Item -ItemType Directory -Path $root | Out-Null }

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $root /inheritance:r /grant:r "${currentUser}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Unable to secure telemetry publisher directory.' }
foreach ($path in @($publisher,$settingsPath,$enrollmentPath)) {
    if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'A telemetry target file is a reparse point.'
    }
}

# CNG persisted user key 由 Windows KSP 與使用者 ACL 保護，明確禁止私鑰匯出。
$key = $null
try {
    if ([Security.Cryptography.CngKey]::Exists($KeyName, [Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider, [Security.Cryptography.CngKeyOpenOptions]::UserKey)) {
        $key = [Security.Cryptography.CngKey]::Open($KeyName, [Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider, [Security.Cryptography.CngKeyOpenOptions]::UserKey)
    } else {
        $parameters = [Security.Cryptography.CngKeyCreationParameters]::new()
        $parameters.Provider = [Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider
        $parameters.ExportPolicy = [Security.Cryptography.CngExportPolicies]::None
        $parameters.KeyUsage = [Security.Cryptography.CngKeyUsages]::Signing
        $parameters.KeyCreationOptions = [Security.Cryptography.CngKeyCreationOptions]::None
        $key = [Security.Cryptography.CngKey]::Create([Security.Cryptography.CngAlgorithm]::ECDsaP256, $KeyName, $parameters)
    }
    if ($key.Algorithm.Algorithm -cne 'ECDSA_P256' -or $key.KeySize -ne 256 -or
        $key.ExportPolicy -ne [Security.Cryptography.CngExportPolicies]::None -or
        -not ($key.KeyUsage -band [Security.Cryptography.CngKeyUsages]::Signing)) { throw 'Persisted telemetry key violates the ECDSA P-256 non-exportable policy.' }

    $ecdsa = [Security.Cryptography.ECDsaCng]::new($key)
    try { $publicKey = $ecdsa.ExportSubjectPublicKeyInfo() } finally { $ecdsa.Dispose() }
    $keyId = [Convert]::ToHexString(([Security.Cryptography.SHA256]::HashData($publicKey))[0..15]).ToLowerInvariant()
    $createdUtc = [DateTimeOffset]::UtcNow
    $settings = [ordered]@{ version=1; nodeId=$NodeId; keyName=$KeyName }
    $enrollment = [ordered]@{ version=1; nodeId=$NodeId; algorithm='ECDSA-P256-SHA256'; keyId=$keyId; publicKey=[Convert]::ToBase64String($publicKey); createdUtc=$createdUtc }

    $enrollment | ConvertTo-Json -Compress | Set-Content -LiteralPath $enrollmentPath -Encoding utf8NoBOM
    if ($EnrollOnly) {
        Write-Output "Public enrollment prepared for $NodeId without changing the publisher task: $enrollmentPath"
        return
    }
    Copy-Item -LiteralPath $source -Destination $publisher -Force
    $settings | ConvertTo-Json -Compress | Set-Content -LiteralPath $settingsPath -Encoding utf8NoBOM
    foreach ($path in @($publisher,$settingsPath,$enrollmentPath)) {
        $item = Get-Item -LiteralPath $path -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'A staged telemetry file is a reparse point.' }
    }

    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -File `"$publisher`" -NodeId $NodeId"
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $taskSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $taskSettings -Description 'Sends ECDSA-signed bounded telemetry outbound; opens no listener.' -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-Output "Telemetry publisher prepared for $NodeId. Public enrollment: $enrollmentPath"
} finally {
    if ($null -ne $key) { $key.Dispose() }
}
