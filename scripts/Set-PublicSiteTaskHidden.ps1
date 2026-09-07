[CmdletBinding()]
param([string]$BackupDirectory='C:\AevryndAudit\silent-public-task-20260905')
$ErrorActionPreference='Stop'
# 僅修正既有網站排程的視窗旗標，保留動作、帳號、觸發條件與其他設定。
$task=Get-ScheduledTask -TaskName 'AevryndWeb Public Site' -TaskPath '\'
if(@($task.Actions).Count -ne 1 -or $task.Actions[0].Execute -ne 'C:\Program Files\PowerShell\7\pwsh.exe'){throw 'Unexpected task action'}
$arguments=[string]$task.Actions[0].Arguments
$encoded=[regex]::Match($arguments,'(?i)-EncodedCommand\s+(\S+)').Groups[1].Value
if(-not $encoded){throw 'Expected encoded bootstrap not found'}
$decoded=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($encoded))
if($decoded -cne '$ErrorActionPreference=''Stop''; & ''C:\ProgramData\AevryndWeb\scripts\Run-ScheduledPublicSite.ps1''; [Environment]::Exit(0)'){throw 'Unexpected bootstrap; no changes made'}
$root=[IO.Path]::GetFullPath($BackupDirectory)
$null=New-Item -ItemType Directory -Path $root -Force
if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Unsafe backup directory'}
$backup=Join-Path $root ('public-site-task-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fffffff')+'.xml')
$before=Export-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath
[IO.File]::WriteAllText($backup,$before,[Text.UTF8Encoding]::new($false))
if($arguments -match '(?i)-WindowStyle\s+\S+'){$arguments=[regex]::Replace($arguments,'(?i)-WindowStyle\s+\S+','-WindowStyle Hidden')}
else{$arguments='-WindowStyle Hidden '+$arguments}
$actionParameters=@{Execute=$task.Actions[0].Execute;Argument=$arguments}
if($task.Actions[0].WorkingDirectory){$actionParameters.WorkingDirectory=$task.Actions[0].WorkingDirectory}
$action=New-ScheduledTaskAction @actionParameters
$task.Settings.Hidden=$true
$null=Set-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Action $action -Settings $task.Settings
$after=Get-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath
if($after.Actions[0].Arguments -cne $arguments -or -not $after.Settings.Hidden){throw 'Task readback mismatch'}
Write-Output 'VERIFIED WindowStyle=Hidden TaskHidden=True; no process stopped or task started'
Write-Output ('BACKUP='+$backup)
