import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { loadGeometry } from './load-character.mjs';
import { CharacterContactGuard, inspectBodyContact, inspectLayerIntersections, applyGuardedMorph } from '../src/character-contact.js';

const path = process.argv[2] ?? new URL('../public/assets/character-female-refined.glb', import.meta.url);
const gltf = await loadGeometry(await readFile(path));
const root = gltf.scene;
const start = performance.now();
const contact = inspectBodyContact(root, ['inner', 'pants', 'jacket', 'scalp', 'hair', 'flyaways']);
console.log('STATIC_CONTACT', contact, 'milliseconds', Math.round(performance.now() - start));
const intersections = inspectLayerIntersections(root);
console.log('LAYER_INTERSECTIONS', intersections);
const guard = new CharacterContactGuard(root);
console.log('NEUTRAL_HEAD_CLEAR', guard.isClear(), 'anchors', guard.anchors.length);
assert.equal(contact.inside, 0, '身體接觸取樣仍有穿模');
assert(intersections.every(pair => pair.intersections === 0), '身體／服裝／頭髮之間仍有三角面相交');
assert(guard.isClear(), '中性臉型與頭髮仍相交');
const keys = ['jawWidth', 'chinLength', 'noseWidth', 'mouthWidth', 'lipThickness'];
let clear = 0, limited = 0;
for (let mask = 0; mask < 32; mask++) {
  root.traverse(node => {
    if (!node.morphTargetDictionary) return;
    node.morphTargetInfluences.fill(0);
    keys.forEach((key, index) => {
      const name = key + ((mask >> index) & 1 ? '_maximum' : '_minimum');
      node.morphTargetInfluences[node.morphTargetDictionary[name]] = 1;
    });
  });
  if (guard.isClear()) clear++; else limited++;
}
root.traverse(node => { node.morphTargetInfluences?.fill(0); });
assert(guard.isClear(), '還原後仍有接觸');
let adjustments = 0, clamped = 0, worstAdjustmentMs = 0;
for (let mask = 0; mask < 32; mask++) {
  for (let index = 0; index < keys.length; index++) {
    const start = performance.now();
    const result = applyGuardedMorph(root, guard, keys[index], (mask >> index) & 1 ? 100 : -100);
    worstAdjustmentMs = Math.max(worstAdjustmentMs, performance.now() - start);
    assert(guard.isClear(), '已接受的滑桿狀態仍有穿模');
    if (result.limited) clamped++;
    adjustments++;
  }
}
console.log(JSON.stringify({ passed: true, combinations: 32, clear, requiresGuard: limited, adjustments, clamped, worstAdjustmentMs, totalMilliseconds: Math.round(performance.now() - start) }, null, 2));
root.traverse(node => { node.morphTargetInfluences?.fill(0); });
guard.hairGeometry.translate(.06, 0, 0);
guard.hairGeometry.boundsTree.refit();
assert.equal(guard.isClear(), false, '刻意將髮型移入頭部時，防護應偵測到相交');
guard.dispose();

// 隔離滑桿回退流程：碰撞判定另由上面的真實模型交線驗證。
const node = { morphTargetDictionary: { jawWidth_minimum: 0, jawWidth_maximum: 1 }, morphTargetInfluences: [0, 0] };
const testRoot = { traverse(callback) { callback(node); } };
const testGuard = { isClear() { return node.morphTargetInfluences[1] <= .37; }, refit() {} };
const accepted = applyGuardedMorph(testRoot, testGuard, 'jawWidth', 100);
assert(accepted.limited && accepted.value <= 37 && accepted.value >= 35, '碰撞時應限制滑桿並保留安全值');
assert(testGuard.isClear());
console.log('CONTACT_GUARD_REJECTION_AND_ROLLBACK passed');
