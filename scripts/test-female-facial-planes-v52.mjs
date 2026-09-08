import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v52.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v52-lod1.glb';
const detailOnly = [
  'Brow_L_Density', 'Brow_R_Density', 'Eye_L_IrisFibers', 'Eye_R_IrisFibers',
  'Eye_L_TearMeniscus', 'Eye_R_TearMeniscus', 'Eye_L_UpperLashes', 'Eye_R_UpperLashes',
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
  if (!lod) {
    for (const [kind, positions, triangles] of [['Upper', 828, 1380], ['Lower', 396, 660]]) {
      for (const side of ['L', 'R']) {
        const name = `Eye_${side}_${kind}Lashes`;
        const mesh = found.get(name);
        assert(mesh?.isMesh, `${path}: ${name} mesh missing`);
        assert.equal(mesh.geometry.getAttribute('position').count, positions, `${path}: ${name} positions`);
        assert.equal(mesh.geometry.getIndex().count / 3, triangles, `${path}: ${name} triangles`);
      }
    }
  }
  for (const name of ['Mouth_OralCavity', 'Mouth_Tongue', 'Mouth_UpperTeeth', 'Mouth_WetLine']) {
    assert(found.get(name)?.isMesh, `${path}: ${name} missing`);
  }
  assert(found.get('Eye_L_Iris')?.isMesh && found.get('Eye_R_Iris')?.isMesh, `${path}: base irises missing`);
  for (const name of detailOnly) {
    assert.equal(found.has(name), !lod, `${path}: ${name} LOD policy`);
  }
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  return bytes.length;
}

const full = await inspect(fullPath, false);
const lod = await inspect(lodPath, true);
assert(full < 8 * 1024 * 1024, `full exceeds 8 MiB: ${full}`);
assert(lod <= full * 0.80, `LOD1 reduction below 20%: ${lod}/${full}`);
console.log(`female-facial-planes-v52: full ${(full / 1048576).toFixed(2)} MiB, LOD1 ${(lod / 1048576).toFixed(2)} MiB, ${((1 - lod / full) * 100).toFixed(1)}% smaller, facial planes and LOD policy pass`);
