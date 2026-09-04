[CmdletBinding(SupportsShouldProcess)]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$projectRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $projectRoot 'AevryndWeb.csproj'
$temporaryRoot = Join-Path $env:TEMP ("AevryndWeb-publish-" + [Guid]::NewGuid().ToString('N'))
$temporaryPublish = Join-Path $temporaryRoot 'publish'
$temporaryScripts = Join-Path $temporaryRoot 'scripts'
$backupPublish = "$script:PublicSitePublish.rollback-$([Guid]::NewGuid().ToString('N'))"
$managedScripts = Join-Path $script:PublicSiteRoot 'scripts'
$backupScripts = "$managedScripts.rollback-$([Guid]::NewGuid().ToString('N'))"
$iisBackup = "AevryndWeb-$([Guid]::NewGuid().ToString('N'))"
$taskName = 'AevryndWeb Public Site'
$fixedPwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'
$codexRelaySecretPath = Join-Path $script:PublicSiteRoot 'codex-relay-secrets.json'

if ($WhatIfPreference) {
    $null = Get-Item -LiteralPath $project -ErrorAction Stop
    foreach ($name in @('PublicSite.Common.ps1','Start-PublicSite.ps1','Stop-PublicSite.ps1','Run-ScheduledPublicSite.ps1')) { $null = Get-Item -LiteralPath (Join-Path $PSScriptRoot $name) -ErrorAction Stop }
    Write-Output 'WHATIF: validate Release publish; back up IIS configuration, publish, scripts and scheduled task; stop only exact legacy/managed processes; enforce the IIS loopback contract; verify locally and externally; commit scripts/task; otherwise restore every prior artifact.'
    return
}
if (-not $PSCmdlet.ShouldProcess($script:PublicSiteRoot, 'Atomically deploy and verify the IIS-hosted public site')) { return }

Assert-PublicSiteAdministrator
Add-PublicSiteCredentialInterop
$paths = Get-PublicSitePaths
$pwsh = if (Test-Path -LiteralPath $fixedPwsh -PathType Leaf) { $fixedPwsh } else { (Get-Command pwsh.exe -ErrorAction Stop).Source }
$hadPublish = Test-Path -LiteralPath $script:PublicSitePublish -PathType Container
$hadScripts = Test-Path -LiteralPath $managedScripts -PathType Container
$previousTaskXml = Export-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$iisBackupCreated = $false; $rollbackRequired = $false; $publishSwapped = $false; $scriptsSwapped = $false; $deploymentSucceeded = $false; $rollbackSucceeded = $false; $committed = $false

function Invoke-AppCmdChecked([string[]]$Arguments) {
    $output = @(& $paths.AppCmd @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        # AppCmd 診斷不含憑證；仍限制長度，避免把大量 IIS 輸出寫入部署紀錄。
        $detail = (($output | ForEach-Object { $_.ToString().Trim() }) -join ' ').Trim()
        if ($detail.Length -gt 512) { $detail = $detail.Substring(0,512) }
        $suffix = if ($detail) { " Detail: $detail" } else { '' }
        throw "IIS operation failed (exit $exitCode): $([string]::Join(' ', $Arguments)).$suffix"
    }
}

function Test-PublishPayload([string]$Path) {
    foreach ($relative in @('AevryndWeb.dll','web.config','wwwroot\css\site.css','wwwroot\js\site.js','wwwroot\lib\bootstrap\dist\css\bootstrap.min.css','wwwroot\lib\jquery\dist\jquery.min.js','wwwroot\lib\sweetalert2\dist\sweetalert2.min.js','wwwroot\lib\datatables\datatables.min.js','wwwroot\lib\datatables\datatables.min.css','wwwroot\lib\datatables\LICENSE.core.txt','wwwroot\lib\datatables\package.core.json')) {
        $item = Get-Item -LiteralPath (Join-Path $Path $relative) -ErrorAction SilentlyContinue
        if ($null -eq $item -or $item.Length -le 0) { throw "Published payload is incomplete: $relative" }
    }
}

function Install-CodexRelaySecrets([string]$Destination) {
    if (-not (Test-Path -LiteralPath $codexRelaySecretPath -PathType Leaf)) { return $false }
    $item = Get-Item -LiteralPath $codexRelaySecretPath -Force
    if ($item.Length -lt 128 -or $item.Length -gt 16384 -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Codex relay secret document is outside policy.'
    }
    $document = Get-Content -LiteralPath $codexRelaySecretPath -Raw | ConvertFrom-Json
    $values = @(
        [string]$document.Operations.CodexRelay.PublisherSecret,
        [string]$document.Operations.CodexRelay.Nodes.taichung.Secret,
        [string]$document.Operations.CodexRelay.Nodes.taoyuan.Secret
    )
    foreach ($value in $values) {
        try { $bytes = [Convert]::FromBase64String($value) } catch { throw 'Codex relay secret document contains invalid base64.' }
        if ($bytes.Length -lt 32 -or $bytes.Length -gt 64) { throw 'Codex relay secret length is outside policy.' }
        [Security.Cryptography.CryptographicOperations]::ZeroMemory($bytes)
    }
    Copy-Item -LiteralPath $codexRelaySecretPath -Destination (Join-Path $Destination 'appsettings.Production.json') -Force
    return $true
}

function Stop-ProvenNgrok {
    $state = Get-PublicSiteRuntimeState -AllowLegacy
    $domainProcesses = @(Get-CimInstance Win32_Process -Filter "Name='ngrok.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine.Contains("--domain=$script:PublicSiteDomain",[StringComparison]::Ordinal) })
    $owned = $null
    if ($null -ne $state) {
        $port = if ($state.schemaVersion -eq 1) { 8792 } else { 8080 }
        $expectedHash = if ($state.schemaVersion -eq 3) { [string]$state.ngrokImageSha256 } else { '' }
        $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$state.ngrokPid) -Paths $paths -UpstreamPort $port -ExpectedHash $expectedHash
        if ($domainProcesses.Count -gt 0 -and $null -eq $owned) { throw 'Runtime-state ngrok ownership could not be proven.' }
    } elseif ($domainProcesses.Count -gt 0) {
        if ($domainProcesses.Count -ne 1) { throw 'Multiple ngrok processes claim the fixed domain.' }
        $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$domainProcesses[0].ProcessId) -Paths $paths -UpstreamPort 8080
        if ($null -eq $owned) { throw 'Domain ngrok has an unexpected upstream or executable.' }
    }
    if ($null -ne $owned) { $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop; $process.Kill($true); if (-not $process.WaitForExit(10000)) { throw 'Managed ngrok did not stop.' } }
    if (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf) { Remove-Item -LiteralPath $script:PublicSiteState -Force }
}

function Stop-ProvenLegacySite {
    $state = Get-PublicSiteRuntimeState -AllowLegacy
    $expected = if ($null -ne $state -and $state.schemaVersion -eq 1) { [int]$state.sitePid } else { 0 }
    $legacy = Get-VerifiedLegacySiteProcess -Paths $paths -ExpectedProcessId $expected
    if ($null -ne $legacy) { $process = Get-Process -Id $legacy.ProcessId -ErrorAction Stop; $process.Kill($true); if (-not $process.WaitForExit(10000)) { throw 'Managed legacy site did not stop.' } }
}

function Set-IisContract {
    $pool = ((& $paths.AppCmd list apppool $script:IisAppPoolName /text:name 2>$null) -join '').Trim()
    if ($pool -cne $script:IisAppPoolName) { Invoke-AppCmdChecked @('add','apppool',"/name:$script:IisAppPoolName") }
    Invoke-AppCmdChecked @('set','apppool',$script:IisAppPoolName,'/managedRuntimeVersion:','/managedPipelineMode:Integrated','/startMode:AlwaysRunning')
    $site = ((& $paths.AppCmd list site $script:IisSiteName /text:name 2>$null) -join '').Trim()
    if ($site -cne $script:IisSiteName) { Invoke-AppCmdChecked @('add','site',"/name:$script:IisSiteName","/bindings:$script:IisBinding","/physicalPath:$script:PublicSitePublish",'/serverAutoStart:false') }
    else {
        Invoke-AppCmdChecked @('set','site',$script:IisSiteName,"/bindings:$script:IisBinding",'/serverAutoStart:false')
        Invoke-AppCmdChecked @('set','vdir',"$script:IisSiteName/","/physicalPath:$script:PublicSitePublish")
    }
    Invoke-AppCmdChecked @('set','app',"$script:IisSiteName/","/applicationPool:$script:IisAppPoolName")
}

function Start-IisContract {
    Invoke-AppCmdChecked @('set','site',$script:IisSiteName,'/serverAutoStart:true')
    $siteState = ((& $paths.AppCmd list site $script:IisSiteName /text:state 2>$null) -join '').Trim()
    if ($siteState -cne 'Started') { Invoke-AppCmdChecked @('start','site',"/site.name:$script:IisSiteName") }
    $poolState = ((& $paths.AppCmd list apppool $script:IisAppPoolName /text:state 2>$null) -join '').Trim()
    if ($poolState -cne 'Started') { Invoke-AppCmdChecked @('start','apppool',"/apppool.name:$script:IisAppPoolName") }
}

try {
    dotnet publish $project -c Release -o $temporaryPublish --nologo
    if ($LASTEXITCODE -ne 0) { throw 'AevryndWeb Release publish failed.' }
    Test-PublishPayload $temporaryPublish
    $relaySecretsInstalled = Install-CodexRelaySecrets $temporaryPublish
    New-Item -ItemType Directory -Path $temporaryScripts | Out-Null
    foreach ($name in @('PublicSite.Common.ps1','Start-PublicSite.ps1','Stop-PublicSite.ps1','Run-ScheduledPublicSite.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $temporaryScripts $name) }
    $parseErrors = @(); Get-ChildItem $temporaryScripts -Filter *.ps1 | ForEach-Object { $tokens=$null; $errors=$null; [Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors) | Out-Null; $parseErrors += $errors }
    if ($parseErrors.Count) { throw 'Managed scripts failed parser validation.' }

    Invoke-AppCmdChecked @('add','backup',$iisBackup); $iisBackupCreated = $true; $rollbackRequired = $true
    Stop-ProvenLegacySite
    Stop-ProvenNgrok
    if (Get-NetTCPConnection -State Listen -LocalPort 8792 -ErrorAction SilentlyContinue) { throw 'Port 8792 still has a listener after exact legacy shutdown.' }
    $standalone = @(Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine.Contains($paths.Assembly,[StringComparison]::OrdinalIgnoreCase) })
    if ($standalone.Count -gt 0) { throw 'A managed-publish standalone dotnet process remains; IIS cannot become the unique instance.' }
    & $paths.AppCmd stop apppool "/apppool.name:$script:IisAppPoolName" 2>$null | Out-Null
    if ($hadPublish) { Move-Item -LiteralPath $script:PublicSitePublish -Destination $backupPublish }
    Move-Item -LiteralPath $temporaryPublish -Destination $script:PublicSitePublish; $publishSwapped = $true
    Set-IisContract
    Initialize-IisContentAcl
    Initialize-OperationsDirectories
    Start-IisContract
    for ($attempt=0;$attempt-lt 40 -and -not (Test-PublicSiteLocal);$attempt++){Start-Sleep -Milliseconds 500}
    if (-not (Test-PublicSiteLocal)) { throw 'IIS local health verification failed.' }
    $null = Assert-IisConfiguration -Paths $paths
    & $pwsh -NoProfile -NonInteractive -File (Join-Path $PSScriptRoot 'Start-PublicSite.ps1')
    if ($LASTEXITCODE -ne 0 -or -not (Test-PublicSiteExternal)) { throw 'External verification failed.' }

    if ($hadScripts) { Move-Item -LiteralPath $managedScripts -Destination $backupScripts }
    Move-Item -LiteralPath $temporaryScripts -Destination $managedScripts; $scriptsSwapped = $true
    $scheduled = Join-Path $managedScripts 'Run-ScheduledPublicSite.ps1'
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("`$ErrorActionPreference='Stop'; & '$scheduled'; [Environment]::Exit(0)"))
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoLogo -NoProfile -NonInteractive -EncodedCommand $encoded"
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Keeps the fixed ngrok route attached to the IIS-hosted AevryndWeb site.' -Force | Out-Null
    $null = Assert-IisConfiguration -Paths $paths
    if (-not (Test-PublicSiteLocal) -or -not (Test-PublicSiteExternal)) { throw 'Post-commit verification failed.' }
    # 此後新站已提交；清理失敗只能留下可回收備份，不得拆除已驗證服務。
    $committed = $true; $deploymentSucceeded = $true
    if ($hadPublish) { $null = Invoke-NonFatalCommittedCleanup -Label 'publish' -Action { Remove-Item -LiteralPath $backupPublish -Recurse -Force } }
    if ($hadScripts) { $null = Invoke-NonFatalCommittedCleanup -Label 'scripts' -Action { Remove-Item -LiteralPath $backupScripts -Recurse -Force } }
    if (Invoke-NonFatalCommittedCleanup -Label "IIS '$iisBackup'" -Action { Invoke-AppCmdChecked @('delete','backup',$iisBackup) }) { $iisBackupCreated = $false }
    Write-Output 'AevryndWeb IIS deployment committed after local, external, ownership and configuration verification.'
    Write-Output "IIS_PHYSICAL_PATH=$script:PublicSitePublish"
    Write-Output "IIS_UPSTREAM=127.0.0.1:$script:PublicSitePort"
    Write-Output "CODEX_RELAY_SECRETS=$relaySecretsInstalled"
} catch {
    $deploymentError = $_
    if ($committed) { Write-Warning "Post-commit cleanup failed without rollback: $($deploymentError.Exception.Message)"; return }
    # IIS backup 尚未成功代表部署尚未跨越第一個異動邊界；只清除暫存，不觸碰既有服務。
    if (-not $rollbackRequired) { throw $deploymentError }
    try {
        Stop-ProvenNgrok
        if ($iisBackupCreated) { Invoke-AppCmdChecked @('restore','backup',$iisBackup) }
        if (($publishSwapped -or (Test-Path -LiteralPath $backupPublish -PathType Container)) -and (Test-Path -LiteralPath $script:PublicSitePublish -PathType Container)) { Remove-Item -LiteralPath $script:PublicSitePublish -Recurse -Force }
        if ($hadPublish -and (Test-Path -LiteralPath $backupPublish -PathType Container)) { Move-Item -LiteralPath $backupPublish -Destination $script:PublicSitePublish }
        if (($scriptsSwapped -or (Test-Path -LiteralPath $backupScripts -PathType Container)) -and (Test-Path -LiteralPath $managedScripts -PathType Container)) { Remove-Item -LiteralPath $managedScripts -Recurse -Force }
        if ($hadScripts -and (Test-Path -LiteralPath $backupScripts -PathType Container)) { Move-Item -LiteralPath $backupScripts -Destination $managedScripts }
        if ($null -ne $previousTaskXml) { Register-ScheduledTask -TaskName $taskName -Xml $previousTaskXml -Force | Out-Null } else { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue }
        if ($hadScripts) { & $pwsh -NoProfile -NonInteractive -File (Join-Path $managedScripts 'Start-PublicSite.ps1') }
        # 只有全部復原步驟完成後才能清除 IIS backup；中途失敗必須保留人工復原依據。
        $rollbackSucceeded = $true
    } catch { throw "Deployment failed and rollback failed. Deployment: $($deploymentError.Exception.Message) Rollback: $($_.Exception.Message)" }
    throw $deploymentError
} finally {
    if ($iisBackupCreated -and ($deploymentSucceeded -or $rollbackSucceeded)) { & $paths.AppCmd delete backup $iisBackup 2>$null | Out-Null }
    if (Test-Path -LiteralPath $temporaryRoot -PathType Container) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
