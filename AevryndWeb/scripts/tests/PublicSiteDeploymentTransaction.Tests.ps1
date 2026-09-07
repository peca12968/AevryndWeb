[CmdletBinding()]
param(
    [string]$CommonPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'PublicSite.Common.ps1'),
    [string]$InstallerPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'Install-PublicSite.ps1'),
    [string]$ValidationRoot = (Join-Path $env:TEMP ("AevryndWeb-deployment-validation-" + [Guid]::NewGuid().ToString('N')))
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. $CommonPath
Add-PublicSiteCredentialInterop

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERT_TRUE_FAILED: $Message" }
}
function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) { throw "ASSERT_EQUAL_FAILED: $Message Expected=$Expected Actual=$Actual" }
}
function Assert-Throws([scriptblock]$Action, [string]$Pattern, [string]$Message) {
    try { & $Action; throw "ASSERT_THROWS_FAILED: $Message" }
    catch {
        if ($_.Exception.Message -like 'ASSERT_THROWS_FAILED:*') { throw }
        if ($_.Exception.Message -notmatch $Pattern) { throw "ASSERT_THROWS_WRONG_ERROR: $Message Actual=$($_.Exception.Message)" }
    }
}

New-Item -ItemType Directory -Path $ValidationRoot -Force | Out-Null
try {
    $hash = 'a' * 64
    $paths = [pscustomobject]@{
        Dotnet='C:\Program Files\dotnet\dotnet.exe'
        Assembly=(Join-Path $ValidationRoot 'publish\AevryndWeb.dll')
        Ngrok='C:\Users\test\ngrok.exe'
        NgrokImage='C:\Program Files\WindowsApps\ngrok.exe'
        NgrokHash=$hash
    }
    $claim = [pscustomobject]@{ Name='ngrok.exe'; ProcessId=41; CommandLine='synthetic exact-domain claim' }
    $legacy = Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $null -DomainProcesses @($claim) `
        -ResolveLegacy { param($Expected) [pscustomobject]@{ ProcessId=31 } } `
        -VerifyNgrok { param($ProcessIdentifier,$Port,$ExpectedHash) if ($ProcessIdentifier -eq 41 -and $Port -eq 8792 -and -not $ExpectedHash) { [pscustomobject]@{ ProcessId=41 } } } `
        -TestOrigin { param($Port) $Port -eq 8792 } -TestExternal { $true }
    Assert-Equal 'Legacy' $legacy.Kind 'State-missing legacy migration must preserve a typed legacy route.'
    Assert-Equal 31 $legacy.SiteProcessId 'The exact legacy dotnet process must be captured.'
    Assert-Equal 41 $legacy.NgrokProcessId 'The exact legacy ngrok process must be captured.'
    Assert-Equal 8792 $legacy.UpstreamPort 'The legacy upstream must remain 8792.'
    Assert-True $legacy.WasHealthy 'Only a healthy route may be accepted as the rollback baseline.'

    $noRoute = Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $null -DomainProcesses @() `
        -ResolveLegacy { $null } -VerifyNgrok { throw 'must not verify' } -TestOrigin { throw 'must not probe' } -TestExternal { throw 'must not probe' }
    Assert-Equal 'None' $noRoute.Kind 'A host with no prior site or tunnel must produce an explicit no-route contract.'

    $schema1State = [pscustomobject]@{ schemaVersion=1; sitePid=31; ngrokPid=41 }
    $schema1Route = Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $schema1State -DomainProcesses @($claim) `
        -ResolveLegacy { param($Expected) if ($Expected -eq 31) { [pscustomobject]@{ ProcessId=31 } } } `
        -VerifyNgrok { param($ProcessIdentifier,$Port,$ExpectedHash) if ($ProcessIdentifier -eq 41 -and $Port -eq 8792) { [pscustomobject]@{ ProcessId=41 } } } `
        -TestOrigin { param($Port) $Port -eq 8792 } -TestExternal { $true }
    Assert-Equal 'Legacy' $schema1Route.Kind 'Schema 1 must admit only the exact 8792 legacy tuple.'

    $schema2State = [pscustomobject]@{ schemaVersion=2; ngrokPid=41 }
    $schema2Route = Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $schema2State -DomainProcesses @($claim) `
        -ResolveLegacy { $null } `
        -VerifyNgrok { param($ProcessIdentifier,$Port,$ExpectedHash) if ($ProcessIdentifier -eq 41 -and $Port -eq 8080) { [pscustomobject]@{ ProcessId=41 } } } `
        -TestOrigin { param($Port) $Port -eq 8080 } -TestExternal { $true }
    Assert-Equal 'Iis' $schema2Route.Kind 'Schema 2 must admit only the exact 8080 IIS tuple.'
    Assert-Throws {
        Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState ([pscustomobject]@{ schemaVersion=2; ngrokPid=42 }) -DomainProcesses @($claim) `
            -ResolveLegacy { $null } -VerifyNgrok { [pscustomobject]@{ ProcessId=42 } } -TestOrigin { $true } -TestExternal { $true }
    } 'disagree' 'State PID mismatch must fail before any route mutation.'
    Assert-Throws {
        Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $schema1State -DomainProcesses @($claim) `
            -ResolveLegacy { [pscustomobject]@{ ProcessId=31 } } -VerifyNgrok { [pscustomobject]@{ ProcessId=41 } } `
            -TestOrigin { $true } -TestExternal { $false }
    } 'not healthy enough' 'Origin healthy but external unhealthy admission must fail closed.'

    Assert-Throws {
        Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $null -DomainProcesses @($claim,$claim) `
            -ResolveLegacy { [pscustomobject]@{ ProcessId=31 } } -VerifyNgrok { [pscustomobject]@{ ProcessId=41 } } `
            -TestOrigin { $true } -TestExternal { $true }
    } 'Multiple ngrok' 'Multiple fixed-domain claimants must fail closed.'
    Assert-Throws {
        Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $null -DomainProcesses @($claim) `
            -ResolveLegacy { [pscustomobject]@{ ProcessId=31 } } -VerifyNgrok { $null } `
            -TestOrigin { $true } -TestExternal { $true }
    } 'outside the exact contract' 'Wrong executable, hash, or upstream must fail closed.'

    $observedPort = 0
    $iisState = [pscustomobject]@{ schemaVersion=3; upstream='iis'; ngrokPid=41; ngrokImageSha256=$hash }
    $iis = Get-PreviousPublicSiteRouteContract -Paths $paths -RuntimeState $iisState -DomainProcesses @($claim) `
        -ResolveLegacy { $null } `
        -VerifyNgrok { param($ProcessIdentifier,$Port,$ExpectedHash) $script:observedPort=$Port; [pscustomobject]@{ ProcessId=$ProcessIdentifier } } `
        -TestOrigin { param($Port) $Port -eq 8080 } -TestExternal { $true }
    Assert-Equal 'Iis' $iis.Kind 'Schema 3 must preserve an IIS route.'
    Assert-Equal 8080 $iis.UpstreamPort 'IIS route verification must require ngrok upstream 8080.'
    Assert-Equal 8080 $observedPort 'The verifier must receive the exact IIS upstream.'

    $partial = [pscustomobject]@{ Kind='Legacy'; UpstreamPort=8792; SiteProcessId=31; NgrokProcessId=41; NgrokImageSha256=$hash; SiteStopped=$false; NgrokStopped=$false }
    $partialStops = [Collections.Generic.List[int]]::new()
    Assert-Throws {
        Stop-ProvenPreviousPublicSiteRoute -Contract $partial -Paths $paths -StatePath (Join-Path $ValidationRoot 'partial-runtime.json') `
            -VerifyNgrok { [pscustomobject]@{ ProcessId=41 } } -VerifyLegacy { [pscustomobject]@{ ProcessId=31 } } `
            -StopProcess { param($ProcessIdentifier,$Label) $partialStops.Add($ProcessIdentifier); if ($ProcessIdentifier -eq 31) { throw 'injected-site-stop' } }
    } 'injected-site-stop' 'A site-stop failure after ngrok stop must preserve partial transition truth.'
    Assert-Equal '41,31' ($partialStops -join ',') 'Partial transition must stop the verified ngrok before attempting the verified legacy site.'
    Assert-True $partial.NgrokStopped 'Partial transition must record that ngrok was stopped.'
    Assert-True (-not $partial.SiteStopped) 'Partial transition must not claim the failed legacy stop succeeded.'

    $restore = [pscustomobject]@{ Kind='Legacy'; UpstreamPort=8792; SiteProcessId=31; NgrokProcessId=41; NgrokImageSha256=$hash; SiteExecutable=$paths.Dotnet; SiteAssembly=$paths.Assembly; SiteStopped=$true; NgrokStopped=$true }
    $null = Restore-PreviousPublicSiteRoute -Contract $restore -Paths $paths `
        -StartLegacy { [pscustomobject]@{ Id=131 } } -StartNgrok { [pscustomobject]@{ Id=141 } } `
        -TestOrigin { $true } -VerifyLegacy { param($ProcessIdentifier) [pscustomobject]@{ ProcessId=$ProcessIdentifier } } `
        -VerifyNgrok { param($ProcessIdentifier) [pscustomobject]@{ ProcessId=$ProcessIdentifier } } -TestExternal { $true } -StopFailedProcess { throw 'must not clean successful restore' }
    Assert-Equal 131 $restore.SiteProcessId 'Successful restore must publish the newly verified site PID.'
    Assert-Equal 141 $restore.NgrokProcessId 'Successful restore must publish the newly verified ngrok PID.'

    $failedRestore = [pscustomobject]@{ Kind='Legacy'; UpstreamPort=8792; SiteProcessId=31; NgrokProcessId=41; NgrokImageSha256=$hash; SiteExecutable=$paths.Dotnet; SiteAssembly=$paths.Assembly; SiteStopped=$true; NgrokStopped=$true }
    $cleanup = [Collections.Generic.List[int]]::new()
    Assert-Throws {
        Restore-PreviousPublicSiteRoute -Contract $failedRestore -Paths $paths `
            -StartLegacy { [pscustomobject]@{ Id=131 } } -StartNgrok { [pscustomobject]@{ Id=141 } } `
            -TestOrigin { $true } -VerifyLegacy { param($ProcessIdentifier) [pscustomobject]@{ ProcessId=$ProcessIdentifier } } `
            -VerifyNgrok { param($ProcessIdentifier) [pscustomobject]@{ ProcessId=$ProcessIdentifier } } -TestExternal { $false } `
            -StopFailedProcess { param($ProcessIdentifier) $cleanup.Add($ProcessIdentifier) }
    } 'exact external verification' 'External failure must reject and clean newly launched rollback processes.'
    Assert-Equal '141,131' ($cleanup -join ',') 'External failure cleanup must stop new tunnel before new site.'

    Assert-True (Test-PublicSiteReadinessPayload -Payload ([pscustomobject]@{ status='ok'; emailReady=$true })) 'IIS readiness requires emailReady=true.'
    Assert-True (-not (Test-PublicSiteReadinessPayload -Payload ([pscustomobject]@{ status='ok'; emailReady=$false }))) 'emailReady=false must fail readiness.'
    Assert-True (-not (Test-PublicSiteReadinessPayload -Payload ([pscustomobject]@{ status='ok'; emailReady='true' }))) 'String emailReady must fail the typed readiness schema.'

    $stepNames = @('stop-new-iis','restore-iis','restore-directories','restore-task-acl','restart-previous','verify-previous')
    for ($failureIndex=-1; $failureIndex -lt $stepNames.Count; $failureIndex++) {
        $events = [Collections.Generic.List[string]]::new()
        $steps = foreach ($index in 0..($stepNames.Count-1)) {
            $capturedIndex = $index
            $capturedName = $stepNames[$index]
            { $events.Add($capturedName); if ($failureIndex -eq $capturedIndex) { throw "injected-$capturedName" } }.GetNewClosure()
        }
        if ($failureIndex -lt 0) {
            Invoke-PublicSiteRollbackTransaction -StopNewIis $steps[0] -RestoreIis $steps[1] -RestoreDirectories $steps[2] -RestoreTaskAndAcl $steps[3] -RestartPreviousRoute $steps[4] -VerifyPreviousRoute $steps[5]
            Assert-Equal ($stepNames -join ',') ($events -join ',') 'Successful rollback must follow the exact recovery order.'
        } else {
            Assert-Throws {
                Invoke-PublicSiteRollbackTransaction -StopNewIis $steps[0] -RestoreIis $steps[1] -RestoreDirectories $steps[2] -RestoreTaskAndAcl $steps[3] -RestartPreviousRoute $steps[4] -VerifyPreviousRoute $steps[5]
            } "injected-$([regex]::Escape($stepNames[$failureIndex]))" "Rollback boundary $failureIndex must propagate its first failure."
            Assert-Equal (($stepNames[0..$failureIndex]) -join ',') ($events -join ',') "Rollback must not cross failed boundary $failureIndex."
        }
    }

    $installBoundaryNames = @('CapturePreviousRoute','BackupIis','StopPreviousRoute','SwapPublish','ConfigureIis','VerifyLocal','StartExternal','VerifyExternal','SwapScripts','HardenScripts','RegisterTask','VerifyCommit')
    foreach ($failureName in @('') + $installBoundaryNames) {
        $installEvents = [Collections.Generic.List[string]]::new()
        $callbacks = @{}
        foreach ($boundaryName in $installBoundaryNames) {
            $capturedBoundary = $boundaryName
            $callbacks[$boundaryName] = {
                $installEvents.Add($capturedBoundary)
                if ($failureName -ceq $capturedBoundary) { throw "install-injected-$capturedBoundary" }
                if ($capturedBoundary -ceq 'CapturePreviousRoute') { return [pscustomobject]@{ Kind='None' } }
            }.GetNewClosure()
        }
        $callbacks.Rollback = { param($Previous,$Failure) $installEvents.Add('Rollback') }
        if (-not $failureName) {
            $result = @(& $InstallerPath -ValidationCallbacks $callbacks)
            Assert-True ($result -contains 'VALIDATION_INSTALL_CALLBACKS_OK') 'Install callback runner must report successful completion.'
            Assert-Equal ($installBoundaryNames -join ',') ($installEvents -join ',') 'Install validation must execute the production boundary order.'
        } else {
            Assert-Throws { & $InstallerPath -ValidationCallbacks $callbacks } "install-injected-$([regex]::Escape($failureName))" "Install boundary $failureName must expose the injected first divergence."
            $failureIndex = [Array]::IndexOf($installBoundaryNames,$failureName)
            $expectedEvents = @($installBoundaryNames[0..$failureIndex])
            if ($failureIndex -ge 2) { $expectedEvents += 'Rollback' }
            Assert-Equal ($expectedEvents -join ',') ($installEvents -join ',') "Install boundary $failureName must invoke rollback exactly after IIS backup crossed the mutation boundary."
        }
    }

    $taskPrincipal = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $taskSid = [Security.Principal.NTAccount]::new($taskPrincipal).Translate([Security.Principal.SecurityIdentifier])
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true,$false)
    $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    $inherit = [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit
    $propagation = [Security.AccessControl.PropagationFlags]::None
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[Security.AccessControl.FileSystemRights]::FullControl,$inherit,$propagation,[Security.AccessControl.AccessControlType]::Allow))
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'),[Security.AccessControl.FileSystemRights]::FullControl,$inherit,$propagation,[Security.AccessControl.AccessControlType]::Allow))
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($taskSid,[Security.AccessControl.FileSystemRights]::ReadAndExecute,$inherit,$propagation,[Security.AccessControl.AccessControlType]::Allow))
    $aclEvents = [Collections.Generic.List[string]]::new()
    $null = Initialize-ManagedScriptsAcl -ScriptsPath (Join-Path $ValidationRoot 'scripts') -TaskPrincipal $taskPrincipal `
        -InvokeAcl { param($Path,$Arguments) $aclEvents.Add(($Arguments -join ' ')) } `
        -ReadAcl { param($Path) $acl }
    Assert-Equal 3 $aclEvents.Count 'Scripts ACL provisioning must execute owner, exact grants and inheritance separately.'
    Assert-True $aclEvents[0].Contains('/setowner') 'Scripts owner must be set in a separate native icacls invocation.'
    Assert-True $aclEvents[1].Contains('/grant:r') 'Exact grants must be installed before inherited access is removed.'
    Assert-True $aclEvents[2].Contains('/inheritance:r') 'Scripts inheritance must be removed in its own final native call before task registration.'

    $realAclRoot = Join-Path $ValidationRoot 'real-acl'
    New-Item -ItemType Directory -Path $realAclRoot -Force | Out-Null
    $taskSidValue = $taskSid.Value
    $null = Initialize-ManagedScriptsAcl -ScriptsPath $realAclRoot -TaskPrincipal $taskPrincipal -OwnerPrincipal "*$taskSidValue"
    $realAcl = Get-Acl -LiteralPath $realAclRoot
    Assert-True $realAcl.AreAccessRulesProtected 'Real icacls validation must remove inheritance on a fresh ValidationRoot.'
    Assert-Equal $taskSidValue $realAcl.GetOwner([Security.Principal.SecurityIdentifier]).Value 'Real icacls owner operation must pass readback.'

    $realIisAclRoot = Join-Path $ValidationRoot 'real-iis-acl'
    New-Item -ItemType Directory -Path $realIisAclRoot -Force | Out-Null
    Initialize-IisContentAcl -PublishPath $realIisAclRoot -SkipRoot
    $realIisAcl = Get-Acl -LiteralPath $realIisAclRoot
    Assert-True $realIisAcl.AreAccessRulesProtected 'Production IIS content ACL must pass real non-inheritance readback.'

    $statePath = Join-Path $ValidationRoot 'runtime.json'
    '{"schemaVersion":99}' | Set-Content -LiteralPath $statePath -Encoding utf8NoBOM
    Restore-PreviousPublicSiteRuntimeState -Contract $legacy -StatePath $statePath
    Assert-True (-not (Test-Path -LiteralPath $statePath)) 'State-missing rollback must remove state created by the failed candidate route.'
    $states = @(
        [pscustomobject]@{ schemaVersion=1; sitePid=31; ngrokPid=41 },
        [pscustomobject]@{ schemaVersion=2; ngrokPid=41 },
        $iisState
    )
    foreach ($savedState in $states) {
        # 模擬 rollback 已將舊 31/41 程序重啟為實際通過健康驗證的 131/141。
        $stateContract = [pscustomobject]@{ RuntimeStatePresent=$true; RuntimeState=$savedState; SiteProcessId=131; NgrokProcessId=141 }
        Restore-PreviousPublicSiteRuntimeState -Contract $stateContract -StatePath $statePath
        $restoredState = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
        Assert-Equal $savedState.schemaVersion $restoredState.schemaVersion "State-present rollback must atomically restore schema $($savedState.schemaVersion)."
        Assert-Equal 141 $restoredState.ngrokPid "Schema $($savedState.schemaVersion) must use the newly verified ngrok identity."
        if ($savedState.schemaVersion -eq 1) { Assert-Equal 131 $restoredState.sitePid 'Schema 1 must use the newly healthy legacy site identity.' }
        Assert-Equal 0 @(Get-ChildItem -LiteralPath $ValidationRoot -Filter 'runtime.json.*.tmp' -File).Count 'Atomic state restoration must not leave a temporary document.'
    }
    $restoredState = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    Assert-Equal $hash $restoredState.ngrokImageSha256 'Schema 3 rollback must preserve the verified image hash.'

    $installer = Get-Content -Raw -LiteralPath $InstallerPath
    $aclPosition = $installer.IndexOf('Initialize-ManagedScriptsAcl -ScriptsPath $managedScripts',[StringComparison]::Ordinal)
    $highestPosition = $installer.IndexOf('New-ScheduledTaskPrincipal',[StringComparison]::Ordinal)
    $registerPosition = $installer.IndexOf('Register-ScheduledTask -TaskName $taskName -Action',[StringComparison]::Ordinal)
    Assert-True ($aclPosition -ge 0 -and $aclPosition -lt $highestPosition -and $highestPosition -lt $registerPosition) 'Managed scripts ACL readback must precede creation and registration of the Highest task.'
    Assert-True (-not $installer.Contains('Stop-ProvenNgrok')) 'Rollback must not re-resolve a previous 8792 route through an IIS-only stop helper.'
    Assert-True $installer.Contains('Get-PreviousPublicSiteRouteContract -Paths $paths') 'The previous route contract must be captured before mutation.'
    Assert-True $installer.Contains('Stop-ProvenPreviousPublicSiteRoute -Contract $previousRoute') 'Transition stop must consume the saved route contract.'
    Assert-True $installer.Contains('Restore-PreviousPublicSiteRuntimeState -Contract $previousRoute') 'Rollback must restore the previous runtime state only after route health verification.'
    Assert-True ($installer.IndexOf('Restore-PreviousPublicSiteRoute -Contract $previousRoute',[StringComparison]::Ordinal) -lt $installer.IndexOf('Restore-PreviousPublicSiteRuntimeState -Contract $previousRoute',[StringComparison]::Ordinal)) 'Runtime state must be rebuilt only after the previous route restart succeeds.'

    Write-Output 'PASS: state-missing migration, exact route ownership, IIS readiness, every rollback boundary, restart order and ACL-before-Highest contracts.'
} finally {
    $realAclRootForCleanup = Join-Path $ValidationRoot 'real-acl'
    foreach ($aclRootForCleanup in @($realAclRootForCleanup,(Join-Path $ValidationRoot 'real-iis-acl'))) {
      if (Test-Path -LiteralPath $aclRootForCleanup -PathType Container) {
        $cleanupSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        & (Join-Path $env:SystemRoot 'System32\icacls.exe') $aclRootForCleanup '/grant:r' "*$cleanupSid`:(OI)(CI)(F)" | Out-Null
        & (Join-Path $env:SystemRoot 'System32\icacls.exe') $aclRootForCleanup '/inheritance:e' | Out-Null
      }
    }
    if (Test-Path -LiteralPath $ValidationRoot -PathType Container) { Remove-Item -LiteralPath $ValidationRoot -Recurse -Force }
}
