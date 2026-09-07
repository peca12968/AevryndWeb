const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../../wwwroot/history');
const data = JSON.parse(fs.readFileSync(path.join(root, 'archive.json'), 'utf8').replace(/^\uFEFF/, ''));
test('歷史版本與原圖完整，公開資料不含本機路徑', () => {
  assert.equal(data.frontier.length, 70); assert.equal(data.gameplay.length, 4);
  assert.equal(new Set(data.frontier.map(x => x.version)).size, 70);
  assert.doesNotMatch(JSON.stringify(data), /[CD]:\\/i);
  for (const r of data.gameplay) {
    assert.equal(r.images.length, 11);
    for (const m of r.images) {
      assert.match(m.url, /^images\/gameplay-[0-9.-]+\/[a-z-]+\.png$/);
      assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root, m.url))).digest('hex'), m.sha256);
    }
  }
});
test('版本展開與深連結，不把資料載入失敗顯示為零筆', async () => {
  const nodes = new Map();
  function element(tag) {
    return {tagName: tag.toUpperCase(), children: [], append(...items) { this.children.push(...items); }, scrollIntoView() {},
      set id(value) { nodes.set(value, this); }, get id() { return ''; }};
  }
  for (const id of ['status','gameplay','frontier']) nodes.set(id, element('section'));
  const context = {document: {createElement: element, getElementById: id => nodes.get(id)}, location: {hash:'#gameplay-1.2.0'}, window: {addEventListener() {}}, fetch: async () => ({ok:true,json:async()=>data})};
  vm.runInNewContext(fs.readFileSync(path.join(root,'archive.js'),'utf8'), context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(nodes.get('gameplay').children.length, 4);
  assert.equal(nodes.get('frontier').children.length, 70);
  assert.equal(nodes.get('gameplay-1.2.0').open, true);
  context.fetch = async () => ({ok:false});
  vm.runInNewContext(fs.readFileSync(path.join(root,'archive.js'),'utf8').replace("const make =", "var make ="), {...context});
  await new Promise(resolve => setImmediate(resolve));
  assert.match(nodes.get('status').textContent, /暫時無法載入/);
});
