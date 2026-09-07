[CmdletBinding(SupportsShouldProcess)]
param([hashtable]$ValidationCallbacks = $null)
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

function Invoke-PublicSiteInstallCallbacks {
    param([Parameter(Mandatory)][hashtable]$Callbacks)
    $names = @('CapturePreviousRoute','BackupIis','StopPreviousRoute','SwapPublish','ConfigureIis','VerifyLocal','StartExternal','VerifyExternal','SwapScripts','HardenScripts','RegisterTask','VerifyCommit','Rollback')
    foreach ($name in $names) { if ($Callbacks[$name] -isnot [scriptblock]) { throw "Install validation callback is missing: $name" } }
    $previous = & $Callbacks.CapturePreviousRoute
    $mutationBoundaryCrossed = $false
    try {
        & $Callbacks.BackupIis; $mutationBoundaryCrossed = $true
        foreach ($name in @('StopPreviousRoute','SwapPublish','ConfigureIis','VerifyLocal','StartExternal','VerifyExternal','SwapScripts','HardenScripts','RegisterTask','VerifyCommit')) { & $Callbacks[$name] $previous }
        return $previous
    } catch {
        $installError = $_
        if ($mutationBoundaryCrossed) { & $Callbacks.Rollback $previous $installError }
        throw $installError
    }
}

if ($null -ne $ValidationCallbacks) {
    $null = Invoke-PublicSiteInstallCallbacks -Callbacks $ValidationCallbacks
    Write-Output 'VALIDATION_INSTALL_CALLBACKS_OK'
    return
}

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
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$previousRoute = $null
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

function Install-ProductionSecrets([string]$Destination) {
    $gmailPassword = [AevryndWebCredentialProcess]::LoadValue($script:GmailCredentialTarget)
    $gmailPassword = $gmailPassword.Replace(' ','')
    $invalidGmailCharacters = @($gmailPassword.ToCharArray() | Where-Object { -not [char]::IsAsciiLetterOrDigit($_) })
    if ($gmailPassword.Length -ne 16 -or $invalidGmailCharacters.Count -ne 0) {
        throw 'Gmail credential does not satisfy the production readiness contract.'
    }
    $production = [ordered]@{ Email = [ordered]@{ Gmail = [ordered]@{ AppPassword = $gmailPassword } } }
    $relayInstalled = $false
    if (Test-Path -LiteralPath $codexRelaySecretPath -PathType Leaf) {
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
        $production.Operations = $document.Operations
        $relayInstalled = $true
    }
    $production | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Destination 'appsettings.Production.json') -Encoding utf8NoBOM
    $gmailPassword = $null
    return $relayInstalled
}

function Stop-NewIisRoute {
    $domainProcesses = @(Get-PublicSiteDomainProcesses)
    $previousStillRunning = $false
    if ($domainProcesses.Count -gt 0) {
        if ($domainProcesses.Count -ne 1) { throw 'Multiple ngrok processes claim the fixed domain.' }
        if ($null -ne $previousRoute -and -not $previousRoute.NgrokStopped -and [int]$domainProcesses[0].ProcessId -eq [int]$previousRoute.NgrokProcessId) {
            $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$previousRoute.NgrokProcessId) -Paths $paths -UpstreamPort ([int]$previousRoute.UpstreamPort) -ExpectedHash ([string]$previousRoute.NgrokImageSha256)
            if ($null -eq $owned) { throw 'The preserved previous ngrok route drifted during rollback.' }
            $previousStillRunning = $true
        } else {
            $owned = Get-VerifiedPublicSiteProcess -ProcessId ([int]$domainProcesses[0].ProcessId) -Paths $paths -UpstreamPort 8080
            if ($null -eq $owned) { throw 'The new IIS ngrok route cannot be proven during rollback.' }
            $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop
            $process.Kill($true)
            if (-not $process.WaitForExit(10000)) { throw 'New IIS ngrok did not stop during rollback.' }
        }
    }
    if (Test-Path -LiteralPath $script:PublicSiteState -PathType Leaf) { Remove-Item -LiteralPath $script:PublicSiteState -Force }
    if (-not ($previousStillRunning -and $previousRoute.Kind -eq 'Iis')) {
        & $paths.AppCmd stop site "/site.name:$script:IisSiteName" 2>$null | Out-Null
        & $paths.AppCmd stop apppool "/apppool.name:$script:IisAppPoolName" 2>$null | Out-Null
    }
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
    if (-not [AevryndWebCredentialProcess]::Available($script:GmailCredentialTarget, 16, 64)) { throw 'Gmail credential is unavailable for IIS production deployment.' }
    if (-not [AevryndWebCredentialProcess]::Available($script:NgrokCredentialTarget, 20, 512)) { throw 'Ngrok credential is unavailable for public routing.' }
    dotnet publish $project -c Release -o $temporaryPublish --nologo
    if ($LASTEXITCODE -ne 0) { throw 'AevryndWeb Release publish failed.' }
    Test-PublishPayload $temporaryPublish
    $relaySecretsInstalled = Install-ProductionSecrets $temporaryPublish
    # Production secrets must be protected before the directory becomes the live IIS physical path.
    Initialize-IisContentAcl -PublishPath $temporaryPublish -SkipRoot
    New-Item -ItemType Directory -Path $temporaryScripts | Out-Null
    foreach ($name in @('PublicSite.Common.ps1','Start-PublicSite.ps1','Stop-PublicSite.ps1','Run-ScheduledPublicSite.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $temporaryScripts $name) }
    $parseErrors = @(); Get-ChildItem $temporaryScripts -Filter *.ps1 | ForEach-Object { $tokens=$null; $errors=$null; [Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors) | Out-Null; $parseErrors += $errors }
    if ($parseErrors.Count) { throw 'Managed scripts failed parser validation.' }
    # 提升權限排程建立前，候選腳本必須先移除繼承並完成唯讀回驗。
    $null = Initialize-ManagedScriptsAcl -ScriptsPath $temporaryScripts -TaskPrincipal $currentUser

    # 在任何服務、IIS 組態或 live 目錄異動前，保存可供 rollback 使用的完整既有路由契約。
    $previousRoute = Get-PreviousPublicSiteRouteContract -Paths $paths

    Invoke-AppCmdChecked @('add','backup',$iisBackup); $iisBackupCreated = $true; $rollbackRequired = $true
    Stop-ProvenPreviousPublicSiteRoute -Contract $previousRoute -Paths $paths
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
    # 在同一提升程序啟動通道，避免長效 ngrok 持有巢狀 pwsh 的輸出管線而讓部署永久等待。
    & (Join-Path $PSScriptRoot 'Start-PublicSite.ps1')
    if (-not (Test-PublicSiteExternal)) { throw 'External verification failed.' }

    if ($hadScripts) { Move-Item -LiteralPath $managedScripts -Destination $backupScripts }
    Move-Item -LiteralPath $temporaryScripts -Destination $managedScripts; $scriptsSwapped = $true
    $null = Initialize-ManagedScriptsAcl -ScriptsPath $managedScripts -TaskPrincipal $currentUser
    $scheduled = Join-Path $managedScripts 'Run-ScheduledPublicSite.ps1'
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("`$ErrorActionPreference='Stop'; & '$scheduled'; [Environment]::Exit(0)"))
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-WindowStyle Hidden -NoLogo -NoProfile -NonInteractive -EncodedCommand $encoded"
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    # 啟動腳本必須讀取 IIS 組態以證明 8080 的 exact-origin ownership；Limited token 會在 redirection.config 上失敗。
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Highest
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
        Invoke-PublicSiteRollbackTransaction `
            -StopNewIis { Stop-NewIisRoute } `
            -RestoreIis { if ($iisBackupCreated) { Invoke-AppCmdChecked @('restore','backup',$iisBackup) } } `
            -RestoreDirectories {
                if (($publishSwapped -or (Test-Path -LiteralPath $backupPublish -PathType Container)) -and (Test-Path -LiteralPath $script:PublicSitePublish -PathType Container)) { Remove-Item -LiteralPath $script:PublicSitePublish -Recurse -Force }
                if ($hadPublish -and (Test-Path -LiteralPath $backupPublish -PathType Container)) { Move-Item -LiteralPath $backupPublish -Destination $script:PublicSitePublish }
                if (($scriptsSwapped -or (Test-Path -LiteralPath $backupScripts -PathType Container)) -and (Test-Path -LiteralPath $managedScripts -PathType Container)) { Remove-Item -LiteralPath $managedScripts -Recurse -Force }
                if ($hadScripts -and (Test-Path -LiteralPath $backupScripts -PathType Container)) { Move-Item -LiteralPath $backupScripts -Destination $managedScripts }
            } `
            -RestoreTaskAndAcl {
                if ($null -ne $previousTaskXml) {
                    if ($previousTaskXml -match '<RunLevel>HighestAvailable</RunLevel>' -and $hadScripts) { $null = Initialize-ManagedScriptsAcl -ScriptsPath $managedScripts -TaskPrincipal $currentUser }
                    Register-ScheduledTask -TaskName $taskName -Xml $previousTaskXml -Force | Out-Null
                } else { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue }
            } `
            -RestartPreviousRoute {
                if ($previousRoute.Kind -eq 'Iis') { Start-IisContract }
                $null = Restore-PreviousPublicSiteRoute -Contract $previousRoute -Paths $paths
            } `
            -VerifyPreviousRoute {
                if ($previousRoute.WasHealthy -and (-not (Test-PublicSiteOriginHealthy -Port ([int]$previousRoute.UpstreamPort)) -or -not (Test-PublicSiteExternal))) { throw 'Rollback restored artifacts but not the previously healthy route.' }
                # runtime state 在舊路由通過健康驗證後才原子恢復，避免留下指向未就緒程序的狀態。
                Restore-PreviousPublicSiteRuntimeState -Contract $previousRoute
            }
        # 只有全部復原步驟完成後才能清除 IIS backup；中途失敗必須保留人工復原依據。
        $rollbackSucceeded = $true
    } catch { throw "Deployment failed and rollback failed. Deployment: $($deploymentError.Exception.Message) Rollback: $($_.Exception.Message)" }
    throw $deploymentError
} finally {
    if ($iisBackupCreated -and ($deploymentSucceeded -or $rollbackSucceeded)) { & $paths.AppCmd delete backup $iisBackup 2>$null | Out-Null }
    if (Test-Path -LiteralPath $temporaryRoot -PathType Container) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
