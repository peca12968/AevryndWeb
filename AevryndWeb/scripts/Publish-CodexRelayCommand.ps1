[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^https://')][string]$PortalUrl,
    [Parameter(Mandatory)][ValidateSet('taichung','taoyuan')][string]$NodeId,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')][string]$CommandId,
    [Parameter(Mandatory)][ValidateCount(1,32)][string[]]$OwnedFiles,
    [Parameter(Mandatory)][ValidateLength(1,8192)][string]$Task,
    [Parameter(Mandatory)][string]$SecretPath
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SecretPath -PathType Leaf)) { throw 'Publisher secret file is unavailable.' }
if ((Get-Item -LiteralPath $SecretPath).Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) { throw 'Publisher secret cannot be a reparse point.' }
$acl = Get-Acl -LiteralPath $SecretPath
$currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$trustedSids = @($currentSid, 'S-1-5-18', 'S-1-5-32-544')
$ownerSid = $acl.Owner
try { $ownerSid = ([Security.Principal.NTAccount]$acl.Owner).Translate([Security.Principal.SecurityIdentifier]).Value } catch { }
if ($trustedSids -notcontains $ownerSid) { throw 'Publisher secret owner is not trusted.' }
foreach ($rule in $acl.Access) {
    if ($rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow) { continue }
    $ruleSid = $rule.IdentityReference.Value
    try { $ruleSid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value } catch { }
    if ($trustedSids -notcontains $ruleSid -and $rule.FileSystemRights -ne 0) { throw 'Publisher secret ACL grants access to an untrusted identity.' }
}
$secretText = (Get-Content -LiteralPath $SecretPath -Raw).Trim()
try { $secret = [Convert]::FromBase64String($secretText) } catch { throw 'Publisher secret must be Base64.' }
if ($secret.Length -lt 32 -or $secret.Length -gt 64) { throw 'Publisher secret must decode to 32-64 bytes.' }

foreach ($ownedFile in $OwnedFiles) {
    if ($ownedFile.Length -gt 260 -or [IO.Path]::IsPathRooted($ownedFile) -or $ownedFile -split '[\\/]' -contains '..') {
        throw "Owned file must be a bounded repository-relative path: $ownedFile"
    }
}

$payload = [ordered]@{ commandId = $CommandId; nodeId = $NodeId; ownedFiles = @($OwnedFiles); task = $Task }
$json = $payload | ConvertTo-Json -Compress -Depth 4
$body = [Text.Encoding]::UTF8.GetBytes($json)
if ($body.Length -gt 16384) { throw 'Command payload exceeds 16384 UTF-8 bytes.' }
$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString([Globalization.CultureInfo]::InvariantCulture)
$nonce = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)).TrimEnd('=').Replace('+','-').Replace('/','_')
$path = '/api/codex-relay/publisher-commands'
$prefix = [Text.Encoding]::UTF8.GetBytes("POST`n$path`n$timestamp`n$nonce`n")
$signed = [byte[]]::new($prefix.Length + $body.Length)
[Array]::Copy($prefix, 0, $signed, 0, $prefix.Length); [Array]::Copy($body, 0, $signed, $prefix.Length, $body.Length)
try {
    $hmac = [Security.Cryptography.HMACSHA256]::new($secret)
    $signature = 'sha256=' + [Convert]::ToHexString($hmac.ComputeHash($signed)).ToLowerInvariant()
    Invoke-WebRequest -Method Post -Uri ($PortalUrl.TrimEnd('/') + $path) -ContentType 'application/json' -Body $body -Headers @{
        'X-Aevrynd-Timestamp' = $timestamp; 'X-Aevrynd-Nonce' = $nonce; 'X-Aevrynd-Signature' = $signature
    } | Select-Object StatusCode, Content
}
finally {
    if ($null -ne $hmac) { $hmac.Dispose() }
    [Security.Cryptography.CryptographicOperations]::ZeroMemory($secret)
    [Security.Cryptography.CryptographicOperations]::ZeroMemory($signed)
}
