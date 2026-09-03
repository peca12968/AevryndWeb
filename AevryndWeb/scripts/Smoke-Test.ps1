$ErrorActionPreference = 'Stop'
$response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8792/health/ready' -Headers @{ Host = '127.0.0.1:8792' }
if ($response.StatusCode -ne 200) { throw 'Readiness endpoint failed.' }
$payload = $response.Content | ConvertFrom-Json
if ($payload.status -ne 'ok') { throw 'Readiness payload failed.' }
Write-Output 'AevryndWeb smoke test passed.'
