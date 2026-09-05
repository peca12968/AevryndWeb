[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [string]$StateDirectory='C:\ProgramData\AevryndWeb\operations'
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
# 由主代理在派工或核對事件後一次發布；不輪詢 GitHub、不啟動任何工作或模型。
$inputFile=Get-Item -LiteralPath $InputPath
$directory=Get-Item -LiteralPath $StateDirectory
if($inputFile.PSIsContainer -or $inputFile.Length -gt 262144 -or -not $directory.PSIsContainer -or
   ($inputFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe schedule input or directory'}
$document=Get-Content -LiteralPath $inputFile.FullName -Raw | ConvertFrom-Json
function Assert-Keys($Value,[string[]]$Keys){
    if($null -eq $Value){throw 'Null schedule object'}
    $actual=@($Value.PSObject.Properties.Name)
    if($actual.Count -ne $Keys.Count -or @($actual|Where-Object {$_ -cnotin $Keys}).Count){throw 'Invalid schedule keys'}
}
function Assert-Text($Value,[int]$Maximum){
    if($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt $Maximum -or
       $Value -match '[\x00-\x1f\x7f]|://|@|[A-Za-z]:[\\/]|(?:\d{1,3}\.){3}\d{1,3}|-----BEGIN'){throw 'Invalid public schedule text'}
}
$hasVerified=@($document.PSObject.Properties.Name) -ccontains 'verifiedAt'
Assert-Keys $document $(if($hasVerified){@('schemaVersion','observedAt','tasks','verifiedAt')}else{@('schemaVersion','observedAt','tasks')})
$now=[DateTimeOffset]::UtcNow
$observed=[DateTimeOffset]$document.observedAt
if($hasVerified -and ($document.schemaVersion -ne 2 -or [DateTimeOffset]$document.verifiedAt -lt $observed -or [DateTimeOffset]$document.verifiedAt -gt $now.AddMinutes(1))){throw 'Invalid verification time'}
if($document.schemaVersion -notin @(1,2) -or $null -eq $document.tasks -or $document.tasks -isnot [array] -or @($document.tasks).Count -gt 100 -or $observed -eq [DateTimeOffset]::MinValue -or $observed -gt $now.AddMinutes(1)){throw 'Invalid schedule document'}
$identities=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($task in $document.tasks){
    Assert-Keys $task @('id','nodeId','title','description','state','reason','dependsOn','assignedAt','updatedAt','evidence')
    if($task.id -isnot [string] -or $task.id -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or
       $task.nodeId -cnotin @('local','taichung','taoyuan') -or
       ($task.state -cnotin @('queued','acknowledged','running','blocked','unconfirmed') -and ($document.schemaVersion -ne 2 -or $task.state -cnotin @('completed','failed','cancelled'))) -or
       -not $identities.Add($task.nodeId+':'+$task.id)){throw 'Invalid schedule identity/state'}
    Assert-Text $task.title 80; Assert-Text $task.description 600; Assert-Text $task.reason 400; Assert-Text $task.evidence 240
    if($null -eq $task.dependsOn -or $task.dependsOn -isnot [array] -or @($task.dependsOn).Count -gt 10){throw 'Invalid dependencies'}
    $dependencies=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($dependency in $task.dependsOn){if($dependency -isnot [string] -or $dependency -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or $dependency -ceq $task.id -or -not $dependencies.Add($dependency)){throw 'Invalid dependency'}}
    $assigned=[DateTimeOffset]$task.assignedAt; $updated=[DateTimeOffset]$task.updatedAt
    if($assigned -eq [DateTimeOffset]::MinValue -or $assigned -gt $updated -or $updated -gt $observed.AddMinutes(1) -or $updated -gt $now.AddMinutes(1)){throw 'Invalid task times'}
}
$target=Join-Path $directory.FullName 'task-schedule.json'
if((Test-Path -LiteralPath $target) -and ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe target'}
$lockPath=Join-Path $directory.FullName '.task-schedule.lock'
if((Test-Path -LiteralPath $lockPath) -and ((Get-Item -LiteralPath $lockPath).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe lock'}
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$temporary=Join-Path $directory.FullName ('task-schedule.'+[guid]::NewGuid().ToString('N')+'.tmp')
try{
    if(Test-Path -LiteralPath $target){
        $existing=Get-Content -LiteralPath $target -Raw|ConvertFrom-Json
        if([DateTimeOffset]$existing.observedAt -gt $observed){throw 'Refusing older schedule overwrite'}
        foreach($prior in $existing.tasks){
            $next=@($document.tasks | Where-Object { $_.nodeId -ceq $prior.nodeId -and $_.id -ceq $prior.id })
            if($prior.state -cin @('completed','failed','cancelled') -and ($next.Count -ne 1 -or $next[0].state -cne $prior.state)){throw 'Refusing terminal resurrection or removal'}
            if($next.Count -eq 1 -and ([DateTimeOffset]$next[0].assignedAt -ne [DateTimeOffset]$prior.assignedAt -or [DateTimeOffset]$next[0].updatedAt -lt [DateTimeOffset]$prior.updatedAt)){throw 'Refusing task identity or time regression'}
        }
    }
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($document|ConvertTo-Json -Depth 12))
    if($bytes.Length -gt 262144){throw 'Schedule exceeds byte limit'}
    [IO.File]::WriteAllBytes($temporary,$bytes)
    [IO.File]::Move($temporary,$target,$true)
    Write-Output ('PUBLISHED_TASKS='+@($document.tasks).Count)
}finally{if([IO.File]::Exists($temporary)){[IO.File]::Delete($temporary)};$lock.Dispose()}
