import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v12.glb';
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
const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isSkinnedMesh, 'female body skin is missing');
assert(body.geometry.getAttribute('color'), 'exported COLOR_0 skin variation is missing');
assert.equal(body.userData.aevrynd_face_revision, 12, 'body facial revision is stale');

for (const side of ['L', 'R']) {
  for (const [suffix, role] of [['UpperFold', 'upper_eyelid_fold'], ['Catchlight', 'eye_catchlight']]) {
    const name = `Eye_${side}_${suffix}`;
    const layer = objects.get(name);
    assert(layer, `missing face layer ${name}`);
    assert.equal(layer.userData.aevrynd_role, role, `${name} has wrong role`);
    assert.equal(layer.userData.aevrynd_face_revision, 12, `${name} has stale revision`);
    assert.equal(layer.parent?.name, 'head', `${name} is not attached to head`);
  }
}

for (const [name, count] of [
  ['HairMain', 1756], ['HairGuides', 136], ['HairlineFine', 825], ['HairFlyaways', 52],
]) {
  assert.equal(objects.get(name)?.userData.aevrynd_strand_count, count, `${name} strand count regressed`);
}
assert.equal(gltf.animations.length, 1, 'deformation action is missing');
assert(bytes.length < 8.5 * 1024 * 1024, `face v12 preview exceeds 8.5 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-face-v12: 21 bones, ${skinned.length} skinned layers, COLOR_0 skin tone, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
