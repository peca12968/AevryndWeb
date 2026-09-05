[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateLength(1,80)][string]$Task,
    [Parameter(Mandatory)][ValidateSet('working','blocked','completed','failed','cancelled')][string]$Status,
    [Parameter(Mandatory)][DateTimeOffset]$StartedUtc,
    [ValidateLength(0,120)][string]$Phase = '',
    [ValidateLength(0,240)][string]$EvidenceSummary = '',
    [Nullable[DateTimeOffset]]$EndedUtc,
    [ValidateRange(1,3600)][int]$Ttl = 900,
    [string]$StateDirectory = 'C:\ProgramData\Aevrynd\Codex'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# 僅由工作事件呼叫，不輪詢 Git、不啟動模型，也不依逾時推測結束狀態。
foreach ($value in @($Task,$Phase,$EvidenceSummary)) {
    if ($value -match '[\x00-\x1f\x7f]|://|@|[A-Za-z]:[\\/]|(?:\d{1,3}\.){3}\d{1,3}|(?i:password|bearer|private[_ -]?key|secret)') { throw 'Work summary contains non-public data' }
}
if ([string]::IsNullOrWhiteSpace($Task)) { throw 'Task cannot be empty' }
$root = [IO.Path]::GetFullPath($StateDirectory)
if (-not [IO.Directory]::Exists($root)) { throw 'State directory must already exist' }
if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'State directory cannot be a reparse point' }
$now = [DateTimeOffset]::UtcNow
$terminal = $Status -in @('completed','failed','cancelled')
if ($StartedUtc -gt $now.AddMinutes(1) -or $StartedUtc -eq [DateTimeOffset]::MinValue) { throw 'Invalid start time' }
if (-not $terminal -and $null -ne $EndedUtc) { throw 'Active work cannot have an end time' }
$ended = if ($terminal) { if ($null -ne $EndedUtc) { [DateTimeOffset]$EndedUtc } else { $now } } else { $null }
if ($terminal -and ($ended -lt $StartedUtc -or $ended -gt $now.AddMinutes(1))) { throw 'Invalid end time' }
foreach ($name in @('status.json','operations-history.json','.work-publish.lock')) {
    $path = Join-Path $root $name
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe state file' }
    }
}
$lock = [IO.File]::Open((Join-Path $root '.work-publish.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
function Write-AtomicJson([string]$Path,$Document,[int]$MaximumBytes) {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Document | ConvertTo-Json -Depth 10 -Compress))
    if ($bytes.Length -gt $MaximumBytes) { throw 'State exceeds size limit' }
    $temporary = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllBytes($temporary,$bytes)
        [IO.File]::Move($temporary,$Path,$true)
    } finally {
        if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}
try {
    $historyPath = Join-Path $root 'operations-history.json'
    $statusPath = Join-Path $root 'status.json'
    $events = @()
    if ([IO.File]::Exists($historyPath)) {
        if ((Get-Item -LiteralPath $historyPath).Length -gt 524288) { throw 'History exceeds size limit' }
        $history = Get-Content -LiteralPath $historyPath -Raw | ConvertFrom-Json
        if ($history.schemaVersion -ne 1 -or $null -eq $history.events -or @($history.events).Count -gt 500) { throw 'Invalid existing history' }
        $events = @($history.events)
    }
    $identity = { param($item) $item.name -ceq $Task.Trim() -and [DateTimeOffset]$item.startedAt -eq $StartedUtc }
    if ($terminal) {
        $event = [ordered]@{name=$Task.Trim();type='codex';startedAt=$StartedUtc.ToUniversalTime().ToString('o');updatedAt=$ended.ToUniversalTime().ToString('o');endedAt=$ended.ToUniversalTime().ToString('o');status=$Status;evidenceSummary=$(if($EvidenceSummary){$EvidenceSummary}else{$null})}
        # 相同工作與開始時間只保留一筆；先寫終態，讀取端再以終態排除舊 active。
        $events = @($events | Where-Object { -not (& $identity $_) }) + @($event)
        $events = @($events | Sort-Object { [DateTimeOffset]$_.startedAt } | Select-Object -Last 500)
        Write-AtomicJson $historyPath ([ordered]@{schemaVersion=1;events=$events}) 524288
    } else {
        if (@($events | Where-Object { & $identity $_ }).Count) { throw 'A terminal work identity cannot be restarted' }
        $document = [ordered]@{schemaVersion=1;status=$Status;task=$Task.Trim();phase=$(if($Phase){$Phase}else{$null});startedUtc=$StartedUtc.ToUniversalTime().ToString('o');updatedUtc=$now.ToString('o');ttl=$Ttl}
        Write-AtomicJson $statusPath $document 8192
    }
    Write-Output ('PUBLISHED {0} {1}' -f $Status,$Task.Trim())
} finally { $lock.Dispose() }
