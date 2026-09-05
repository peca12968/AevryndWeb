[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CommentsPath,
    [Parameter(Mandatory)][string]$CatalogPath,
    [Parameter(Mandatory)][string]$CommandMapPath,
    [Parameter(Mandatory)][string]$OutputPath,
    [string]$FetchReceiptPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
# 一次性離線轉換；呼叫者提供已核對的 GitHub API 回應，本程式不抓網路、不派工、不發布正式資料。
function Assert-JsonKeys([System.Text.Json.JsonElement]$Value){
    if($Value.ValueKind -eq [System.Text.Json.JsonValueKind]::Object){
        $keys=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach($property in $Value.EnumerateObject()){
            if(-not $keys.Add($property.Name)){throw 'Duplicate JSON property'}
            Assert-JsonKeys $property.Value
        }
    }elseif($Value.ValueKind -eq [System.Text.Json.JsonValueKind]::Array){foreach($item in $Value.EnumerateArray()){Assert-JsonKeys $item}}
}
function Read-Document([string]$Path,[long]$Maximum){
    $file=Get-Item -LiteralPath $Path
    if($file.PSIsContainer -or $file.Length -gt $Maximum -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe input file'}
    $json=[IO.File]::ReadAllText($file.FullName)
    $parsed=[System.Text.Json.JsonDocument]::Parse($json)
    try{Assert-JsonKeys $parsed.RootElement}finally{$parsed.Dispose()}
    return ConvertFrom-Json -InputObject $json -AsHashtable -DateKind String
}
function Assert-Keys($Value,[string[]]$Required,[string[]]$Allowed=$Required){
    if($Value -isnot [Collections.IDictionary]){throw 'Expected JSON object'}
    foreach($key in $Required){if(@($Value.Keys) -cnotcontains $key){throw "Missing exact property: $key"}}
    foreach($key in $Value.Keys){if($Allowed -cnotcontains $key){throw "Unexpected property: $key"}}
}
function Assert-PublicText($Value,[int]$Maximum){
    if($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt $Maximum -or $Value -match '[\x00-\x1f\x7f]|://|@|[A-Za-z]:[\\/]|(?:\d{1,3}\.){3}\d{1,3}|-----BEGIN'){throw 'Invalid public text'}
}
function Read-Time($Value){
    if($Value -isnot [string] -or $Value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?(?:Z|[+-]\d{2}:\d{2})$'){throw 'Invalid timestamp'}
    $result=[DateTimeOffset]::Parse($Value,[Globalization.CultureInfo]::InvariantCulture)
    if($result -eq [DateTimeOffset]::MinValue -or $result -gt [DateTimeOffset]::UtcNow.AddMinutes(1)){throw 'Future or empty timestamp'}
    return $result
}
function Read-Field([string]$Body,[string]$Name,[bool]$Required=$true){
    $matches=[regex]::Matches($Body,'(?im)^'+[regex]::Escape($Name)+':[^\r\n]*')
    if($matches.Count -eq 0 -and -not $Required){return $null}
    if($matches.Count -ne 1 -or -not $matches[0].Value.StartsWith($Name+':',[StringComparison]::Ordinal)){throw "Invalid or duplicate field: $Name"}
    return $matches[0].Value.Substring($Name.Length+1).Trim()
}
function Flatten-Comments($Value,[int]$Depth=0){
    if($Depth -gt 4){throw 'Comment nesting exceeds limit'}
    if($Value -is [Collections.IDictionary]){return ,$Value}
    if($Value -isnot [array]){throw 'Expected comments array'}
    foreach($entry in $Value){Flatten-Comments $entry ($Depth+1)}
}
$catalog=Read-Document $CatalogPath 262144
Assert-Keys $catalog @('schemaVersion','observedAt','tasks') @('schemaVersion','observedAt','tasks','verifiedAt')
if($catalog.schemaVersion -notin @(1,2) -or $catalog.tasks -isnot [array] -or $catalog.tasks.Count -gt 100){throw 'Invalid catalog'}
$observed=Read-Time $catalog.observedAt
$verified=$null
if(@($catalog.Keys) -ccontains 'verifiedAt'){
    if($catalog.schemaVersion -ne 2){throw 'Verification timestamp requires schema 2'}
    $verified=Read-Time $catalog.verifiedAt
}
$taskKeys=@('id','nodeId','title','description','state','reason','dependsOn','assignedAt','updatedAt','evidence')
$tasks=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($task in $catalog.tasks){
    Assert-Keys $task $taskKeys
    if($task.id -isnot [string] -or $task.id -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or $task.nodeId -cnotin @('local','taichung','taoyuan') -or $task.state -cnotin @('queued','acknowledged','running','blocked','unconfirmed','completed','failed','cancelled')){throw 'Invalid catalog identity or state'}
    Assert-PublicText $task.title 80; Assert-PublicText $task.description 600; Assert-PublicText $task.reason 400; Assert-PublicText $task.evidence 240
    $assigned=Read-Time $task.assignedAt; $updated=Read-Time $task.updatedAt
    if($assigned -gt $updated -or $updated -gt $observed.AddMinutes(1)){throw 'Catalog time regression'}
    if($task.dependsOn -isnot [array] -or $task.dependsOn.Count -gt 10){throw 'Invalid dependencies'}
    $dependencies=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($dependency in $task.dependsOn){if($dependency -isnot [string] -or $dependency -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or $dependency -ceq $task.id -or -not $dependencies.Add($dependency)){throw 'Invalid dependency'}}
    if(-not $tasks.TryAdd($task.nodeId+':'+$task.id,$task)){throw 'Duplicate catalog command'}
}
$map=Read-Document $CommandMapPath 262144
Assert-Keys $map @('schemaVersion','ownerLogin','ownerId','issueUrl','commands')
if($map.schemaVersion -ne 1 -or $map.ownerLogin -isnot [string] -or $map.ownerId -isnot [long] -and $map.ownerId -isnot [int] -or $map.ownerId -le 0 -or $map.issueUrl -cnotmatch '^https://api\.github\.com/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*$' -or $map.commands -isnot [array] -or $map.commands.Count -gt 100){throw 'Invalid trust map'}
$commands=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$commandComments=[Collections.Generic.HashSet[long]]::new()
foreach($command in $map.commands){
    Assert-Keys $command @('commandId','nodeId','commandCommentId','title','description','dependsOn')
    if($command.commandId -isnot [string] -or $command.commandId -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or $command.nodeId -cnotin @('taichung','taoyuan') -or ($command.commandCommentId -isnot [long] -and $command.commandCommentId -isnot [int]) -or $command.commandCommentId -le 0 -or -not $commandComments.Add($command.commandCommentId) -or -not $commands.TryAdd($command.commandId,$command)){throw 'Invalid or duplicate command allowlist'}
    Assert-PublicText $command.title 80; Assert-PublicText $command.description 600
    if($command.dependsOn -isnot [array] -or $command.dependsOn.Count -gt 10){throw 'Invalid command dependencies'}
    $dependencies=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($dependency in $command.dependsOn){if($dependency -isnot [string] -or $dependency -cnotmatch '^[A-Z0-9][A-Z0-9_-]{0,159}$' -or $dependency -ceq $command.commandId -or -not $dependencies.Add($dependency)){throw 'Invalid command dependency'}}
}
$comments=@(Flatten-Comments (Read-Document $CommentsPath 33554432))
$seen=[Collections.Generic.Dictionary[long,string]]::new()
$events=[Collections.Generic.List[object]]::new()
$origins=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($comment in $comments){
    if($comment -isnot [Collections.IDictionary] -or @($comment.Keys) -cnotcontains 'body' -or $comment.body -isnot [string]){throw 'Invalid comment'}
    $blocks=[regex]::Matches($comment.body,'(?ms)^\[(MAIN_COMMAND|NODE_ACK|NODE_REPORT)\]\r?\n(.*?)^\[/\1\]\s*')
    if($blocks.Count -eq 0){continue}
    $candidate=Read-Field $blocks[0].Groups[2].Value 'COMMAND_ID' $false
    if(-not $candidate -or -not $commands.ContainsKey($candidate)){continue}
    if($blocks.Count -ne 1){throw 'Ambiguous event blocks'}
    foreach($key in @('id','created_at','issue_url','author_association','user')){if(@($comment.Keys) -cnotcontains $key){throw 'Missing comment provenance'}}
    if(($comment.id -isnot [long] -and $comment.id -isnot [int]) -or $comment.id -le 0 -or $comment.author_association -cne 'OWNER' -or $comment.issue_url -cne $map.issueUrl -or $comment.user -isnot [Collections.IDictionary] -or @($comment.user.Keys) -cnotcontains 'login' -or @($comment.user.Keys) -cnotcontains 'id' -or $comment.user.login -cne $map.ownerLogin -or $comment.user.id -ne $map.ownerId){throw 'Untrusted event author or issue'}
    $created=Read-Time $comment.created_at
    $fingerprint=$comment | ConvertTo-Json -Depth 30 -Compress
    if($seen.ContainsKey($comment.id)){if($seen[$comment.id] -cne $fingerprint){throw 'Conflicting comment ID'};continue}
    $seen.Add($comment.id,$fingerprint)
    $kind=$blocks[0].Groups[1].Value; $body=$blocks[0].Groups[2].Value; $command=$commands[$candidate]
    $node=Read-Field $body $(if($kind -ceq 'MAIN_COMMAND'){'TARGET'}else{'NODE'})
    if($node -cne $command.nodeId.ToUpperInvariant()){throw 'Event node mismatch'}
    if($kind -ceq 'MAIN_COMMAND'){
        if($comment.id -ne $command.commandCommentId){throw 'Command comment does not match allowlist'}
        $origins.Add($candidate,@{created=$created;commentId=$comment.id})
        continue
    }
    $status=Read-Field $body 'STATUS' ($kind -cne 'NODE_ACK')
    $reference=Read-Field $body 'COMMENT_ID' $false
    if($null -ne $reference -and $reference -cne [string]$command.commandCommentId){throw 'Event command reference mismatch'}
    $state=if($kind -ceq 'NODE_ACK'){
        if($null -ne $status -and $status -cne 'ACK'){throw 'Invalid acknowledgement state'}
        if($null -eq $reference){throw 'Acknowledgement requires command comment reference'}
        'acknowledged'
    }else{
        switch -CaseSensitive ($status){ 'COMPLETED' {'completed'} 'COMPLETE' {'completed'} 'FAILED' {'failed'} 'CANCELLED' {'cancelled'} 'BLOCKED' {'blocked'} 'NEEDS_MAIN_VALIDATION' {'blocked'} 'NEEDS_MAIN_DECISION' {'unconfirmed'} default {throw 'Unverified report state'} }
    }
    $events.Add(@{commandId=$candidate;nodeId=$command.nodeId;state=$state;created=$created;commentId=$comment.id;needsMainValidation=($status -ceq 'NEEDS_MAIN_VALIDATION');needsMainDecision=($status -ceq 'NEEDS_MAIN_DECISION')})
}
foreach($command in $commands.Values){
    if(-not $origins.ContainsKey($command.commandId)){throw 'Missing verified MAIN_COMMAND'}
    $key=$command.nodeId+':'+$command.commandId
    if(-not $tasks.ContainsKey($key)){
        $at=$origins[$command.commandId].created.ToUniversalTime().ToString('O')
        $tasks.Add($key,[ordered]@{id=$command.commandId;nodeId=$command.nodeId;title=$command.title;description=$command.description;state='queued';reason='已驗證派工來源；尚無接單事件。';dependsOn=@($command.dependsOn);assignedAt=$at;updatedAt=$at;evidence='OWNER MAIN_COMMAND comment '+$command.commandCommentId})
    }
    if($origins[$command.commandId].created -gt $observed){$observed=$origins[$command.commandId].created}
}
foreach($event in ($events | Sort-Object created,commentId)){
    $origin=$origins[$event.commandId]
    if($event.created -lt $origin.created){throw 'Event predates command'}
    $task=$tasks[$event.nodeId+':'+$event.commandId]
    $updated=Read-Time $task.updatedAt
    if($event.created -lt (Read-Time $task.assignedAt)){throw 'Event predates catalog assignment'}
    if($task.state -cin @('completed','failed','cancelled')){
        if($event.state -cin @('completed','failed','cancelled') -and $event.state -cne $task.state){throw 'Conflicting terminal states'}
        continue
    }
    if($event.created -lt $updated){continue}
    if($event.created -eq $updated -and $event.state -cne $task.state){throw 'Conflicting same-time state'}
    $task.state=$event.state
    $task.updatedAt=$event.created.ToUniversalTime().ToString('O')
    $task.reason=switch ($event.state){'acknowledged' {'已驗證接單事件；接單不代表程序正在執行。'} 'completed' {'節點已提供明確完成報告；不代表其他驗收項目已通過。'} 'failed' {'節點已提供明確失敗報告；需主代理處理。'} 'cancelled' {'節點已提供明確取消報告。'} 'blocked' {'節點已提供明確受阻報告。'} 'unconfirmed' {'來源已回報；等待主機決策，不能推定完成或執行中。'}}
    if($event.needsMainValidation){$task.reason='副機已回報修正證據，等待主機獨立驗證正式網站；尚未確認完成。'}
    if($event.needsMainDecision){$task.reason='副機已回報 NEEDS_MAIN_DECISION；等待主機決策，不能推定完成或執行中。'}
    $task.evidence='OWNER '+$map.ownerLogin+'；MAIN_COMMAND '+$origin.commentId+'；事件 comment '+$event.commentId
    if($event.created -gt $observed){$observed=$event.created}
}
if($tasks.Count -gt 100){throw 'Schedule task limit exceeded'}
$output=[IO.Path]::GetFullPath($OutputPath)
if($output.StartsWith('C:\ProgramData\',[StringComparison]::OrdinalIgnoreCase)){throw 'Review output must not target ProgramData'}
if([IO.File]::Exists($output)){throw 'Review output already exists; choose a fresh path'}
$directory=Get-Item -LiteralPath ([IO.Path]::GetDirectoryName($output))
if(-not $directory.PSIsContainer -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe output directory'}
$result=[ordered]@{schemaVersion=2;observedAt=$observed.ToUniversalTime().ToString('O');tasks=@($tasks.Values | Sort-Object nodeId,assignedAt,id)}
if($FetchReceiptPath){
    $receipt=Read-Document $FetchReceiptPath 4096
    Assert-Keys $receipt @('schemaVersion','sourceUri','transport','complete','fetchedAtUtc','commentsSha256')
    if($receipt.schemaVersion -ne 1 -or $receipt.sourceUri -cne ($map.issueUrl+'/comments') -or $receipt.transport -cne 'gh-api-paginated' -or $receipt.complete -isnot [bool] -or -not $receipt.complete -or $receipt.commentsSha256 -cne (Get-FileHash -LiteralPath $CommentsPath -Algorithm SHA256).Hash){throw 'Unverified fetch receipt'}
    $fetched=Read-Time $receipt.fetchedAtUtc
    if($fetched -lt $observed -or ($null -ne $verified -and $fetched -lt $verified)){throw 'Fetch receipt time regression'}
    $verified=$fetched
}
if($null -ne $verified){$result.verifiedAt=$verified.ToUniversalTime().ToString('O')}
$json=$result | ConvertTo-Json -Depth 12
$bytes=[Text.UTF8Encoding]::new($false).GetBytes($json)
if($bytes.Length -gt 262144){throw 'Schedule byte limit exceeded'}
$stream=[IO.File]::Open($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
Write-Output ('REVIEW_TASKS='+$tasks.Count+'; ACCEPTED_EVENTS='+$events.Count+'; OBSERVED_AT='+$result.observedAt)
