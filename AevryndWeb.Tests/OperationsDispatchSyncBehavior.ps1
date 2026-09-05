[CmdletBinding()]
param([Parameter(Mandatory)][string]$ScriptPath,[Parameter(Mandatory)][string]$ResultDirectory)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$null=New-Item -ItemType Directory -Path $ResultDirectory -Force
$results=[Collections.Generic.List[object]]::new()
$map=@{schemaVersion=1;ownerLogin='owner';ownerId=1234;issueUrl='https://api.github.com/repos/owner/repo/issues/1';commands=@(@{commandId='TEST-01';nodeId='taichung';commandCommentId=101;title='驗證派遣同步';description='保留實際來源事件時間。';dependsOn=@()})}
function Comment([long]$Id,[string]$Kind,[string]$Fields,[string]$Time){
    return @{id=$Id;created_at=$Time;issue_url=$map.issueUrl;author_association='OWNER';user=@{login='owner';id=1234};body="[$Kind]`nCOMMAND_ID: TEST-01`n$Fields`n[/$Kind]"}
}
$command=Comment 101 'MAIN_COMMAND' 'TARGET: TAICHUNG' '2026-09-05T03:00:00Z'
$ack=Comment 102 'NODE_ACK' "NODE: TAICHUNG`nSTATUS: ACK`nCOMMENT_ID: 101" '2026-09-05T03:10:00Z'
$terminal=Comment 103 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: COMPLETED" '2026-09-05T03:20:00Z'
function Run-Case([string]$Name,[scriptblock]$Body){
    try{& $Body;$results.Add(@{name=$Name;status='passed'});Write-Output "PASS $Name"}catch{$results.Add(@{name=$Name;status='failed';error=$_.Exception.Message});Write-Output "FAIL $Name : $($_.Exception.Message)"}
}
function Assert-Equal($Actual,$Expected){if($Actual -cne $Expected){throw "Expected [$Expected], actual [$Actual]"}}
function Invoke-Fixture($Comments,[scriptblock]$Mutation={},$Catalog=$null,[bool]$Reject=$false){
    $directory=Join-Path $ResultDirectory ([guid]::NewGuid().ToString('N'));$null=New-Item -ItemType Directory -Path $directory
    $testMap=$map | ConvertTo-Json -Depth 10 | ConvertFrom-Json -AsHashtable
    $testComments=@($Comments | ConvertTo-Json -Depth 10 | ConvertFrom-Json -AsHashtable -DateKind String)
    if($null -eq $Catalog){$Catalog=@{schemaVersion=1;observedAt='2026-09-05T02:00:00Z';tasks=@()}}
    & $Mutation $testComments $testMap
    $commentsPath=Join-Path $directory 'comments.json';$catalogPath=Join-Path $directory 'catalog.json';$mapPath=Join-Path $directory 'map.json';$outputPath=Join-Path $directory 'schedule.json'
    [IO.File]::WriteAllText($commentsPath,(ConvertTo-Json -InputObject $testComments -Depth 20))
    [IO.File]::WriteAllText($catalogPath,($Catalog | ConvertTo-Json -Depth 20))
    [IO.File]::WriteAllText($mapPath,($testMap | ConvertTo-Json -Depth 20))
    $rejected=$false
    try{& $ScriptPath -CommentsPath $commentsPath -CatalogPath $catalogPath -CommandMapPath $mapPath -OutputPath $outputPath | Out-Null}catch{if(-not $Reject){throw};$rejected=$true}
    if($Reject){if(-not $rejected -or (Test-Path -LiteralPath $outputPath)){throw 'Expected fail-closed without output'};return}
    return Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json -AsHashtable -DateKind String
}
Run-Case 'ACK preserves actual event time without claiming process execution' {
    $result=Invoke-Fixture @($command,$ack)
    Assert-Equal $result.tasks[0].state 'acknowledged'
    Assert-Equal $result.tasks[0].assignedAt '2026-09-05T03:00:00.0000000+00:00'
    Assert-Equal $result.tasks[0].updatedAt '2026-09-05T03:10:00.0000000+00:00'
    Assert-Equal $result.observedAt $result.tasks[0].updatedAt
}
Run-Case 'terminal wins and late ACK does not resurrect or freshen source' {
    $late=Comment 104 'NODE_ACK' "NODE: TAICHUNG`nSTATUS: ACK`nCOMMENT_ID: 101" '2026-09-05T03:30:00Z'
    $result=Invoke-Fixture @($late,$terminal,$ack,$command)
    Assert-Equal $result.tasks[0].state 'completed';Assert-Equal $result.observedAt '2026-09-05T03:20:00.0000000+00:00'
    $replayed=Invoke-Fixture @($command,$ack,$terminal,$late) -Catalog $result
    Assert-Equal $replayed.tasks[0].state 'completed';Assert-Equal $replayed.observedAt $result.observedAt
}
Run-Case 'identical comments deduplicate' {$result=Invoke-Fixture @($command,$ack,$ack);Assert-Equal $result.tasks.Count 1}
Run-Case 'actual NODE_ACK without STATUS remains acknowledged' {
    $minimal=Comment 104 'NODE_ACK' "NODE: TAICHUNG`nCOMMENT_ID: 101`nACK_UTC: 2026-09-05T03:25:00Z" '2026-09-05T03:25:01Z'
    $result=Invoke-Fixture @($command,$minimal);Assert-Equal $result.tasks[0].state 'acknowledged'
}
Run-Case 'wrong author fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].user.login='intruder'} -Reject $true}
Run-Case 'wrong owner ID fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].user.id=9999} -Reject $true}
Run-Case 'non OWNER fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].author_association='MEMBER'} -Reject $true}
Run-Case 'wrong issue fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].issue_url='https://api.github.com/repos/owner/repo/issues/2'} -Reject $true}
Run-Case 'wrong node fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].body=$c[1].body.Replace('TAICHUNG','TAOYUAN')} -Reject $true}
Run-Case 'missing MAIN_COMMAND fails closed' {Invoke-Fixture @($ack) -Reject $true}
Run-Case 'incorrect command reference fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].body=$c[1].body.Replace('COMMENT_ID: 101','COMMENT_ID: 999')} -Reject $true}
Run-Case 'duplicate semantic field fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].body=$c[1].body.Replace('STATUS: ACK',"STATUS: ACK`nSTATUS: COMPLETED")} -Reject $true}
Run-Case 'case-variant semantic field fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].body=$c[1].body.Replace('STATUS:','status:')} -Reject $true}
Run-Case 'conflicting comment ID fails closed' {$bad=Comment 102 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: FAILED" '2026-09-05T03:20:00Z';Invoke-Fixture @($command,$ack,$bad) -Reject $true}
Run-Case 'conflicting terminal fails closed' {$bad=Comment 104 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: FAILED" '2026-09-05T03:25:00Z';Invoke-Fixture @($command,$terminal,$bad) -Reject $true}
Run-Case 'event before command fails closed' {Invoke-Fixture @($command,$ack) {param($c,$m) $c[1].created_at='2026-09-05T02:59:00Z'} -Reject $true}
Run-Case 'unverified running report fails closed' {$running=Comment 104 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: RUNNING" '2026-09-05T03:25:00Z';Invoke-Fixture @($command,$running) -Reject $true}
Run-Case 'legacy tasks survive unchanged' {
    $legacy=@{schemaVersion=1;observedAt='2026-09-05T03:00:00Z';tasks=@(@{id='LEGACY-01';nodeId='taoyuan';title='既有工作';description='保留既有指派。';state='unconfirmed';reason='沒有可信終態。';dependsOn=@();assignedAt='2026-09-04T00:00:00Z';updatedAt='2026-09-04T00:00:00Z';evidence='先前核對來源。'})}
    $result=Invoke-Fixture @($command,$ack) -Catalog $legacy
    $retained=@($result.tasks | Where-Object {$_.id -ceq 'LEGACY-01'})[0]
    Assert-Equal $retained.updatedAt '2026-09-04T00:00:00Z';Assert-Equal $retained.state 'unconfirmed'
}
Run-Case 'NEEDS_MAIN_VALIDATION remains blocked instead of completed' {
    $pending=Comment 104 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: NEEDS_MAIN_VALIDATION" '2026-09-05T03:25:00Z'
    $result=Invoke-Fixture @($command,$ack,$pending)
    Assert-Equal $result.tasks[0].state 'blocked'
    if($result.tasks[0].reason -notmatch '等待主機獨立驗證'){throw 'Missing main validation reason'}
}
Run-Case 'NEEDS_MAIN_DECISION preserves evidence without claiming no acknowledgement' {
    $pending=Comment 104 'NODE_REPORT' "NODE: TAICHUNG`nSTATUS: NEEDS_MAIN_DECISION" '2026-09-05T03:25:00Z'
    $result=Invoke-Fixture @($command,$ack,$pending)
    Assert-Equal $result.tasks[0].state 'unconfirmed'
    if($result.tasks[0].reason -notmatch 'NEEDS_MAIN_DECISION' -or $result.tasks[0].evidence -notmatch '104'){throw 'Missing decision source evidence'}
}
$failures=@($results | Where-Object {$_.status -eq 'failed'}).Count
[IO.File]::WriteAllText((Join-Path $ResultDirectory 'results.json'),(@{total=$results.Count;passed=$results.Count-$failures;failed=$failures;results=@($results)} | ConvertTo-Json -Depth 6))
if($failures){exit 1}
