Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PublicSite.Common.ps1')

$projectRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $projectRoot 'AevryndWeb.csproj'
$temporaryRoot = Join-Path $env:TEMP ("AevryndWeb-publish-" + [Guid]::NewGuid().ToString('N'))
$temporaryPublish = Join-Path $temporaryRoot 'publish'
$backupPublish = "$script:PublicSitePublish.rollback-$([Guid]::NewGuid().ToString('N'))"
$managedScripts = Join-Path $script:PublicSiteRoot 'scripts'
$legacyPublicSiteRoot = Join-Path $env:LOCALAPPDATA 'AevryndWeb'
$legacyPublicSitePublish = Join-Path $legacyPublicSiteRoot 'publish'
$legacyStartScript = Join-Path $legacyPublicSiteRoot 'scripts\Start-PublicSite.ps1'
$legacyFallbackAvailable = Test-Path -LiteralPath (Join-Path $legacyPublicSitePublish 'AevryndWeb.dll') -PathType Leaf
$fixedPwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'
$deploymentSucceeded = $false
$restartMayBeNeeded = $false
$hadPreviousPublish = Test-Path -LiteralPath $script:PublicSitePublish -PathType Container

New-Item -ItemType Directory -Path $script:PublicSiteRoot -Force | Out-Null
New-Item -ItemType Directory -Path $managedScripts -Force | Out-Null
Initialize-RemoteTelemetryDirectory

if (Test-Path -LiteralPath $fixedPwsh -PathType Leaf) {
    $pwsh = $fixedPwsh
} else {
    $pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
    if (-not (Test-Path -LiteralPath $pwsh -PathType Leaf)) { throw 'A durable PowerShell 7 executable was not found.' }
}

function Stop-VerifiedPublishedSite {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $script:PublicSitePort -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { return }
    if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -cne '127.0.0.1') {
        throw 'Port 8792 is not exclusively owned by the managed loopback site.'
    }
    $candidate = Get-CimInstance Win32_Process -Filter "ProcessId=$($listeners[0].OwningProcess)" -ErrorAction Stop
    $expectedAssembly = Join-Path $script:PublicSitePublish 'AevryndWeb.dll'
    $legacyAssembly = Join-Path $legacyPublicSitePublish 'AevryndWeb.dll'
    $isManagedAssembly = $candidate.CommandLine.Contains($expectedAssembly, [StringComparison]::OrdinalIgnoreCase) -or
        $candidate.CommandLine.Contains($legacyAssembly, [StringComparison]::OrdinalIgnoreCase)
    if ($candidate.Name -cne 'dotnet.exe' -or -not $isManagedAssembly) {
        throw 'Port 8792 is occupied by an unmanaged process.'
    }
    $owned = Get-Process -Id $candidate.ProcessId -ErrorAction Stop
    $owned.Kill($true)
    if (-not $owned.WaitForExit(10000)) { throw 'The prior AevryndWeb process did not stop in time.' }
}

function Test-PublishPayload {
    param([Parameter(Mandatory)][string]$Path)
    $required = @(
        'AevryndWeb.dll',
        'wwwroot\css\site.css',
        'wwwroot\js\site.js',
        'wwwroot\lib\bootstrap\dist\css\bootstrap.min.css',
        'wwwroot\lib\jquery\dist\jquery.min.js',
        'wwwroot\lib\sweetalert2\dist\sweetalert2.min.js'
    )
    foreach ($relativePath in $required) {
        $item = Get-Item -LiteralPath (Join-Path $Path $relativePath) -ErrorAction SilentlyContinue
        if ($null -eq $item -or -not $item.PSIsContainer -and $item.Length -le 0) {
            throw "Published payload is incomplete: $relativePath"
        }
    }
}

try {
    # 先在獨立目錄完成建置，避免失敗的編譯影響目前服務。
    dotnet publish $project -c Release -o $temporaryPublish --nologo
    if ($LASTEXITCODE -ne 0) { throw 'AevryndWeb Release publish failed.' }
    Test-PublishPayload -Path $temporaryPublish

    foreach ($scriptName in @('PublicSite.Common.ps1', 'Start-PublicSite.ps1', 'Stop-PublicSite.ps1', 'Run-ScheduledPublicSite.ps1')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $scriptName) -Destination (Join-Path $managedScripts $scriptName) -Force
    }

    $startScript = Join-Path $managedScripts 'Start-PublicSite.ps1'
    $scheduledScript = Join-Path $managedScripts 'Run-ScheduledPublicSite.ps1'
    $scheduledCommand = "`$ErrorActionPreference='Stop'; & '$scheduledScript'; [Environment]::Exit(0)"
    $encodedScheduledCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($scheduledCommand))
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoLogo -NoProfile -NonInteractive -EncodedCommand $encodedScheduledCommand"
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName 'AevryndWeb Public Site' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Starts the local AevryndWeb site and its fixed ngrok endpoint after sign-in.' -Force | Out-Null

    $restartMayBeNeeded = $true
    Stop-VerifiedPublishedSite
    if ($hadPreviousPublish) { Move-Item -LiteralPath $script:PublicSitePublish -Destination $backupPublish }
    Move-Item -LiteralPath $temporaryPublish -Destination $script:PublicSitePublish

    & $pwsh -NoProfile -NonInteractive -File $startScript
    if ($LASTEXITCODE -ne 0 -or -not (Test-PublicSiteLocal) -or -not (Test-PublicSiteExternal)) {
        throw 'The new public-site deployment did not pass live verification.'
    }
    $deploymentSucceeded = $true
    if ($hadPreviousPublish -and (Test-Path -LiteralPath $backupPublish -PathType Container)) {
        Remove-Item -LiteralPath $backupPublish -Recurse -Force
    }
    Write-Output 'AevryndWeb was built, atomically deployed, verified, and registered for sign-in startup.'
} catch {
    $deploymentError = $_
    if ($restartMayBeNeeded) {
        try {
            Stop-VerifiedPublishedSite
            $failedPublish = Join-Path $temporaryRoot 'failed-publish'
            $backupAvailable = Test-Path -LiteralPath $backupPublish -PathType Container
            if ($backupAvailable -and (Test-Path -LiteralPath $script:PublicSitePublish -PathType Container)) {
                Move-Item -LiteralPath $script:PublicSitePublish -Destination $failedPublish
            }
            if ($backupAvailable) {
                Move-Item -LiteralPath $backupPublish -Destination $script:PublicSitePublish
                & $pwsh -NoProfile -NonInteractive -File (Join-Path $managedScripts 'Start-PublicSite.ps1')
            } elseif ($hadPreviousPublish -and (Test-Path -LiteralPath (Join-Path $script:PublicSitePublish 'AevryndWeb.dll') -PathType Leaf)) {
                & $pwsh -NoProfile -NonInteractive -File (Join-Path $managedScripts 'Start-PublicSite.ps1')
            } elseif ($legacyFallbackAvailable) {
                & $pwsh -NoProfile -NonInteractive -File $legacyStartScript
            } else {
                throw 'No previously verified deployment is available for rollback.'
            }
            if ($LASTEXITCODE -ne 0 -or -not (Test-PublicSiteExternal)) { throw 'Rollback service verification failed.' }
        } catch {
            throw "Deployment failed and rollback could not be verified. Deployment: $($deploymentError.Exception.Message) Rollback: $($_.Exception.Message)"
        }
    }
    throw $deploymentError
} finally {
    if (Test-Path -LiteralPath $temporaryRoot -PathType Container) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
    if (-not $deploymentSucceeded -and -not $hadPreviousPublish -and (Test-Path -LiteralPath $backupPublish -PathType Container)) {
        Remove-Item -LiteralPath $backupPublish -Recurse -Force
    }
}
