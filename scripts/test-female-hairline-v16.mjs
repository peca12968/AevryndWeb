import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v16.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v16-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const documentText = bytes.subarray(20, 20 + jsonLength).toString();
  const gltf = await loadGeometry(bytes);
  const objects = new Map();
  const bones = [];
  gltf.scene.traverse((object) => {
    objects.set(object.name, object);
    if (object.isBone) bones.push(object.name);
  });
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert(objects.get('AevryndFemaleBodyBase')?.geometry.getAttribute('color'), `${path}: skin COLOR_0 regressed`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  assert(!objects.get('HairlineFine'), `${path}: obsolete long hairline layer remains`);
  return { bytes, objects };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
for (const result of [full, lod]) {
  const hairline = result.objects.get('HairlineBaby');
  assert(hairline, 'short transition hairline is missing');
  assert.equal(hairline.userData.aevrynd_role, 'hairline_baby_hairs');
  assert.equal(hairline.userData.aevrynd_groom_revision, 16);
  assert.equal(hairline.userData.aevrynd_strand_count, 84);
  assert.equal(hairline.parent?.name, 'head');
}
for (const name of ['HairClumpsLarge', 'HairGuides', 'HairTempleClumps', 'HairNapeClumps', 'HairScalp']) {
  assert(lod.objects.get(name), `LOD1 is missing retained layer ${name}`);
}
for (const name of ['HairMain', 'HairFlyaways']) {
  assert(!lod.objects.get(name), `LOD1 unexpectedly contains ${name}`);
}
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');

console.log(`female-hairline-v16: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, ${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller`);
