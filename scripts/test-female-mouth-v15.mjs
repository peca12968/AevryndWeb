import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v15.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v15-lod1.glb';

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
  assert.equal(new Set(bones).size, 21, `${path}: unexpected bone count`);
  assert(skinned.length >= 6, `${path}: mouth skin layers are incomplete`);
  assert(objects.get('AevryndFemaleBodyBase')?.geometry.getAttribute('color'), `${path}: skin COLOR_0 regressed`);
  assert.equal(objects.get('AevryndFemaleBodyBase')?.userData.aevrynd_mouth_revision, 15, `${path}: body mouth revision is stale`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes, objects };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
for (const [name, role] of [
  ['Lip_Upper', 'upper_lip_volume'],
  ['Lip_Lower', 'lower_lip_volume'],
  ['Mouth_WetLine', 'mouth_wet_line'],
]) {
  for (const runtime of [full, lod]) {
    const layer = runtime.objects.get(name);
    assert(layer?.isSkinnedMesh, `${name} is missing or not skinned`);
    assert.equal(layer.userData.aevrynd_role, role, `${name} has wrong role`);
    assert.equal(layer.userData.aevrynd_mouth_revision, 15, `${name} has stale revision`);
  }
}
assert(!full.objects.get('Mouth_Crease'), 'obsolete flat mouth crease still exported');
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.77, 'LOD1 does not reduce at least 23% of GLB bytes');

console.log(`female-mouth-v15: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, three skinned mouth layers`);
