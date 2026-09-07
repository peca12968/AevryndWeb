param([Parameter(Mandatory)][string]$InventoryPath)
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -LiteralPath $InventoryPath -Raw | ConvertFrom-Json
$destination = Join-Path $PSScriptRoot '../wwwroot/history'
$descriptions = @(
    '保存的 Gameplay Lab 原型：多視角、近戰及物件選單。不是全專案最早原型。',
    '碰撞穩定性、物件抓取與角色材質整合；Frontier Ultra 當時仍為獨立展示。',
    'Ultra 開放世界整入 Gameplay，包含日夜、多視角、物件選單、抓取及近戰；角色與動畫仍為原型。',
    '環境碰撞串流、半解析度體積大氣、雲層與定向光束。碰撞仍為保守方盒，大氣仍為螢幕空間效果；歷史畫質不代表目前目標。'
)
$titles = @{'first-day'='第一人稱 · 日間';'first-dusk'='第一人稱 · 黃昏';'first-night'='第一人稱 · 夜間';'third-day'='第三人稱 · 日間';'third-dusk'='第三人稱 · 黃昏';'third-night'='第三人稱 · 夜間';'god-day'='上帝視角 · 日間';'god-dusk'='上帝視角 · 黃昏';'god-night'='上帝視角 · 夜間';'melee-combat'='近戰';'palette-building'='物件選單與建造'}
$releases = @(); $index = 0
foreach ($release in $inventory.gameplayReleases) {
    if ($release.releaseId -notmatch '^v(1\.[0-3]\.0)-engine-v2\.86\.0-[a-f0-9]+$') { throw '非預期版本' }
    $version = $Matches[1]; $id = 'gameplay-' + $version
    $folder = Join-Path $destination ('images/' + $id)
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    $images = @()
    foreach ($capture in $release.captures) {
        if ([IO.Path]::GetExtension($capture.path) -ne '.png') { continue }
        if (-not $capture.hashVerified -or (Get-FileHash -LiteralPath $capture.path -Algorithm SHA256).Hash -ne $capture.sha256) { throw '歷史截圖雜湊不符' }
        $name = [IO.Path]::GetFileName($capture.path); $stem = [IO.Path]::GetFileNameWithoutExtension($name)
        if (-not $titles.ContainsKey($stem)) { throw '未知截圖名稱' }
        Copy-Item -LiteralPath $capture.path -Destination (Join-Path $folder $name)
        $images += @{url="images/$id/$name";title=$titles[$stem];sha256=$capture.sha256}
    }
    if ($images.Count -ne 11) { throw '截圖數量不符' }
    $releases += @{id=$id;version=$version;releaseId=$release.releaseId;engineVersion=$release.engineVersion;description=$descriptions[$index];images=$images}; $index++
}
if ($releases.Count -ne 4 -or $inventory.frontier.Count -ne 70) { throw '版本數量不符' }
$frontier = @($inventory.frontier | ForEach-Object { @{version=$_.version;fileName=[IO.Path]::GetFileName($_.path)} })
# 公開輸出僅保留版本與媒體，不洩漏本機路徑或原始測試收據。
@{schemaVersion=1;historicalOnly=$true;gameplay=$releases;frontier=$frontier} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $destination 'archive.json') -Encoding utf8
Write-Output 'HISTORY_EXPORT_OK; RELEASES=4; IMAGES=44; FRONTIER=70'
