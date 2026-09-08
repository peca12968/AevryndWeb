import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v37.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v37-lod1.glb';

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
    const meniscus = found.get(`Eye_${side}_TearMeniscus`);
    const caruncle = found.get(`Eye_${side}_Caruncle`);
    assert(meniscus?.isMesh, `${path}: ${side} rebuilt tear meniscus is missing`);
    assert(caruncle?.isMesh, `${path}: ${side} lacrimal caruncle is missing`);
    assert.equal(meniscus.geometry.getAttribute('position').count, 94, `${path}: invalid meniscus topology`);
    assert.equal(caruncle.geometry.getAttribute('position').count, 15, `${path}: invalid caruncle topology`);
  }
  const scalp = found.get('HairScalp');
  assert(scalp?.geometry.getAttribute('color'), `${path}: scalp density is missing`);
  const scalpMaterial = document.materials.find((entry) => entry.name === 'Aevrynd_Hair_Scalp');
  assert.equal(scalpMaterial?.alphaMode, 'BLEND', `${path}: scalp transparency mode is missing`);
  assert(document.materials.some((entry) => entry.name === 'Aevrynd_TearFilm_v37'), `${path}: tear material is missing`);
  assert(document.materials.some((entry) => entry.name === 'Aevrynd_Caruncle_v37'), `${path}: caruncle material is missing`);
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
  `female-eye-margins-v37: full ${(fullBytes / 1048576).toFixed(2)} MiB, `
  + `LOD1 ${(lodBytes / 1048576).toFixed(2)} MiB, `
  + `${((1 - lodBytes / fullBytes) * 100).toFixed(1)}% smaller, 4 eye-margin layers present`,
);
