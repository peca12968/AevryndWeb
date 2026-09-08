import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v6.glb';
const bytes = await readFile(modelPath);
const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
const document = JSON.parse(documentText);
const gltf = await loadGeometry(bytes);
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));

const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isMesh, 'Aevrynd female body is missing');
assert.equal(body.userData.aevrynd_skin_texture_revision, 6, 'skin texture revision is missing');
assert.equal(body.userData.aevrynd_skin_texture_resolution, 1024, 'skin texture resolution is wrong');

for (const side of ['L', 'R']) {
  const sclera = objects.get(`Eye_${side}_Sclera`);
  assert(sclera?.isMesh, `missing Eye_${side}_Sclera`);
  assert.equal(sclera.userData.aevrynd_sclera_texture_revision, 6, `${side} sclera texture revision is missing`);
}

const images = new Set((document.images || []).map((image) => image.name));
for (const name of ['aevrynd-skin-basecolor-v1', 'aevrynd-sclera-basecolor-v1', 'aevrynd-iris-hazel-v1']) {
  assert(images.has(name), `runtime GLB does not embed ${name}`);
}

const materialByName = new Map(document.materials.map((material) => [material.name, material]));
const skin = materialByName.get('Aevrynd_Skin_Clay');
const sclera = materialByName.get('Aevrynd_Eye_Sclera');
assert(skin?.pbrMetallicRoughness?.baseColorTexture, 'skin base-color texture is not connected');
assert(sclera?.pbrMetallicRoughness?.baseColorTexture, 'sclera base-color texture is not connected');
assert.equal(skin.normalTexture, undefined, 'unvalidated skin normal map must not enter runtime');
assert.equal(skin.pbrMetallicRoughness.roughnessTexture, undefined, 'unvalidated roughness map must not enter runtime');

for (const name of ['HairScalp', 'HairGuides', 'HairMain', 'HairlineFine', 'HairFlyaways']) {
  const hair = objects.get(name);
  assert(hair?.isMesh, `missing inherited groom layer ${name}`);
  assert(hair.userData.aevrynd_collision_clearance_m >= 0.0008, `${name} lost body clearance`);
}
for (const name of ['Eye_L_TearMeniscus', 'Eye_R_TearMeniscus', 'Mouth_Crease']) {
  assert(objects.get(name)?.isMesh, `missing inherited face layer ${name}`);
}

assert(bytes.length < 5 * 1024 * 1024, `runtime preview exceeds 5 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-skin-v6: 3 embedded color maps, safe tangent fallback, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
