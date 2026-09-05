[CmdletBinding(SupportsShouldProcess)]
param([Parameter(Mandatory)][string]$AssemblyPath,[Parameter(Mandatory)][string]$StateDirectory,
    [Parameter(Mandatory)][string]$PowerShellPath,[string]$GhPath='C:\Program Files\GitHub CLI\gh.exe')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
# 僅由主代理驗收後明確呼叫；腳本本身不更動 ACL、秘密或既有網站工作。
$name='Aevrynd Operations Dispatch Sync'
$runner=Join-Path $PSScriptRoot 'Watch-OperationsDispatch.ps1'
foreach($path in @($AssemblyPath,$PowerShellPath,$GhPath,$runner,$StateDirectory)){
    $item=Get-Item -LiteralPath ([IO.Path]::GetFullPath($path))
    if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Unsafe installer path'}
    if($path.Contains('"')){throw 'Invalid quote in installer path'}
}
$arguments='-NoProfile -NonInteractive -WindowStyle Hidden -File "'+$runner+'" -AssemblyPath "'+([IO.Path]::GetFullPath($AssemblyPath))+'" -StateDirectory "'+([IO.Path]::GetFullPath($StateDirectory))+'" -GhPath "'+([IO.Path]::GetFullPath($GhPath))+'"'
if($PSCmdlet.ShouldProcess($name,'Register one hidden current-user AtLogOn dispatch projection task')){
    if(Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue){throw 'Task already exists; review before updating'}
    $user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    $action=New-ScheduledTaskAction -Execute ([IO.Path]::GetFullPath($PowerShellPath)) -Argument $arguments
    $trigger=New-ScheduledTaskTrigger -AtLogOn -User $user
    $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    $settings=New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
}
