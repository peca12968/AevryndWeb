# 以系統管理員執行，建立可回溯的本機 IIS 平行站台。
[CmdletBinding()]
param(
    [string]$SiteName = 'AevryndWeb-IIS',
    [string]$AppPoolName = 'AevryndWeb-IIS',
    [int]$Port = 8080,
    [string]$PhysicalPath = 'C:\ProgramData\AevryndWeb\publish'
)
$ErrorActionPreference = 'Stop'
trap { $_ | Out-File -FilePath 'C:\ProgramData\AevryndWeb\iis-config-error.log' -Encoding utf8; exit 1 }
Import-Module WebAdministration
if (-not (Test-Path -LiteralPath $PhysicalPath)) { throw "Published site path not found: $PhysicalPath" }
& icacls.exe $PhysicalPath /grant 'IIS_IUSRS:(OI)(CI)(RX)' /T /C | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Unable to grant IIS read access to published site." }
if (-not (Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue)) {
    New-WebAppPool -Name $AppPoolName | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name managedRuntimeVersion -Value ''
Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
if (-not (Get-Website -Name $SiteName -ErrorAction SilentlyContinue)) {
    New-Website -Name $SiteName -Port $Port -IPAddress '127.0.0.1' -HostHeader '' -PhysicalPath $PhysicalPath -ApplicationPool $AppPoolName | Out-Null
} else {
    Set-ItemProperty "IIS:\Sites\$SiteName" -Name physicalPath -Value $PhysicalPath
    Set-ItemProperty "IIS:\Sites\$SiteName" -Name applicationPool -Value $AppPoolName
    Set-ItemProperty "IIS:\Sites\$SiteName" -Name bindings -Value @{ protocol = 'http'; bindingInformation = "127.0.0.1:${Port}:" }
}
Start-WebAppPool -Name $AppPoolName
Start-Website -Name $SiteName
$response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health/ready" -TimeoutSec 15
if ($response.StatusCode -ne 200) { throw "IIS health check returned $($response.StatusCode)." }
Write-Output "IIS site '$SiteName' is healthy at http://127.0.0.1:$Port/health/ready"
