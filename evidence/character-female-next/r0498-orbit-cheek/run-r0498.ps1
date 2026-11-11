param([string]$Script,[string]$LogStem='author',[int]$MaxSeconds=240,[int]$PrivateLimitMiB=4300,[int]$MinFreePhysicalMiB=4800,[int]$MinFreeCommitMiB=6200)
$ErrorActionPreference='Stop'
$r=$PSScriptRoot
$env:TEMP=$r;$env:TMP=$r;$env:PYTHONDONTWRITEBYTECODE='1';$env:OPENBLAS_NUM_THREADS='1'
$os=Get-CimInstance Win32_OperatingSystem
if($os.FreePhysicalMemory -lt $MinFreePhysicalMiB*1MB/1KB -or $os.FreeVirtualMemory -lt $MinFreeCommitMiB*1MB/1KB){throw 'Insufficient headroom for this bounded job'}
$proc=Start-Process -FilePath 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' -ArgumentList @('-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','17','--python',"$r\$Script") -WindowStyle Hidden -WorkingDirectory $r -RedirectStandardOutput "$r\$LogStem.log" -RedirectStandardError "$r\$LogStem.err" -PassThru
"R498_PID=$($proc.Id)"
$clock=[Diagnostics.Stopwatch]::StartNew();[long]$peak=0
while(-not $proc.HasExited){
 $proc.Refresh();if($proc.HasExited){break}
 $peak=[Math]::Max($peak,[long]$proc.PrivateMemorySize64)
 $os=Get-CimInstance Win32_OperatingSystem
 if($proc.PrivateMemorySize64 -gt $PrivateLimitMiB*1MB -or $os.FreeVirtualMemory -lt 1250MB/1KB -or $clock.Elapsed.TotalSeconds -gt $MaxSeconds){
  if(-not $proc.HasExited){$proc.Kill();$proc.WaitForExit()}
  throw "Bounded compact Blender stopped after $($clock.Elapsed.TotalSeconds) seconds, peak $peak bytes"
 }
 Start-Sleep -Milliseconds 750
}
$proc.WaitForExit()
"BLENDER_EXIT=$($proc.ExitCode) PEAK_PRIVATE_BYTES=$peak"
Get-Content -LiteralPath "$r\$LogStem.log","$r\$LogStem.err" -Tail 12
exit $proc.ExitCode
