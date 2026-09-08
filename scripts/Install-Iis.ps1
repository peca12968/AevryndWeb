#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$SiteName = 'AevryndWeb',
    [int]$Port = 8081
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $repoRoot 'AevryndWeb\AevryndWeb.csproj'
$publishPath = Join-Path $repoRoot 'artifacts\iis'
$schemaPath = Join-Path $repoRoot 'Database\Schema.sql'
$refreshScript = Join-Path $PSScriptRoot 'Start-LocalSite.ps1'
$appCmd = Join-Path $env:windir 'System32\inetsrv\appcmd.exe'
$ownerSqlInstance = '(localdb)\MSSQLLocalDB'
$sqlLogin = 'AevryndWebIis'
$appPoolIdentity = "IIS APPPOOL\$SiteName"

if ($SiteName -notmatch '^[A-Za-z0-9._-]+$') { throw 'SiteName 只能包含英文字母、數字、句點、底線與連字號。' }
if ($Port -lt 1 -or $Port -gt 65535) { throw 'Port 必須介於 1 到 65535。' }
if (-not (Test-Path $appCmd)) { throw 'IIS 管理工具未安裝。' }
if (-not (Test-Path "$env:ProgramFiles\IIS\Asp.Net Core Module\V2\aspnetcorev2.dll")) {
    throw 'IIS 尚未安裝 ASP.NET Core Hosting Bundle。'
}

sqllocaldb start MSSQLLocalDB | Out-Null
$instanceInfo = sqllocaldb info MSSQLLocalDB
$pipeName = [regex]::Match(($instanceInfo -join "`n"), 'np:\\\\.\\pipe\\[^\r\n]+').Value.Trim()
if (-not $pipeName) { throw '無法取得 LocalDB 具名管道。' }

$siteExists = & $appCmd list site "/name:$SiteName"
if ($siteExists) {
    & $appCmd stop site "/site.name:$SiteName" | Out-Null
}

dotnet publish $projectPath -c Release -o $publishPath
if ($LASTEXITCODE -ne 0) { throw '網站發布失敗。' }

sqlcmd -S $ownerSqlInstance -E -b -i $schemaPath
if ($LASTEXITCODE -ne 0) { throw 'Aevrynd 資料庫結構建立失敗。' }

$databasePassword = [Convert]::ToBase64String(
    [System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)) + 'aA1!'
$loginSql = @"
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'$sqlLogin')
    CREATE LOGIN [$sqlLogin] WITH PASSWORD = N'$databasePassword';
ELSE
    ALTER LOGIN [$sqlLogin] WITH PASSWORD = N'$databasePassword';
USE [Aevrynd];
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'$sqlLogin')
    CREATE USER [$sqlLogin] FOR LOGIN [$sqlLogin];
ALTER ROLE db_datareader ADD MEMBER [$sqlLogin];
ALTER ROLE db_datawriter ADD MEMBER [$sqlLogin];
"@
sqlcmd -S $ownerSqlInstance -E -b -Q $loginSql
if ($LASTEXITCODE -ne 0) { throw 'IIS 資料庫帳號建立失敗。' }

$connectionString = "Server=$pipeName;Database=Aevrynd;User ID=$sqlLogin;Password=$databasePassword;Encrypt=false"
@{ ConnectionStrings = @{ Aevrynd = $connectionString } } |
    ConvertTo-Json -Depth 3 |
    Set-Content -LiteralPath (Join-Path $publishPath 'appsettings.Production.json') -Encoding utf8

$poolExists = & $appCmd list apppool "/name:$SiteName"
if (-not $poolExists) {
    & $appCmd add apppool "/name:$SiteName"
}
& $appCmd set apppool "/apppool.name:$SiteName" /managedRuntimeVersion:"" /managedPipelineMode:Integrated /processModel.identityType:ApplicationPoolIdentity /processModel.loadUserProfile:true

if (-not $siteExists) {
    & $appCmd add site "/name:$SiteName" "/bindings:http/*:${Port}:" "/physicalPath:$publishPath"
} else {
    & $appCmd set vdir "$SiteName/" "/physicalPath:$publishPath"
    & $appCmd set site "/site.name:$SiteName" "/bindings:http/*:${Port}:"
}
& $appCmd set app "$SiteName/" "/applicationPool:$SiteName"
& icacls $publishPath /grant "${appPoolIdentity}:(OI)(CI)RX" /T /C | Out-Null

$startupDirectory = [Environment]::GetFolderPath('Startup')
$startupCommand = Join-Path $startupDirectory 'AevryndWeb-LocalDB.cmd'
$pwsh = Join-Path $PSHOME 'pwsh.exe'
"@echo off`r`nstart `"`" /min `"$pwsh`" -NoProfile -ExecutionPolicy Bypass -File `"$refreshScript`"`r`n" |
    Set-Content -LiteralPath $startupCommand -Encoding ascii

& $appCmd start site "/site.name:$SiteName"
Write-Host "AevryndWeb 已安裝：http://localhost:$Port/"
