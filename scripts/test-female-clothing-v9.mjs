import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v9.glb';
const bytes = await readFile(modelPath);
const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
const document = JSON.parse(documentText);
const gltf = await loadGeometry(bytes);

const objects = new Map();
const bones = [];
const skinnedMeshes = [];
gltf.scene.traverse((object) => {
  objects.set(object.name, object);
  if (object.isBone) bones.push(object.name);
  if (object.isSkinnedMesh) skinnedMeshes.push(object);
});

assert.equal(new Set(bones).size, 21, 'unexpected runtime bone count');
assert.equal(skinnedMeshes.length, 3, 'expected body plus two skinned clothing layers');
for (const [name, role, clearance] of [
  ['Clothing_InnerTop', 'inner_clothing_top', 0.0064],
  ['Clothing_InnerShorts', 'inner_clothing_bottom', 0.0194],
]) {
  const garment = objects.get(name);
  assert(garment?.isSkinnedMesh, `missing skinned garment ${name}`);
  assert.equal(garment.userData.aevrynd_role, role, `${name} has wrong layer role`);
  assert.equal(garment.userData.aevrynd_clothing_revision, 9, `${name} has wrong revision`);
  assert.equal(garment.userData.aevrynd_unweighted_vertices, 0, `${name} has unweighted vertices`);
  assert.equal(garment.userData.aevrynd_maximum_influences, 4, `${name} exceeds four influences`);
  assert(Math.abs(garment.userData.aevrynd_body_clearance_m - clearance) < 1e-6,
    `${name} has unexpected authored clearance`);
}

assert.equal(gltf.animations.length, 1, 'deformation action is missing');
assert(gltf.animations[0].tracks.length >= 60, 'deformation action has insufficient tracks');
for (const name of ['aevrynd-skin-basecolor-v1', 'aevrynd-sclera-basecolor-v1', 'aevrynd-iris-hazel-v1']) {
  assert((document.images || []).some((image) => image.name === name), `runtime GLB does not embed ${name}`);
}
assert(bytes.length < 7 * 1024 * 1024, `clothed runtime preview exceeds 7 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-clothing-v9: 21 bones, 3 skins, 2 clothing layers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
