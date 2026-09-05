$ErrorActionPreference = 'Stop'
$publisher = Join-Path (Split-Path -Parent $PSScriptRoot) 'Publish-LocalWork.ps1'
$root = Join-Path ([IO.Path]::GetTempPath()) ('aevrynd-local-work-test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $root
$start = [DateTimeOffset]::UtcNow.AddMinutes(-1)
# 使用隔離目錄驗證，不覆寫正式工作來源。
& $publisher -Task 'LOCAL-TEST-01' -Status working -StartedUtc $start -Phase 'Validating current source' -StateDirectory $root
$first = Get-Content -LiteralPath (Join-Path $root 'status.json') -Raw | ConvertFrom-Json
if ($first.status -ne 'working' -or [DateTimeOffset]$first.startedUtc -ne $start) { throw 'Start failed' }
& $publisher -Task 'LOCAL-TEST-01' -Status working -StartedUtc $start -Phase 'Running checks' -StateDirectory $root
$second = Get-Content -LiteralPath (Join-Path $root 'status.json') -Raw | ConvertFrom-Json
if ([DateTimeOffset]$second.startedUtc -ne $start) { throw 'Refresh changed start' }
$end = [DateTimeOffset]::UtcNow.AddSeconds(-1)
& $publisher -Task 'LOCAL-TEST-01' -Status completed -StartedUtc $start -EndedUtc $end -EvidenceSummary 'Native checks passed' -StateDirectory $root
& $publisher -Task 'LOCAL-TEST-01' -Status completed -StartedUtc $start -EndedUtc $end -EvidenceSummary 'Native checks passed' -StateDirectory $root
$history = Get-Content -LiteralPath (Join-Path $root 'operations-history.json') -Raw | ConvertFrom-Json
if (@($history.events).Count -ne 1 -or $history.events[0].status -ne 'completed' -or [DateTimeOffset]$history.events[0].endedAt -ne $end) { throw 'Terminal history mismatch' }
$rejected = 0
try { & $publisher -Task 'LOCAL-TEST-01' -Status working -StartedUtc $start -StateDirectory $root } catch { $rejected++ }
try { & $publisher -Task 'LOCAL-FUTURE' -Status working -StartedUtc ([DateTimeOffset]::UtcNow.AddHours(1)) -StateDirectory $root } catch { $rejected++ }
try { & $publisher -Task 'LOCAL-UNSAFE' -Status working -StartedUtc $start -Phase 'https://example.com' -StateDirectory $root } catch { $rejected++ }
try { & $publisher -Task 'LOCAL-END-ORDER' -Status failed -StartedUtc $start -EndedUtc $start.AddSeconds(-1) -StateDirectory $root } catch { $rejected++ }
if ($rejected -ne 4) { throw "Expected four rejects, saw $rejected" }
Write-Output "PASS active-start refresh terminal-idempotency four-negative-cases $root"
