import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v13.glb';
const bytes = await readFile(modelPath);
const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
const gltf = await loadGeometry(bytes);
const objects = new Map();
const bones = [];
const skinned = [];
gltf.scene.traverse((object) => {
  objects.set(object.name, object);
  if (object.isBone) bones.push(object.name);
  if (object.isSkinnedMesh) skinned.push(object);
});

assert.equal(new Set(bones).size, 21, 'unexpected runtime bone count');
assert(skinned.length >= 5, 'body, clothing and lip skins are incomplete');
assert(objects.get('AevryndFemaleBodyBase')?.geometry.getAttribute('color'), 'skin COLOR_0 regressed');
for (const [name, role, countKey, count] of [
  ['HairClumpsLarge', 'hair_clumps_large', 'aevrynd_clump_count', 57],
  ['HairMain', 'hair_main', 'aevrynd_strand_count', 1756],
  ['HairGuides', 'hair_clumps_medium', 'aevrynd_strand_count', 136],
  ['HairlineFine', 'hairline_fine', 'aevrynd_strand_count', 794],
  ['HairFlyaways', 'hair_flyaways', 'aevrynd_strand_count', 52],
]) {
  const layer = objects.get(name);
  assert(layer, `missing groom layer ${name}`);
  assert.equal(layer.userData.aevrynd_role, role, `${name} has wrong role`);
  assert.equal(layer.userData.aevrynd_groom_revision, 13, `${name} has stale revision`);
  assert.equal(layer.userData[countKey], count, `${name} has wrong element count`);
  assert.equal(layer.parent?.name, 'head', `${name} is not attached to head`);
}
assert.equal(objects.get('HairScalp')?.userData.aevrynd_groom_revision, 13, 'scalp hairline revision is stale');
assert.equal(gltf.animations.length, 1, 'deformation action is missing');
assert(bytes.length < 8 * 1024 * 1024, `groom v13 preview exceeds 8 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-groom-v13: 21 bones, ${skinned.length} skinned layers, 57/136/1756 clump hierarchy, ${(bytes.length / 1024 / 1024).toFixed(3)} MiB`);
