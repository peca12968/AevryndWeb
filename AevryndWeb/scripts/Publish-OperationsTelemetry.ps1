#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('taichung','taoyuan')][string]$NodeId,
    [string]$Endpoint = 'https://sample-cupid-overdrawn.ngrok-free.dev/api/operations/telemetry',
    [string]$StatusPath = 'C:\ProgramData\Aevrynd\Codex\status.json',
    [string]$HistoryPath = 'C:\ProgramData\Aevrynd\Codex\operations-history.json',
    [switch]$Once,
    [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$uri = [Uri]$Endpoint
if ($uri.AbsolutePath -cne '/api/operations/telemetry' -or $uri.Query -or $uri.Fragment -or
    (($uri.Scheme -cne 'https' -or $uri.Host -cne 'sample-cupid-overdrawn.ngrok-free.dev') -and
     ($uri.Scheme -cne 'http' -or $uri.Host -notin @('127.0.0.1','localhost')))) { throw 'Telemetry endpoint is outside the fixed allowlist.' }
$telemetryRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'Aevrynd\OperationsTelemetry'
$settingsPath = Join-Path $telemetryRoot "$NodeId-settings.json"

function Test-SafeTelemetryAcl([string]$Path) {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $administrators = [Security.Principal.SecurityIdentifier]::new([Security.Principal.WellKnownSidType]::BuiltinAdministratorsSid, $null)
    $system = [Security.Principal.SecurityIdentifier]::new([Security.Principal.WellKnownSidType]::LocalSystemSid, $null)
    $acl = Get-Acl -LiteralPath $Path
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($owner -notin @($current.Value,$administrators.Value,$system.Value)) { return $false }
    foreach ($rule in $acl.Access) {
        if ($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
            $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -notin @($current.Value,$administrators.Value,$system.Value)) { return $false }
    }
    return $true
}

function Test-SafeTelemetryFile([string]$Path, [int]$Maximum) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return $item.Length -gt 0 -and $item.Length -le $Maximum -and
        -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and (Test-SafeTelemetryAcl $Path)
}

function Test-SafeText([string]$Value, [int]$Maximum) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt $Maximum -or $Value.Contains('://') -or $Value.Contains('@') -or $Value.Contains(':\')) { return $false }
    foreach ($character in $Value.ToCharArray()) { if ([char]::IsControl($character)) { return $false } }
    return $Value -notmatch '(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)'
}

function Read-WorkState([DateTimeOffset]$Now) {
    $active = @(); $history = @()
    if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
        $item = Get-Item -LiteralPath $StatusPath -Force
        if ($item.Length -ge 2 -and $item.Length -le 8192 -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $status = Get-Content -Raw -LiteralPath $StatusPath | ConvertFrom-Json
            $updated = [DateTimeOffset]$status.updatedUtc
            if ($status.schemaVersion -eq 1 -and $status.status -in @('working','blocked','completed','failed','cancelled') -and (Test-SafeText ([string]$status.task) 80) -and
                $updated -le $Now.AddMinutes(1) -and [int]$status.ttl -ge 1 -and [int]$status.ttl -le 3600) {
                $started = if ($null -ne $status.PSObject.Properties['startedUtc']) { [DateTimeOffset]$status.startedUtc } else { $updated }
                if ($status.status -in @('working','blocked') -and $Now.Subtract($updated).TotalSeconds -le [int]$status.ttl) {
                    $active = @([ordered]@{ Name=[string]$status.task; Type='codex'; Host=$NodeId; StartedAt=$started; UpdatedAt=$updated; EndedAt=$null; Status=[string]$status.status; EvidenceSummary=$null })
                } elseif ($status.status -in @('completed','failed','cancelled')) {
                    $history += [ordered]@{ Name=[string]$status.task; Type='codex'; Host=$NodeId; StartedAt=$started; UpdatedAt=$updated; EndedAt=$updated; Status=[string]$status.status; EvidenceSummary=$null }
                } elseif ($Now.Subtract($updated).TotalSeconds -gt [int]$status.ttl) {
                    $ended = $updated.AddSeconds([int]$status.ttl)
                    $history += [ordered]@{ Name=[string]$status.task; Type='codex'; Host=$NodeId; StartedAt=$started; UpdatedAt=$ended; EndedAt=$ended; Status='cancelled'; EvidenceSummary='Work status expired without a terminal result.' }
                }
            }
        }
    }
    if (Test-Path -LiteralPath $HistoryPath -PathType Leaf) {
        $item = Get-Item -LiteralPath $HistoryPath -Force
        if ($item.Length -ge 2 -and $item.Length -le 131072 -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $document = Get-Content -Raw -LiteralPath $HistoryPath | ConvertFrom-Json
            if ($document.schemaVersion -ne 1 -or @($document.events).Count -gt 100) { throw 'Work history document is outside schema limits.' }
            foreach ($event in @($document.events)) {
                if (-not (Test-SafeText ([string]$event.name) 80) -or -not (Test-SafeText ([string]$event.type) 40) -or $event.status -notin @('completed','failed','cancelled')) { throw 'Work history event is invalid.' }
                $evidence = if ($null -eq $event.evidenceSummary) { $null } else { [string]$event.evidenceSummary }
                if ($null -ne $evidence -and -not (Test-SafeText $evidence 240)) { throw 'Work history evidence is invalid.' }
                $history += [ordered]@{ Name=[string]$event.name; Type=[string]$event.type; Host=$NodeId; StartedAt=[DateTimeOffset]$event.startedAt; UpdatedAt=[DateTimeOffset]$event.updatedAt; EndedAt=[DateTimeOffset]$event.endedAt; Status=[string]$event.status; EvidenceSummary=$evidence }
            }
            $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            $activeIdentity = if ($active.Count -eq 1) { "$($active[0].Name)`n$(([DateTimeOffset]$active[0].StartedAt).UtcDateTime.ToString('O'))" } else { $null }
            $history = @($history | Sort-Object StartedAt -Descending | Where-Object {
                $identity = "$(($_.Name))`n$(([DateTimeOffset]$_.StartedAt).UtcDateTime.ToString('O'))"
                $identity -cne $activeIdentity -and $seen.Add($identity)
            } | Select-Object -First 100)
        }
    }
    return [pscustomobject]@{ Active=$active; History=$history }
}

function Get-GpuPercent {
    $command = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if ($null -eq $command) { return $null }
    $values = @(& $command.Source '--query-gpu=utilization.gpu' '--format=csv,noheader,nounits' 2>$null | ForEach-Object { $parsed=0.0; if ([double]::TryParse($_,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$parsed)) { $parsed } })
    if ($LASTEXITCODE -ne 0 -or $values.Count -eq 0) { return $null }
    return [Math]::Round(($values | Measure-Object -Average).Average,1)
}

function Send-Heartbeat {
    $now = [DateTimeOffset]::UtcNow
    $processor = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" -ErrorAction Stop
    $memory = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $work = Read-WorkState $now
    $payload = [ordered]@{ version=1; nodeId=$NodeId; measurement='measured'; cpuPercent=[Math]::Round([double]$processor.PercentProcessorTime,1); ramPercent=[Math]::Round(100.0*(1.0-[double]$memory.FreePhysicalMemory/[double]$memory.TotalVisibleMemorySize),1); gpuPercent=Get-GpuPercent; sampledUtc=$now; activeWork=@($work.Active); history=@($work.History) }
    $json = $payload | ConvertTo-Json -Depth 6 -Compress
    if ($WhatIf) { Write-Output ([pscustomobject]@{ version=1; nodeId=$NodeId; measurement='measured'; cpuPercent=$payload.cpuPercent; ramPercent=$payload.ramPercent; gpuPercent=$payload.gpuPercent; sampledUtc=$now; activeWorkCount=$work.Active.Count; historyCount=$work.History.Count } | ConvertTo-Json -Compress); return }
    if (-not (Test-Path -LiteralPath $telemetryRoot -PathType Container)) { throw 'Telemetry key directory is unavailable.' }
    $rootItem = Get-Item -LiteralPath $telemetryRoot -Force
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or -not (Test-SafeTelemetryAcl $telemetryRoot) -or
        -not (Test-SafeTelemetryFile $settingsPath 512)) { throw 'Telemetry key settings are unavailable or unsafe.' }
    $keySettings = Get-Content -Raw -LiteralPath $settingsPath | ConvertFrom-Json
    if (@($keySettings.PSObject.Properties).Count -ne 3 -or $keySettings.version -ne 1 -or
        $keySettings.nodeId -cne $NodeId -or [string]$keySettings.keyName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$') { throw 'Telemetry key settings are invalid.' }
    $key = $null
    $ecdsa = $null
    try {
        $key = [Security.Cryptography.CngKey]::Open([string]$keySettings.keyName, [Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider, [Security.Cryptography.CngKeyOpenOptions]::UserKey)
        if ($key.Algorithm.Algorithm -cne 'ECDSA_P256' -or $key.KeySize -ne 256 -or
            $key.ExportPolicy -ne [Security.Cryptography.CngExportPolicies]::None -or
            -not ($key.KeyUsage -band [Security.Cryptography.CngKeyUsages]::Signing)) { throw 'Telemetry signing key violates policy.' }
        $ecdsa = [Security.Cryptography.ECDsaCng]::new($key)
        $publicKey = $ecdsa.ExportSubjectPublicKeyInfo()
        $keyId = [Convert]::ToHexString(([Security.Cryptography.SHA256]::HashData($publicKey))[0..15]).ToLowerInvariant()
        $timestamp = $now.ToUnixTimeSeconds().ToString([Globalization.CultureInfo]::InvariantCulture)
        $nonceBytes = [Security.Cryptography.RandomNumberGenerator]::GetBytes(18)
        $nonce = [Convert]::ToBase64String($nonceBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
        $body = [Text.Encoding]::UTF8.GetBytes($json)
        $prefix = [Text.Encoding]::UTF8.GetBytes("POST`n/api/operations/telemetry`n$NodeId`n$timestamp`n$nonce`n")
        $signed = [byte[]]::new($prefix.Length+$body.Length); [Array]::Copy($prefix,0,$signed,0,$prefix.Length); [Array]::Copy($body,0,$signed,$prefix.Length,$body.Length)
        $signatureBytes = $ecdsa.SignData($signed, [Security.Cryptography.HashAlgorithmName]::SHA256, [Security.Cryptography.DSASignatureFormat]::IeeeP1363FixedFieldConcatenation)
        $signature = 'ecdsa-p256-sha256=' + [Convert]::ToBase64String($signatureBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
        Invoke-WebRequest -UseBasicParsing -Method Post -Uri $uri -ContentType 'application/json' -Body $body -Headers @{ 'X-Aevrynd-Node'=$NodeId; 'X-Aevrynd-Timestamp'=$timestamp; 'X-Aevrynd-Nonce'=$nonce; 'X-Aevrynd-Key-Id'=$keyId; 'X-Aevrynd-Signature'=$signature } -TimeoutSec 8 | Out-Null
    } finally {
        if ($null -ne $ecdsa) { $ecdsa.Dispose() }
        if ($null -ne $key) { $key.Dispose() }
    }
}

do { try { Send-Heartbeat } catch { Write-Warning "Telemetry cycle failed: $($_.Exception.Message)" }; if (-not $Once -and -not $WhatIf) { Start-Sleep -Seconds 10 } } while (-not $Once -and -not $WhatIf)
