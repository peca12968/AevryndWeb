[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$AssemblyPath,
    [Parameter(Mandatory)][string]$StateDirectory,
    [string]$GhPath='C:\Program Files\GitHub CLI\gh.exe',
    [string]$CommentsPath,
    [switch]$Once,
    [ValidateRange(20,30)][int]$PollSeconds=30,
    [ValidateRange(5,25)][int]$TimeoutSeconds=25
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
# 僅在主機目前使用者登入脈絡中使用既有 gh 認證；不匯出 token，不啟動模型，也不由 IIS 執行。
function Assert-SafePath([string]$Path,[bool]$Directory){
    $item=Get-Item -LiteralPath ([IO.Path]::GetFullPath($Path))
    if($item.PSIsContainer -ne $Directory){throw 'PATH_TYPE_INVALID'}
    $cursor=$item
    while($null -ne $cursor){if($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'REPARSE_PATH_REJECTED'};$cursor=if($cursor -is [IO.DirectoryInfo]){$cursor.Parent}else{$cursor.Directory}}
    return $item.FullName
}
function Write-Atomic([string]$Path,[string]$Text){
    if(Test-Path -LiteralPath $Path){$null=Assert-SafePath $Path $false}
    $temporary=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    try{[IO.File]::WriteAllText($temporary,$Text,[Text.UTF8Encoding]::new($false));[IO.File]::Move($temporary,$Path,$true)}finally{if([IO.File]::Exists($temporary)){[IO.File]::Delete($temporary)}}
}
function Get-Digest([string]$Text){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($Text)))}
$assembly=Assert-SafePath $AssemblyPath $false
$root=Assert-SafePath $StateDirectory $true
if($CommentsPath -and -not $Once){throw 'OFFLINE_INPUT_REQUIRES_ONCE'}
if(-not $CommentsPath){$GhPath=Assert-SafePath $GhPath $false}
$null=[Reflection.Assembly]::LoadFrom($assembly)
$statePath=Join-Path $root 'dispatch-state.json';$healthPath=Join-Path $root 'dispatch-health.json';$lockPath=Join-Path $root '.dispatch-sync.lock'
if(Test-Path -LiteralPath $lockPath){$null=Assert-SafePath $lockPath $false}
try{$lease=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}catch{throw 'DISPATCH_SYNC_ALREADY_RUNNING'}
$failures=0;$lastSuccess=$null
try{
    if(Test-Path -LiteralPath $healthPath){
        $null=Assert-SafePath $healthPath $false
        if((Get-Item -LiteralPath $healthPath).Length -le 8192){$priorHealth=Get-Content -LiteralPath $healthPath -Raw | ConvertFrom-Json -AsHashtable -DateKind String;$lastSuccess=$priorHealth['lastSuccessAt']}
    }
    do{
        $process=$null;$cancellation=$null;$success=$false
        try{
            $previous=$null
            if(Test-Path -LiteralPath $statePath){$null=Assert-SafePath $statePath $false;if((Get-Item -LiteralPath $statePath).Length -gt 2097152){throw 'STATE_SIZE_LIMIT'};$previous=[IO.File]::ReadAllText($statePath)}
            if($CommentsPath){
                $inputFile=Assert-SafePath $CommentsPath $false
                if((Get-Item -LiteralPath $inputFile).Length -gt 33554432){throw 'COMMENT_SIZE_LIMIT'}
                $raw=[IO.File]::ReadAllText($inputFile)
            }else{
                $start=[Diagnostics.ProcessStartInfo]::new($GhPath)
                $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
                $start.StandardOutputEncoding=[Text.UTF8Encoding]::new($false);$start.StandardErrorEncoding=[Text.UTF8Encoding]::new($false)
                foreach($argument in @('api','--paginate','--slurp','repos/peca12968/Aevrynd/issues/1/comments?per_page=100')){$start.ArgumentList.Add($argument)}
                $process=[Diagnostics.Process]::Start($start)
                $cancellation=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds($TimeoutSeconds))
                $stdout=[AevryndWeb.Security.OperationsDispatchProjection]::ReadBoundedAsync($process.StandardOutput,33554432,$cancellation.Token)
                $stderr=[AevryndWeb.Security.OperationsDispatchProjection]::ReadBoundedAsync($process.StandardError,32768,$cancellation.Token)
                $exitTask=$process.WaitForExitAsync($cancellation.Token)
                [Threading.Tasks.Task]::WhenAll([Threading.Tasks.Task[]]@($stdout,$stderr,$exitTask)).GetAwaiter().GetResult()
                if($process.ExitCode -ne 0){throw 'GITHUB_FETCH_FAILED'}
                $raw=$stdout.GetAwaiter().GetResult()
            }
            $attempt=[DateTimeOffset]::UtcNow
            $projected=[AevryndWeb.Security.OperationsDispatchProjection]::BuildJson($raw,$previous,$attempt)
            $parsed=$projected | ConvertFrom-Json -AsHashtable -DateKind String
            $changed=$projected -cne $previous
            if($changed){Write-Atomic $statePath $projected}
            # 工作資料無變化不重寫；抓取健康另存，不能以連線時間覆蓋任務事件時間。
            if(-not $CommentsPath){$lastSuccess=$attempt.ToString('O')}
            $health=[ordered]@{schemaVersion=1;status=$(if($CommentsPath){'offline'}elseif($parsed.rejectedEvents -gt 0){'partial'}else{'current'});lastAttemptAt=$attempt.ToString('O');lastSuccessAt=$lastSuccess;stateSha256=(Get-Digest $projected);sourceSha256=(Get-Digest $raw);rejectedEvents=$parsed.rejectedEvents;diagnostic=$(if($CommentsPath){'OFFLINE_FIXTURE'}elseif($parsed.rejectedEvents -gt 0){'DISPATCH_EVENTS_REJECTED'}else{'DISPATCH_SOURCE_CURRENT'})}
            Write-Atomic $healthPath ($health | ConvertTo-Json -Compress)
            Write-Output ('DISPATCH_SYNC_OK; TASKS='+$parsed.tasks.Count+'; CHANGED='+$changed+'; SOURCE='+$health.status)
            $success=$true;$failures=0
        }catch{
            $failures++
            $code=if($cancellation -and $cancellation.IsCancellationRequested){'GITHUB_FETCH_TIMEOUT'}elseif($_.Exception.Message -match 'DISPATCH_|COMMENT_|STATE_'){'DISPATCH_SOURCE_INVALID'}else{'GITHUB_FETCH_FAILED'}
            $currentHash=if(Test-Path -LiteralPath $statePath){(Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash}else{''}
            $health=[ordered]@{schemaVersion=1;status='unavailable';lastAttemptAt=[DateTimeOffset]::UtcNow.ToString('O');lastSuccessAt=$lastSuccess;stateSha256=$currentHash;sourceSha256='';rejectedEvents=0;diagnostic=$code}
            Write-Atomic $healthPath ($health | ConvertTo-Json -Compress)
            Write-Warning $code
        }finally{
            if($process){if(-not $process.HasExited){$process.Kill($true);$null=$process.WaitForExit(5000)};$process.Dispose()}
            if($cancellation){$cancellation.Dispose()}
        }
        if($Once){if(-not $success){exit 1};break}
        $delay=if($success){$PollSeconds}else{[Math]::Min(300,$PollSeconds*[Math]::Pow(2,[Math]::Min($failures,4)))}
        Start-Sleep -Seconds $delay
    }while($true)
}finally{$lease.Dispose()}
