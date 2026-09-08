import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v10.glb';
const bytes = await readFile(modelPath);
const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
const document = JSON.parse(documentText);
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
for (const [name, role] of [['Lip_Upper', 'upper_lip'], ['Lip_Lower', 'lower_lip']]) {
  const lip = objects.get(name);
  assert(lip?.isSkinnedMesh, `${name} is not an exported skinned layer`);
  assert.equal(lip.userData.aevrynd_role, role, `${name} has wrong semantic role`);
  assert.equal(lip.userData.aevrynd_skin_binding_revision, 10, `${name} has stale skin binding`);
  assert.equal(lip.userData.aevrynd_dynamic_clearance_m, 0.00085, `${name} clearance is missing`);
}

const fibers = objects.get('HairFiberDetail');
assert(fibers?.isMesh, 'fine hair fiber layer is missing');
assert.equal(fibers.userData.aevrynd_role, 'hair_fiber_detail', 'wrong fine hair role');
assert.equal(fibers.userData.aevrynd_fiber_strands, 1288, 'wrong fine hair strand count');
assert.equal(fibers.parent?.name, 'head', 'fine hair is not rigidly attached to the head');

const main = objects.get('HairMain');
assert(main?.isMesh, 'main hair layer is missing');
assert.equal(main.userData.aevrynd_alpha_card_revision, 10, 'main hair lacks alpha-card metadata');
assert.equal(main.userData.aevrynd_removed_body_intersection_faces, 8, 'main hair collision cleanup is missing');
assert.equal(fibers.userData.aevrynd_removed_body_intersection_faces, 17, 'fiber collision cleanup is missing');

const hairImage = (document.images || []).find((image) => image.name === 'aevrynd-hair-strands-v1');
assert(hairImage, 'self-authored hair strand texture is not embedded');
const alphaMaterial = (document.materials || []).find((item) => item.name === 'Aevrynd_Hair_AlphaStrands');
assert.equal(alphaMaterial?.alphaMode, 'BLEND', 'hair material does not export transparency');
assert.equal(gltf.animations.length, 1, 'deformation action is missing');
assert(skinned.length >= 5, `expected body, clothing and lip skins; found ${skinned.length}`);
assert(bytes.length < 7 * 1024 * 1024, `head v10 preview exceeds 7 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-head-v10: 21 bones, ${skinned.length} skinned layers, 1288 hair fibers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
