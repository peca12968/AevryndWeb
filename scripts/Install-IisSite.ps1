# 以系統管理員執行，將網站部署到獨立 IIS 版本目錄，避免鎖住 Kestrel 發布目錄。
[CmdletBinding()]
param(
    [string]$SiteName = 'AevryndWeb-IIS',
    [string]$AppPoolName = 'AevryndWeb-IIS',
    [int]$Port = 8080,
    [string]$ReleaseRoot = 'C:\ProgramData\AevryndWeb\iis-releases'
)
$ErrorActionPreference = 'Stop'
$errorLog = 'C:\ProgramData\AevryndWeb\iis-deploy-error.log'
trap { $_ | Out-File -FilePath $errorLog -Encoding utf8; exit 1 }

Import-Module WebAdministration
$repoRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $repoRoot 'AevryndWeb\AevryndWeb.csproj'
$temporaryRoot = Join-Path $env:TEMP ("AevryndWeb-iis-" + [Guid]::NewGuid().ToString('N'))
$temporaryPublish = Join-Path $temporaryRoot 'publish'
$releasePath = Join-Path $ReleaseRoot ((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N'))
$previousPath = $null
$siteWasCreated = $false
$switched = $false
$sharedKestrelPublish = Join-Path $env:ProgramData 'AevryndWeb\publish'

function Test-PublishPayload {
    param([Parameter(Mandatory)][string]$Path)
    foreach ($relativePath in @(
        'AevryndWeb.dll',
        'web.config',
        'wwwroot\css\site.css',
        'wwwroot\js\site.js',
        'wwwroot\lib\bootstrap\dist\css\bootstrap.min.css',
        'wwwroot\lib\jquery\dist\jquery.min.js',
        'wwwroot\lib\sweetalert2\dist\sweetalert2.min.js'
    )) {
        $item = Get-Item -LiteralPath (Join-Path $Path $relativePath) -ErrorAction SilentlyContinue
        if ($null -eq $item -or $item.PSIsContainer -or $item.Length -le 0) { throw "Published payload is incomplete: $relativePath" }
    }
}

function Stop-IisRuntime {
    $pool = Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue
    if ($null -ne $pool -and $pool.Value -eq 'Started') { Stop-WebAppPool -Name $AppPoolName }
    $site = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
    if ($null -ne $site -and $site.State -eq 'Started') { Stop-Website -Name $SiteName }
}

function Start-IisRuntime {
    $pool = Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue
    if ($null -eq $pool -or $pool.Value -ne 'Started') { Start-WebAppPool -Name $AppPoolName }
    $site = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
    if ($null -eq $site -or $site.State -ne 'Started') { Start-Website -Name $SiteName }
}

function Test-IisHealth {
    param([int]$CheckPort)
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$CheckPort/health/ready" -TimeoutSec 15
    if ($response.StatusCode -ne 200) { throw "IIS health check returned $($response.StatusCode)." }
    $payload = $response.Content | ConvertFrom-Json
    if ($payload.status -ne 'ok') { throw 'IIS health payload is not ready.' }
}

try {
    if (-not (Test-Path -LiteralPath $project -PathType Leaf)) { throw "Project file not found: $project" }
    New-Item -ItemType Directory -Path $ReleaseRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    dotnet publish $project -c Release -o $temporaryPublish --nologo
    if ($LASTEXITCODE -ne 0) { throw 'IIS Release publish failed.' }
    Test-PublishPayload -Path $temporaryPublish
    New-Item -ItemType Directory -Path $releasePath -Force | Out-Null
    Get-ChildItem -LiteralPath $temporaryPublish -Force | Copy-Item -Destination $releasePath -Recurse -Force
    & icacls.exe $releasePath /grant 'IIS_IUSRS:(OI)(CI)(RX)' /T /C | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Unable to grant IIS read access to the release.' }

    $existingSite = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
    if ($null -ne $existingSite) { $previousPath = $existingSite.PhysicalPath }
    if (-not (Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue)) { New-WebAppPool -Name $AppPoolName | Out-Null }
    Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name managedRuntimeVersion -Value ''
    Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
    Stop-IisRuntime
    if ($null -eq $existingSite) {
        New-Website -Name $SiteName -Port $Port -IPAddress '127.0.0.1' -HostHeader '' -PhysicalPath $releasePath -ApplicationPool $AppPoolName | Out-Null
        $siteWasCreated = $true
    } else {
        Set-ItemProperty "IIS:\Sites\$SiteName" -Name physicalPath -Value $releasePath
        Set-ItemProperty "IIS:\Sites\$SiteName" -Name applicationPool -Value $AppPoolName
        Set-ItemProperty "IIS:\Sites\$SiteName" -Name bindings -Value @{ protocol = 'http'; bindingInformation = "127.0.0.1:${Port}:" }
    }
    Start-IisRuntime
    $switched = $true
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try { Test-IisHealth -CheckPort $Port; break } catch { if ($attempt -eq 29) { throw }; Start-Sleep -Milliseconds 500 }
    }
    Remove-Item -LiteralPath $errorLog -Force -ErrorAction SilentlyContinue
    Write-Output "IIS site '$SiteName' deployed to independent release '$releasePath' and is healthy at http://127.0.0.1:$Port/health/ready"
} catch {
    $deploymentError = $_
    try {
        Stop-IisRuntime
        if ($null -ne $previousPath -and
            $previousPath -cne $sharedKestrelPublish -and
            (Test-Path -LiteralPath $previousPath -PathType Container)) {
            Set-ItemProperty "IIS:\Sites\$SiteName" -Name physicalPath -Value $previousPath
            Start-IisRuntime
            Test-IisHealth -CheckPort $Port
        } elseif ($siteWasCreated) {
            # 新站台尚無可回復版本時保持停止，避免暴露未驗證版本。
            Stop-IisRuntime
        }
    } catch { throw "IIS deployment failed and rollback could not be verified. Deployment: $($deploymentError.Exception.Message) Rollback: $($_.Exception.Message)" }
    throw $deploymentError
} finally {
    if (Test-Path -LiteralPath $temporaryRoot -PathType Container) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
