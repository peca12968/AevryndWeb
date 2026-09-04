$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env:ASPNETCORE_ENVIRONMENT = 'Production'
dotnet run --project (Join-Path $root 'AevryndWeb.csproj') --no-launch-profile --urls 'http://127.0.0.1:8081'
