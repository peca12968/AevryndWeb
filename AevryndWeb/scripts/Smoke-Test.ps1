[CmdletBinding()]
param([ValidatePattern('^http://127\.0\.0\.1:\d{2,5}$')][string]$BaseUri = 'http://127.0.0.1:8080')
$ErrorActionPreference = 'Stop'
$authority = ([Uri]$BaseUri).Authority
$hostContract = if (([Uri]$BaseUri).Port -eq 8080) { 'sample-cupid-overdrawn.ngrok-free.dev' } else { $authority }
$response = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUri/health/ready" -Headers @{ Host = $hostContract }
if ($response.StatusCode -ne 200) { throw 'Readiness endpoint failed.' }
$payload = $response.Content | ConvertFrom-Json
if ($payload.status -ne 'ok') { throw 'Readiness payload failed.' }
$assetChecks = @(
    @{ Path = '/css/site.css'; Marker = '--mint:#91e4b8' },
    @{ Path = '/js/site.js'; Marker = 'data-operations-root' },
    @{ Path = '/lib/datatables/datatables.min.js'; Marker = 'DataTables 3.0.3' },
    @{ Path = '/lib/datatables/datatables.min.css'; Marker = '--dt_background-selected' },
    @{ Path = '/lib/datatables/package.core.json'; Marker = '"version": "3.0.3"' },
    @{ Path = '/lib/bootstrap/dist/css/bootstrap.min.css'; Marker = 'Bootstrap  v5.3.8' },
    @{ Path = '/lib/jquery/dist/jquery.min.js'; Marker = 'jQuery v4.0.0' },
    @{ Path = '/lib/sweetalert2/dist/sweetalert2.min.js'; Marker = 'sweetalert2 v11.26.25' }
)
foreach ($assetCheck in $assetChecks) {
    $asset = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUri$($assetCheck.Path)" -Headers @{ Host = $hostContract }
    if ($asset.StatusCode -ne 200 -or -not $asset.Content.Contains($assetCheck.Marker, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Static asset verification failed: $($assetCheck.Path)"
    }
}
$dataTablesLicense = Join-Path (Split-Path -Parent $PSScriptRoot) 'wwwroot\lib\datatables\LICENSE.core.txt'
if (-not (Test-Path -LiteralPath $dataTablesLicense -PathType Leaf) -or -not (Get-Content -Raw -LiteralPath $dataTablesLicense).Contains('MIT License')) { throw 'DataTables MIT license metadata is missing.' }
Write-Output 'AevryndWeb smoke test passed.'
