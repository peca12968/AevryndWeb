#requires -Version 7.0
[CmdletBinding(SupportsShouldProcess)]
param([Parameter(Mandatory)][ValidateSet('taichung','taoyuan')][string]$NodeId, [switch]$Remove)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskName = "Aevrynd Operations Telemetry ($NodeId)"
$root = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'Aevrynd\OperationsTelemetry'
$publisher = Join-Path $root 'Publish-OperationsTelemetry.ps1'
if ($PSCmdlet.ShouldProcess($taskName, $(if ($Remove) { 'Stop and unregister telemetry publisher' } else { 'Stop telemetry publisher' }))) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -ne $task) { Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue; if ($Remove) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false } }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine.Contains($publisher,[StringComparison]::OrdinalIgnoreCase) -and $_.CommandLine.Contains("-NodeId $NodeId",[StringComparison]::Ordinal) })
    foreach ($process in $processes) { Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop }
    if ($Remove -and (Test-Path -LiteralPath $publisher -PathType Leaf)) { Remove-Item -LiteralPath $publisher -Force }
}
Write-Output "Telemetry publisher stopped for $NodeId."
