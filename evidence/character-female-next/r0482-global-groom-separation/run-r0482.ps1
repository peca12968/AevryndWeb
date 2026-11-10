param([string]$Script='layout-r0482.py',[string]$LogStem='probe',[int]$MaxSeconds=350,[int]$Threads=4,[int]$PrivateLimitMiB=8704,[switch]$Lite)
$ErrorActionPreference='Stop'
$r=$PSScriptRoot
$env:TEMP=$r
$env:TMP=$r
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OPENBLAS_NUM_THREADS='1'
$os=Get-CimInstance Win32_OperatingSystem
if($os.FreePhysicalMemory -lt $(if($Lite){1800MB/1KB}else{5000MB/1KB}) -or $os.FreeVirtualMemory -lt $(if($Lite){2300MB/1KB}else{8300MB/1KB})){throw 'Insufficient memory headroom'}
if($PrivateLimitMiB -gt 8704 -and ($os.FreePhysicalMemory -lt 7000MB/1KB -or $os.FreeVirtualMemory -lt 13500MB/1KB)){throw 'Insufficient headroom for the larger worker'}
$proc=Start-Process -FilePath 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' -ArgumentList @('-b','--factory-startup','--disable-autoexec','-t',"$Threads",'--python-exit-code','17','--python',"$r\$Script") -WindowStyle Hidden -WorkingDirectory $r -RedirectStandardOutput "$r\$LogStem.log" -RedirectStandardError "$r\$LogStem.err" -PassThru
"R482_PID=$($proc.Id)"
$clock=[Diagnostics.Stopwatch]::StartNew()
[long]$peak=0
while(-not $proc.HasExited){
    $proc.Refresh()
    if($proc.HasExited){break}
    $peak=[Math]::Max($peak,[long]$proc.PrivateMemorySize64)
    $os=Get-CimInstance Win32_OperatingSystem
    if($proc.PrivateMemorySize64 -gt $(if($Lite){1400MB}else{$PrivateLimitMiB*1MB}) -or $os.FreeVirtualMemory -lt 1250MB/1KB -or $clock.Elapsed.TotalSeconds -gt $MaxSeconds){
        if(-not $proc.HasExited){$proc.Kill();$proc.WaitForExit()}
        throw "Bounded Blender stopped after $($clock.Elapsed.TotalSeconds) seconds, peak private bytes $peak, virtual memory free $($os.FreeVirtualMemory) KiB"
    }
    Start-Sleep -Milliseconds 750
}
$proc.WaitForExit()
"BLENDER_EXIT=$($proc.ExitCode) PEAK_PRIVATE_BYTES=$peak"
Get-Content -LiteralPath "$r\$LogStem.log","$r\$LogStem.err" -Tail 15
exit $proc.ExitCode













