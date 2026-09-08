import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v11.glb';
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
for (const [name, role, count] of [
  ['HairMain', 'hair_main', 1756],
  ['HairGuides', 'hair_guides', 136],
  ['HairlineFine', 'hairline_fine', 825],
  ['HairFlyaways', 'hair_flyaways', 52],
]) {
  const layer = objects.get(name);
  assert(layer, `missing groom layer ${name}`);
  let hasMesh = Boolean(layer.isMesh);
  layer.traverse((child) => { hasMesh ||= Boolean(child.isMesh); });
  assert(hasMesh, `${name} has no exported mesh primitive`);
  assert.equal(layer.userData.aevrynd_role, role, `${name} has wrong role`);
  assert.equal(layer.userData.aevrynd_groom_revision, 11, `${name} has stale revision`);
  assert.equal(layer.userData.aevrynd_strand_count, count, `${name} has wrong strand count`);
  assert.equal(layer.parent?.name, 'head', `${name} is not attached to head`);
}
assert.equal(objects.get('HairMain').userData.aevrynd_removed_body_intersection_faces, 497,
  'main groom collision cleanup is missing');
assert.equal(objects.get('HairlineFine').userData.aevrynd_removed_body_intersection_faces, 54,
  'hairline collision cleanup is missing');
assert.equal(gltf.animations.length, 1, 'deformation action is missing');
assert(bytes.length < 8 * 1024 * 1024, `groom v11 preview exceeds 8 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-groom-v11: 21 bones, ${skinned.length} skinned layers, 2769 groom strands, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
