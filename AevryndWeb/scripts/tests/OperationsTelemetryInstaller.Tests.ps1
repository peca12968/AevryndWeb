#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$InstallerPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'Install-OperationsTelemetry.ps1')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-FileState([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return 'absent' }
    $item = Get-Item -LiteralPath $Path -Force
    return "$($item.Length):$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash)"
}

function Get-TaskState([string]$TaskName) {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($null -eq $task) { return 'absent' }
        $xml = Export-ScheduledTask -TaskName $TaskName
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($xml)))
    } catch { return "unavailable:$($_.Exception.GetType().Name)" }
}

function Test-KeyExists([string]$KeyName) {
    return [Security.Cryptography.CngKey]::Exists(
        $KeyName,
        [Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider,
        [Security.Cryptography.CngKeyOpenOptions]::UserKey)
}

function Get-ExecutableProcessCount([string]$ExecutablePath) {
    $canonical = [IO.Path]::GetFullPath($ExecutablePath)
    return @(
        Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ExecutablePath -and [IO.Path]::GetFullPath($_.ExecutablePath) -ceq $canonical }
    ).Count
}

function Get-TrimmedText([object]$Value) {
    if ($null -eq $Value) { return '' }
    return ([string]$Value).Trim()
}

function Invoke-InstallerCase([string]$Name, [string[]]$Arguments, [string]$OutputRoot) {
    $stdoutPath = Join-Path $OutputRoot "$Name.stdout.txt"
    $stderrPath = Join-Path $OutputRoot "$Name.stderr.txt"
    $hostPwsh = Join-Path $PSHOME 'pwsh.exe'
    & $hostPwsh -NoLogo -NoProfile -NonInteractive -File $InstallerPath @Arguments 1> $stdoutPath 2> $stderrPath
    return [pscustomobject]@{
        Name = $Name
        ExitCode = $LASTEXITCODE
        Stdout = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { '' }
        Stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { '' }
    }
}

if (-not (Test-Path -LiteralPath $InstallerPath -PathType Leaf)) { throw 'Installer test input is missing.' }
$publisherPath = Join-Path (Split-Path -Parent $InstallerPath) 'Publish-OperationsTelemetry.ps1'
if (-not (Test-Path -LiteralPath $publisherPath -PathType Leaf)) { throw 'Publisher test input is missing.' }

$testRoot = Join-Path ([IO.Path]::GetTempPath()) ("AevryndTelemetryInstallerTests-" + [Guid]::NewGuid().ToString('N'))
$alternateRoot = Join-Path $testRoot 'alternate-runtime'
$alternatePwsh = Join-Path $alternateRoot 'pwsh.exe'
$wrongExecutable = Join-Path $alternateRoot 'not-pwsh.exe'
$wrongRuntimeRoot = Join-Path $testRoot 'wrong-runtime'
$wrongRuntime = Join-Path $wrongRuntimeRoot 'pwsh.exe'
$programDataRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'Aevrynd\OperationsTelemetry'
$settingsPath = Join-Path $programDataRoot 'taoyuan-settings.json'
$enrollmentPath = Join-Path $programDataRoot 'taoyuan-enrollment.json'
$taskName = 'Aevrynd Operations Telemetry (taoyuan)'
$keyName = 'Aevrynd-TelemetryTest-' + [Guid]::NewGuid().ToString('N')
$publisherHash = (Get-FileHash -LiteralPath $publisherPath -Algorithm SHA256).Hash.ToLowerInvariant()

try {
    New-Item -ItemType Directory -Path $alternateRoot | Out-Null
    New-Item -ItemType Directory -Path $wrongRuntimeRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSHOME 'pwsh.exe') -Destination $alternatePwsh
    Copy-Item -LiteralPath (Join-Path $PSHOME 'pwsh.exe') -Destination $wrongExecutable
    Copy-Item -LiteralPath (Join-Path ([Environment]::SystemDirectory) 'WindowsPowerShell\v1.0\powershell.exe') -Destination $wrongRuntime

    $before = [ordered]@{
        Settings = Get-FileState $settingsPath
        Enrollment = Get-FileState $enrollmentPath
        Task = Get-TaskState $taskName
        KeyExists = Test-KeyExists $keyName
        AlternateProcesses = Get-ExecutableProcessCount $alternatePwsh
    }

    $common = @('-NodeId','taoyuan','-KeyName',$keyName,'-EnrollOnly','-ExpectedPublisherSha256',$publisherHash,'-WhatIf')
    $alternate = Invoke-InstallerCase 'alternate-trusted-path' ($common + @('-PowerShellPath',$alternatePwsh)) $testRoot
    $missing = Invoke-InstallerCase 'missing-executable' ($common + @('-PowerShellPath',(Join-Path $alternateRoot 'missing\pwsh.exe'))) $testRoot
    $wrong = Invoke-InstallerCase 'wrong-executable' ($common + @('-PowerShellPath',$wrongExecutable)) $testRoot
    $wrongProduct = Invoke-InstallerCase 'wrong-powershell-product' ($common + @('-PowerShellPath',$wrongRuntime)) $testRoot
    $mismatch = Invoke-InstallerCase 'publisher-hash-mismatch' (@('-NodeId','taoyuan','-KeyName',$keyName,'-EnrollOnly','-ExpectedPublisherSha256',('0' * 64),'-PowerShellPath',$alternatePwsh,'-WhatIf')) $testRoot

    $after = [ordered]@{
        Settings = Get-FileState $settingsPath
        Enrollment = Get-FileState $enrollmentPath
        Task = Get-TaskState $taskName
        KeyExists = Test-KeyExists $keyName
        AlternateProcesses = Get-ExecutableProcessCount $alternatePwsh
    }

    $results = [ordered]@{
        AlternateTrustedPath = $alternate.ExitCode -eq 0 -and $alternate.Stdout -match '^What if:'
        MissingExecutableRejected = $missing.ExitCode -ne 0
        WrongExecutableRejected = $wrong.ExitCode -ne 0
        WrongPowerShellProductRejected = $wrongProduct.ExitCode -ne 0
        PublisherHashMismatchRejected = $mismatch.ExitCode -ne 0
        WhatIfZeroMutation = ($before | ConvertTo-Json -Compress) -ceq ($after | ConvertTo-Json -Compress)
    }
    $failed = @($results.GetEnumerator() | Where-Object { -not $_.Value })
    [pscustomobject]@{
        SchemaVersion = 1
        Results = $results
        ExitCodes = [ordered]@{
            AlternateTrustedPath = $alternate.ExitCode
            MissingExecutable = $missing.ExitCode
            WrongExecutable = $wrong.ExitCode
            WrongPowerShellProduct = $wrongProduct.ExitCode
            PublisherHashMismatch = $mismatch.ExitCode
        }
        ErrorSummaries = [ordered]@{
            AlternateTrustedPath = Get-TrimmedText $alternate.Stderr
            MissingExecutable = Get-TrimmedText $missing.Stderr
            WrongExecutable = Get-TrimmedText $wrong.Stderr
            WrongPowerShellProduct = Get-TrimmedText $wrongProduct.Stderr
            PublisherHashMismatch = Get-TrimmedText $mismatch.Stderr
        }
        WhatIfStateBefore = $before
        WhatIfStateAfter = $after
    } | ConvertTo-Json -Depth 5
    if ($failed.Count -gt 0) { exit 1 }
    exit 0
} finally {
    if (Test-Path -LiteralPath $testRoot -PathType Container) {
        $resolved = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $testRoot).ProviderPath)
        $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
        if (-not $resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup path escaped the temporary directory.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
