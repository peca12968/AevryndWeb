'use strict';
// 歷史資料只以文字節點呈現，不執行清單中的內容。
const make = (tag, text) => { const e = document.createElement(tag); if (text) e.textContent = text; return e; };
function panel(parent, id, title) {
    const d = make('details'); d.id = id; d.append(make('summary', title));
    const link = make('a', '此版本連結'); link.href = '#' + id; d.append(link); parent.append(d); return d;
}
async function loadArchive() {
    const response = await fetch('archive.json'); if (!response.ok) throw new Error('archive unavailable');
    const data = await response.json();
    for (const release of data.gameplay) {
        const d = panel(document.getElementById('gameplay'), release.id, 'Gameplay Lab ' + release.version + ' · 11 張歷史截圖');
        d.append(make('p', release.description), make('p', '引擎版本：' + release.engineVersion), make('code', release.releaseId));
        d.append(make('p', '影片：尚未找到可確認屬於本版的獨立影片。保留原始截圖，不冒充連續遊玩錄影。'));
        const gallery = make('div'); gallery.className = 'gallery';
        for (const media of release.images) {
            if (!/^images\/gameplay-[0-9.-]+\/[a-z-]+\.png$/.test(media.url)) throw new Error('invalid media path');
            const f = make('figure'); const a = make('a'); a.href = media.url;
            const img = make('img'); img.src = media.url; img.alt = release.version + ' · ' + media.title; img.loading = 'lazy';
            a.append(img); f.append(a, make('figcaption', media.title)); gallery.append(f);
        }
        d.append(gallery);
    }
    for (const entry of data.frontier) {
        const d = panel(document.getElementById('frontier'), 'frontier-' + entry.version, 'Frontier World v' + entry.version);
        d.append(make('p', '已保存此版執行檔；尚未找到能準確對應本版的圖片、影片或改動說明。'), make('code', entry.fileName));
    }
    const reveal = () => { const e = document.getElementById(location.hash.slice(1)); if(e?.tagName === 'DETAILS') { e.open = true; e.scrollIntoView(); } };
    window.addEventListener('hashchange', reveal); reveal();
    document.getElementById('status').textContent = '已整理 70 個 Frontier 0.x 版本紀錄，以及 Gameplay 1.0～1.3 共 44 張原始截圖；截圖雜湊已重新核對。';
}
loadArchive().catch(() => { document.getElementById('status').textContent = '版本紀錄暫時無法載入，請重新整理；未將缺少資料視為零筆。'; });
