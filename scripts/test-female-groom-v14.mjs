import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v14.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v14-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
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
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert(skinned.length >= 5, `${path}: body, clothing and lip skins are incomplete`);
  assert(objects.get('AevryndFemaleBodyBase')?.geometry.getAttribute('color'), `${path}: skin COLOR_0 regressed`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes, objects, skinned };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
for (const [name, role, countKey, count] of [
  ['HairClumpsLarge', 'hair_clumps_large', 'aevrynd_clump_count', 57],
  ['HairMain', 'hair_main', 'aevrynd_strand_count', 1756],
  ['HairGuides', 'hair_clumps_medium', 'aevrynd_strand_count', 136],
  ['HairlineFine', 'hairline_fine', 'aevrynd_strand_count', 397],
  ['HairFlyaways', 'hair_flyaways', 'aevrynd_strand_count', 52],
  ['HairTempleClumps', 'hair_temple_clumps', 'aevrynd_clump_count', 60],
  ['HairNapeClumps', 'hair_nape_clumps', 'aevrynd_clump_count', 46],
]) {
  const layer = full.objects.get(name);
  assert(layer, `full model is missing ${name}`);
  assert.equal(layer.userData.aevrynd_role, role, `${name} has wrong role`);
  assert.equal(layer.userData.aevrynd_groom_revision, 14, `${name} has stale revision`);
  assert.equal(layer.userData[countKey], count, `${name} has wrong element count`);
  assert.equal(layer.parent?.name, 'head', `${name} is not attached to head`);
}
for (const name of ['HairClumpsLarge', 'HairGuides', 'HairTempleClumps', 'HairNapeClumps', 'HairScalp']) {
  assert(lod.objects.get(name), `LOD1 is missing retained layer ${name}`);
}
for (const name of ['HairMain', 'HairlineFine', 'HairFlyaways']) {
  assert(!lod.objects.get(name), `LOD1 unexpectedly contains ${name}`);
}
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.77, 'LOD1 does not reduce at least 23% of GLB bytes');

console.log(`female-groom-v14: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, ${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller`);
