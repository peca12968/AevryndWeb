$ErrorActionPreference = 'Stop'
$root = 'D:\Download\Aevrynd'
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $root 'engine\assets\characters\female-next\source')).TrimEnd('\')
$mirrorRoot = [IO.Path]::GetFullPath((Join-Path $root 'sites-engine-journey\assets-source\aevrynd-character\female-next')).TrimEnd('\')
$rawRoot = [IO.Path]::GetFullPath((Join-Path $sourceRoot 'study-vitruvian-textures-source4k')).TrimEnd('\')
$originalRoot = [IO.Path]::GetFullPath((Join-Path $root 'Reference\character\charmorph-vitruvian-cc0\textures-4k')).TrimEnd('\')
$evidenceRoot = Join-Path $root 'Evidence\character-female-next\r0073-complete-skin'
$freeBefore = (Get-PSDrive -Name D).Free
$records = [Collections.Generic.List[object]]::new()
function Assert-Child([string]$path, [string]$parent) {
    $absolute = [IO.Path]::GetFullPath($path)
    if (-not $absolute.StartsWith($parent+'\',[StringComparison]::OrdinalIgnoreCase)) { throw "Outside verified directory: $absolute" }
    return $absolute
}
function Replace-WithExactHardlink([string]$source, [string]$mirror, [string]$verifiedHash) {
    $temporary = $mirror+'.r73-hardlink'
    if (Test-Path -LiteralPath $temporary) { throw "Temporary path already exists: $temporary" }
    New-Item -ItemType HardLink -Path $temporary -Target $source | Out-Null
    if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash -ne $verifiedHash) { throw 'New link hash differs' }
    try { Move-Item -LiteralPath $temporary -Destination $mirror -Force }
    catch {
        if (-not (Test-Path -LiteralPath $mirror)) { Move-Item -LiteralPath $temporary -Destination $mirror }
        elseif (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
        throw
    }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $verifiedHash -or (Get-FileHash -LiteralPath $mirror -Algorithm SHA256).Hash -ne $verifiedHash) { throw 'Post-link bytes differ' }
}
# Only immutable female-next history mirrors. Active/formal/scoped foundations
# and all r73 production outputs are excluded; no file contents are changed.
foreach ($item in (Get-ChildItem -LiteralPath $sourceRoot -File -Filter '*.blend' | Sort-Object LastWriteTime -Descending)) {
    if ((Get-PSDrive -Name D).Free -ge 4GB) { break }
    if ($item.Name -notmatch '^aevrynd-female-next-r(\d{4})-.*\.blend$') { continue }
    $revision = [int]$Matches[1]
    if ($revision -ge 73 -or $revision -in @(1,51,65,68,69)) { continue }
    $source = Assert-Child $item.FullName $sourceRoot
    $mirror = Assert-Child (Join-Path $mirrorRoot $item.Name) $mirrorRoot
    if (-not (Test-Path -LiteralPath $mirror -PathType Leaf)) { continue }
    $other = Get-Item -LiteralPath $mirror
    if ($other.Length -ne $item.Length -or $other.LinkType -eq 'HardLink') { continue }
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $mirror -Algorithm SHA256).Hash -ne $sourceHash) { continue }
    Replace-WithExactHardlink $source $mirror $sourceHash
    $records.Add([ordered]@{kind='identical-immutable-history-mirror';source=$source;mirror=$mirror;sha256=$sourceHash;duplicateBytesReleased=$item.Length;contentsChanged=$false})
}
# Repair the current failed byte-copy using the immutable original EXR files.
# Existing targets are accepted only as outputs created by this r73 job.
$metadata = Get-Content -LiteralPath (Join-Path $root 'Evidence\character-female-next\r0057-coherent-foundation\texture-derivatives.json') -Raw | ConvertFrom-Json
foreach ($entry in $metadata.files) {
    if ($entry.file -notmatch '^(Light_Skin_Color|Skin_Roughness|Skin_Height)\.100[1-4]\.exr$') { continue }
    $source = Assert-Child (Join-Path $originalRoot $entry.file) $originalRoot
    $target = Assert-Child (Join-Path $rawRoot $entry.file) $rawRoot
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ($hash.ToLowerInvariant() -ne $entry.sourceSHA256) { throw "Original source hash differs: $source" }
    $oldBytes = 0
    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target
        if ($item.LinkType -eq 'HardLink') {
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $hash) { throw 'Existing source link differs' }
            continue
        }
        if ($item.CreationTimeUtc -lt [DateTimeOffset]::Parse('2026-10-20T05:56:00Z').UtcDateTime) { throw "Not a current r73 copy: $target" }
        $oldBytes = $item.Length
    }
    Replace-WithExactHardlink $source $target $hash
    $records.Add([ordered]@{kind='original-source-map-hardlink';source=$source;mirror=$target;sha256=$hash;oldFailedCopyBytes=$oldBytes;sourceContentsChanged=$false;targetNowExactSource=$true})
}
$existingPairs = [Collections.Generic.List[object]]::new()
foreach ($item in (Get-ChildItem -LiteralPath $sourceRoot -File -Filter '*.blend')) {
    if ($item.Name -notmatch '^aevrynd-female-next-r(\d{4})-.*\.blend$') { continue }
    if ([int]$Matches[1] -ge 73 -or [int]$Matches[1] -in @(1,51,65,68,69)) { continue }
    $mirror = Assert-Child (Join-Path $mirrorRoot $item.Name) $mirrorRoot
    if (-not (Test-Path -LiteralPath $mirror)) { continue }
    $other = Get-Item -LiteralPath $mirror
    if ($other.LinkType -ne 'HardLink') { continue }
    $hash = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $mirror -Algorithm SHA256).Hash -ne $hash) { throw 'Final mirror hash differs' }
    $existingPairs.Add([ordered]@{source=$item.FullName;mirror=$mirror;sha256=$hash;bytes=$item.Length;observedLinkTargets=$other.Target})
}
$receipt = [ordered]@{observedBeforeInitialRecoveryFreeBytes=933888;freeBeforeThisInvocationBytes=$freeBefore;freeAfterBytes=(Get-PSDrive -Name D).Free;modelContentsOrHistoricalVersionsDeleted=$false;activeAndFormalSourcePathsExcluded=$true;method='NTFS same-volume hardlinks after SHA256 equality; replace only duplicate mirrors/current failed copies';initialRecoveryNote='Model deduplication completed before the first invocation stopped at a raw-copy timestamp guard. PowerShell local-time conversion of a Z DateTime literal was corrected to explicit DateTimeOffset.UtcDateTime; final existing link pairs are independently rehashed below.';operationsThisInvocation=$records;verifiedFinalHistoricalMirrorPairs=$existingPairs}
$receipt | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'disk-recovery.json') -Encoding utf8
Write-Output ('Recovered free bytes: '+$receipt.freeAfterBytes+'; hardlink operations: '+$records.Count)
