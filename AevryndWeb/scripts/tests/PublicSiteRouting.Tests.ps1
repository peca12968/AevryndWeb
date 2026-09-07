[CmdletBinding()]
param(
    [string]$CommonPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'PublicSite.Common.ps1'),
    [switch]$SkipTransaction
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

$wrapper = 'C:\Users\USER\AppData\Local\Microsoft\WindowsApps\ngrok.exe'
$website = "`"$wrapper`" http http://127.0.0.1:8080 --domain=$script:PublicSiteDomain --scheme=https --inspect=false --log=false"
$wrongOrigin = "`"$wrapper`" http http://127.0.0.1:8787 --domain=$script:PublicSiteDomain --scheme=https --inspect=false --log=false"
$line = "`"$wrapper`" http http://127.0.0.1:8787 --domain=line-gateway.example.invalid --scheme=https --inspect=false --log=false"
$substring = "`"$wrapper`" http http://127.0.0.1:8787 --domain=prefix-$script:PublicSiteDomain --scheme=https --inspect=false --log=false"

Assert-True (Test-PublicSiteDomainClaim -CommandLine $website) 'The exact website domain must be detected.'
Assert-True (Test-PublicSiteDomainClaim -CommandLine $wrongOrigin) 'A wrong-origin process claiming the website domain must be detected as a conflict.'
Assert-True (-not (Test-PublicSiteDomainClaim -CommandLine $line)) 'An unrelated LINE tunnel must be allowed to coexist.'
Assert-True (-not (Test-PublicSiteDomainClaim -CommandLine $substring)) 'A domain substring must not claim the website domain.'

$processes = @(
    [pscustomobject]@{ Name='ngrok.exe'; ProcessId=10; CommandLine=$line },
    [pscustomobject]@{ Name='ngrok.exe'; ProcessId=11; CommandLine=$wrongOrigin },
    [pscustomobject]@{ Name='other.exe'; ProcessId=12; CommandLine=$website }
)
$claims = @(Get-PublicSiteDomainProcesses -Processes $processes)
Assert-Equal 1 $claims.Count 'Only ngrok.exe with the exact fixed domain may enter the ownership decision.'
Assert-Equal 11 $claims[0].ProcessId 'The wrong-origin claimant must remain visible for fail-closed handling.'

$stateProcess = [pscustomobject]@{ ProcessId=20 }
$startFromState = Resolve-PublicSiteStartProcess -RuntimeState ([pscustomobject]@{ ngrokPid=20 }) -DomainProcesses @() `
    -VerifyStateProcess { $stateProcess } -VerifyDomainProcess { throw 'must not inspect claim' } -StartProcess { throw 'must not start' }
Assert-Equal 'state' $startFromState.Source 'Start must reuse a verified runtime-state process.'
$startFromClaim = Resolve-PublicSiteStartProcess -RuntimeState $null -DomainProcesses @([pscustomobject]@{ ProcessId=21 }) `
    -VerifyStateProcess { throw 'must not inspect state' } -VerifyDomainProcess { [pscustomobject]@{ ProcessId=21 } } -StartProcess { throw 'must not start' }
Assert-Equal 'claim' $startFromClaim.Source 'Start must reuse one exact 8080 domain claimant.'
$startNew = Resolve-PublicSiteStartProcess -RuntimeState $null -DomainProcesses @() `
    -VerifyStateProcess { throw 'must not inspect state' } -VerifyDomainProcess { throw 'must not inspect claim' } -StartProcess { [pscustomobject]@{ Id=22 } }
Assert-True $startNew.Launched 'Start must identify a newly launched process for failure cleanup.'
try {
    Resolve-PublicSiteStartProcess -RuntimeState $null -DomainProcesses @([pscustomobject]@{ProcessId=1},[pscustomobject]@{ProcessId=2}) `
        -VerifyStateProcess { $null } -VerifyDomainProcess { $null } -StartProcess { $null }
    throw 'ASSERT_START_MULTIPLE_FAILED'
} catch { if ($_.Exception.Message -eq 'ASSERT_START_MULTIPLE_FAILED') { throw } }

$stopFromState = Resolve-PublicSiteStopProcess -RuntimeState ([pscustomobject]@{ ngrokPid=20 }) -DomainProcesses @() -VerifyStateProcess { $stateProcess } -VerifyDomainProcess { throw 'must not inspect claim' }
Assert-Equal 20 $stopFromState.ProcessId 'Stop must prefer exact verified runtime-state ownership.'
$stopNone = Resolve-PublicSiteStopProcess -RuntimeState $null -DomainProcesses @() -VerifyStateProcess { throw 'must not inspect state' } -VerifyDomainProcess { throw 'must not inspect claim' }
Assert-True ($null -eq $stopNone) 'Stop with no state and no claimant must be an idempotent no-op.'
try {
    Resolve-PublicSiteStopProcess -RuntimeState ([pscustomobject]@{ ngrokPid=99 }) -DomainProcesses @() -VerifyStateProcess { $null } -VerifyDomainProcess { $null }
    throw 'ASSERT_STOP_MISMATCH_FAILED'
} catch { if ($_.Exception.Message -eq 'ASSERT_STOP_MISMATCH_FAILED') { throw } }

$installer = Get-Content -Raw -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'Install-PublicSite.ps1')
$startScript = Get-Content -Raw -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'Start-PublicSite.ps1')
$stopScript = Get-Content -Raw -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'Stop-PublicSite.ps1')
$commonScript = Get-Content -Raw -LiteralPath $CommonPath
Assert-True $installer.Contains('-WindowStyle Hidden') 'The scheduled action must not open a PowerShell window.'
Assert-True $installer.Contains('-RunLevel Highest') 'The scheduled action must be able to read IIS configuration for ownership proof.'
Assert-True $installer.Contains('Install-ProductionSecrets') 'IIS deployment must provision the Gmail readiness secret without weakening health checks.'
Assert-True $installer.Contains("AppPassword = `$gmailPassword") 'The production configuration must receive the validated Gmail credential.'
Assert-True $installer.Contains('Initialize-IisContentAcl -PublishPath $temporaryPublish -SkipRoot') 'Production secrets must receive the restrictive publish ACL before the live swap.'
Assert-True $installer.Contains('Get-PreviousPublicSiteRouteContract -Paths $paths') 'Deployment must preserve an exact previous-route contract before service mutation.'
Assert-True $installer.Contains('Stop-ProvenPreviousPublicSiteRoute -Contract $previousRoute') 'Transition stop must consume the previously verified route contract.'
Assert-True $installer.Contains('Invoke-PublicSiteRollbackTransaction') 'Rollback must use the ordered transaction contract.'
Assert-True (-not $installer.Contains('Stop-ProvenNgrok')) 'Rollback must not reinterpret a saved 8792 route through an IIS-only resolver.'
Assert-True $installer.Contains('Initialize-ManagedScriptsAcl -ScriptsPath $managedScripts') 'Elevated scheduled scripts must have a verified non-inheriting ACL.'
Assert-True $startScript.Contains('Resolve-PublicSiteStartProcess') 'Production Start must use the tested state/claim/new branch resolver.'
Assert-True $stopScript.Contains('Resolve-PublicSiteStopProcess') 'Production Stop must use the tested state/claim/no-route branch resolver.'
Assert-True $startScript.Contains('if ($resolution.Launched)') 'Production Start must clean only a tunnel launched by the failing invocation.'
Assert-True (($commonScript.Split('CreateNoWindow = true').Count - 1) -ge 2) 'Both legacy dotnet and ngrok rollback launches must be hidden.'

Write-Output 'PASS: public-site domain isolation, wrong-origin conflict detection, hidden startup and IIS ownership privilege contracts.'
if (-not $SkipTransaction) {
    & (Join-Path $PSScriptRoot 'PublicSiteDeploymentTransaction.Tests.ps1') -CommonPath $CommonPath
    if ($LASTEXITCODE -notin @(0,$null)) { throw "Public-site deployment transaction runner failed with exit $LASTEXITCODE." }
}
