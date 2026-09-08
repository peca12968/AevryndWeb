import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v61.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v61-lod1.glb';
const fullOnly = [
  'Brow_L_Density', 'Brow_R_Density',
  'Eye_L_TearMeniscus', 'Eye_R_TearMeniscus',
  'Eye_L_Caruncle', 'Eye_R_Caruncle',
  'Eye_L_UpperLashes', 'Eye_R_UpperLashes',
  'Eye_L_LowerLashes', 'Eye_R_LowerLashes',
];
const retired = [
  'Eye_L_IrisFibers', 'Eye_R_IrisFibers',
  'Eye_L_LimbalRing', 'Eye_R_LimbalRing',
  'Eye_L_UpperFold', 'Eye_R_UpperFold',
];

async function inspect(path, lod) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const text = bytes.subarray(20, 20 + jsonLength).toString();
  const gltf = await loadGeometry(bytes);
  const found = new Map();
  const bones = [];
  gltf.scene.traverse(object => {
    found.set(object.name, object);
    if (object.isBone) bones.push(object.name);
  });

  for (const name of ['Lip_Upper', 'Lip_Lower']) {
    const group = found.get(name);
    assert(group?.isGroup, `${path}: ${name} group missing`);
    const meshes = group.children.filter(child => child.isSkinnedMesh);
    assert.deepEqual(meshes.map(mesh => mesh.geometry.getAttribute('position').count).sort((a, b) => a - b), [130, 195, 260], `${path}: ${name} positions`);
    assert.deepEqual(meshes.map(mesh => mesh.geometry.getIndex().count / 3).sort((a, b) => a - b), [128, 256, 384], `${path}: ${name} triangles`);
  }
  for (const name of ['Mouth_OralCavity', 'Mouth_Tongue', 'Mouth_UpperTeeth', 'Mouth_WetLine', 'Eye_L_Iris', 'Eye_R_Iris', 'Eye_L_Cornea', 'Eye_R_Cornea', 'HairScalp']) {
    assert(found.get(name)?.isMesh, `${path}: ${name} missing`);
  }
  for (const name of fullOnly) assert.equal(found.has(name), !lod, `${path}: ${name} LOD policy`);
  for (const name of retired) assert(!found.has(name), `${path}: retired overlay ${name} exported`);
  for (const name of ['HairMain', 'HairGuides', 'HairFlyaways', 'HairClumpsLarge', 'HairClumpsMediumCards']) {
    assert(!found.has(name), `${path}: legacy groom ${name} present`);
  }
  if (lod) {
    assert(found.get('HairFiberLOD1')?.isMesh, `${path}: HairFiberLOD1 missing`);
    assert(!found.has('HairFiberBase') && !found.has('HairFiberDetail'), `${path}: full groom leaked into LOD1`);
    assert.equal(found.get('HairFiberLOD1').geometry.getAttribute('position').count, 11760, `${path}: LOD1 hair positions`);
  } else {
    assert(found.get('HairFiberBase')?.isMesh && found.get('HairFiberDetail')?.isMesh, `${path}: full fiber layers missing`);
    assert(!found.has('HairFiberLOD1'), `${path}: LOD1 groom leaked into full asset`);
    assert.equal(found.get('HairFiberBase').geometry.getAttribute('position').count, 36960, `${path}: base hair positions`);
    assert.equal(found.get('HairFiberDetail').geometry.getAttribute('position').count, 14540, `${path}: detail hair positions`);
  }
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  assert(/aevrynd-iris-hazel-v61|Aevrynd Iris Hazel V61/i.test(text), `${path}: v61 iris texture missing`);
  return bytes.length;
}

const full = await inspect(fullPath, false);
const lod = await inspect(lodPath, true);
assert(full < 8 * 1024 * 1024, `full exceeds 8 MiB: ${full}`);
assert(lod <= full * 0.80, `LOD1 reduction below 20%: ${lod}/${full}`);
console.log(`female-eye-anatomy-v61: full ${(full / 1048576).toFixed(2)} MiB, LOD1 ${(lod / 1048576).toFixed(2)} MiB, ${((1 - lod / full) * 100).toFixed(1)}% smaller, layered eye and dependency policy pass`);
