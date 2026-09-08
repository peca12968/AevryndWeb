import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v8.glb';
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

const expectedBones = [
  'root', 'pelvis', 'spine_01', 'spine_02', 'chest', 'neck', 'head',
  'clavicleL', 'upper_armL', 'forearmL', 'handL',
  'clavicleR', 'upper_armR', 'forearmR', 'handR',
  'thighL', 'shinL', 'footL', 'thighR', 'shinR', 'footR',
];
for (const name of expectedBones) assert(bones.includes(name), `missing runtime bone ${name}`);
assert.equal(new Set(bones).size, 21, 'unexpected runtime bone count');

assert.equal(skinnedMeshes.length, 1, 'expected exactly one skinned body mesh');
const body = skinnedMeshes[0];
assert.equal(body.name, 'AevryndFemaleBodyBase', 'wrong skinned body mesh');
assert.equal(body.skeleton.bones.length, 21, 'body skeleton is incomplete');
assert.equal(body.userData.aevrynd_skin_binding_revision, 8, 'skin binding revision is missing');
assert.equal(body.userData.aevrynd_unweighted_vertices, 0, 'body has unweighted vertices');
assert.equal(body.userData.aevrynd_maximum_influences, 4, 'body exceeds four bone influences');
assert.equal(body.userData.aevrynd_weight_limit, 4, 'weight limit metadata is missing');
assert(body.userData.aevrynd_trimmed_weight_entries > 0, 'weight pruning did not run');

assert.equal(gltf.animations.length, 1, 'deformation action is missing');
const action = gltf.animations[0];
assert.equal(action.name, 'Aevrynd_Female_DeformationSuite_v1', 'wrong deformation action');
assert(action.duration >= 0.8, 'deformation action is too short');
assert(action.tracks.length >= 60, 'deformation action has insufficient tracks');

for (const name of ['HairScalp', 'HairGuides', 'HairMain', 'HairlineFine', 'HairFlyaways']) {
  const object = objects.get(name);
  assert(object?.isMesh, `missing inherited groom layer ${name}`);
  assert.equal(object.parent?.name, 'head', `${name} is not rigidly parented to head`);
}
for (const name of ['Eye_L_TearMeniscus', 'Eye_R_TearMeniscus', 'Mouth_Crease']) {
  assert.equal(objects.get(name)?.parent?.name, 'head', `${name} is not rigidly parented to head`);
}

for (const name of ['aevrynd-skin-basecolor-v1', 'aevrynd-sclera-basecolor-v1', 'aevrynd-iris-hazel-v1']) {
  assert((document.images || []).some((image) => image.name === name), `runtime GLB does not embed ${name}`);
}
assert(bytes.length < 6 * 1024 * 1024, `rigged runtime preview exceeds 6 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-rig-v8: 21 bones, 1 skin, 1 deformation action, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
