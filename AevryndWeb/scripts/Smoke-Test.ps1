$ErrorActionPreference = 'Stop'
$response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8792/health/ready' -Headers @{ Host = '127.0.0.1:8792' }
if ($response.StatusCode -ne 200) { throw 'Readiness endpoint failed.' }
$payload = $response.Content | ConvertFrom-Json
if ($payload.status -ne 'ok') { throw 'Readiness payload failed.' }
$assetChecks = @(
    @{ Path = '/css/site.css'; Marker = '--mint:#91e4b8' },
    @{ Path = '/lib/bootstrap/dist/css/bootstrap.min.css'; Marker = 'Bootstrap  v5.3.8' },
    @{ Path = '/lib/jquery/dist/jquery.min.js'; Marker = 'jQuery v4.0.0' },
    @{ Path = '/lib/sweetalert2/dist/sweetalert2.min.js'; Marker = 'sweetalert2 v11.26.25' }
)
foreach ($assetCheck in $assetChecks) {
    $asset = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8792$($assetCheck.Path)" -Headers @{ Host = '127.0.0.1:8792' }
    if ($asset.StatusCode -ne 200 -or -not $asset.Content.Contains($assetCheck.Marker, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Static asset verification failed: $($assetCheck.Path)"
    }
}
Write-Output 'AevryndWeb smoke test passed.'
