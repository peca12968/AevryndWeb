import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v38.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v38-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const documentText = bytes.subarray(20, 20 + jsonLength).toString();
  const document = JSON.parse(documentText);
  const gltf = await loadGeometry(bytes);
  const found = new Map();
  const bones = [];
  gltf.scene.traverse((object) => {
    found.set(object.name, object);
    if (object.isBone) bones.push(object.name);
  });
  for (const side of ['L', 'R']) {
    const upper = found.get(`Eye_${side}_UpperLashes`);
    const lower = found.get(`Eye_${side}_LowerLashes`);
    assert(upper?.isMesh && lower?.isMesh, `${path}: ${side} lash layers are missing`);
    assert.equal(upper.geometry.getAttribute('position').count, 390, `${path}: invalid upper lash topology`);
    assert.equal(lower.geometry.getAttribute('position').count, 180, `${path}: invalid lower lash topology`);
    assert(found.get(`Eye_${side}_Caruncle`)?.isMesh, `${path}: ${side} caruncle is missing`);
    assert(found.get(`Eye_${side}_TearMeniscus`)?.isMesh, `${path}: ${side} meniscus is missing`);
  }
  assert(found.get('HairScalp')?.geometry.getAttribute('color'), `${path}: scalp density is missing`);
  assert.equal(document.materials.find((entry) => entry.name === 'Aevrynd_Hair_Scalp')?.alphaMode, 'BLEND');
  assert(document.materials.some((entry) => entry.name === 'Aevrynd_Lash_Hair_v38'), `${path}: lash material is missing`);
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return bytes.length;
}

const fullBytes = await inspect(fullPath);
const lodBytes = await inspect(lodPath);
assert(fullBytes < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${fullBytes}`);
assert(lodBytes <= fullBytes * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');
console.log(
  `female-lashes-v38: full ${(fullBytes / 1048576).toFixed(2)} MiB, `
  + `LOD1 ${(lodBytes / 1048576).toFixed(2)} MiB, `
  + `${((1 - lodBytes / fullBytes) * 100).toFixed(1)}% smaller, 4 tapered lash layers present`,
);
