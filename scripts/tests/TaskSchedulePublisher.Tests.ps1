$ErrorActionPreference='Stop'
$publisher=Join-Path (Split-Path -Parent $PSScriptRoot) 'Publish-TaskSchedule.ps1'
$root=Join-Path ([IO.Path]::GetTempPath()) ('aevrynd-schedule-tests-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $root
$inputPath=Join-Path $root 'input.json'
$now=[DateTimeOffset]::UtcNow
$task=[ordered]@{id='TEST-01';nodeId='local';title='測試工作';description='驗證排程發布';state='queued';reason='等待執行';dependsOn=@();assignedAt=$now.AddMinutes(-1).ToString('o');updatedAt=$now.AddMinutes(-1).ToString('o');evidence='隔離測試資料'}
$document=[ordered]@{schemaVersion=1;observedAt=$now.ToString('o');tasks=@($task)}
function Save-Input{[IO.File]::WriteAllText($inputPath,($document|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))}
Save-Input
& $publisher -InputPath $inputPath -StateDirectory $root
$target=Join-Path $root 'task-schedule.json'
$hash=(Get-FileHash -LiteralPath $target).Hash
$rejected=0
$task.state='completed';Save-Input
try{& $publisher -InputPath $inputPath -StateDirectory $root}catch{$rejected++}
$task.state='queued';$task.description='https://private.example';Save-Input
try{& $publisher -InputPath $inputPath -StateDirectory $root}catch{$rejected++}
$task.description='驗證排程發布';$document.observedAt=$now.AddSeconds(-1).ToString('o');Save-Input
try{& $publisher -InputPath $inputPath -StateDirectory $root}catch{$rejected++}
if($rejected -ne 3 -or (Get-FileHash -LiteralPath $target).Hash -ne $hash){throw 'Rejected input changed the last good schedule'}
Write-Output 'PASS publish and three fail-closed unchanged-state cases'
