import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v35.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v35-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const documentText = bytes.subarray(20, 20 + jsonLength).toString();
  const document = JSON.parse(documentText);
  const gltf = await loadGeometry(bytes);
  let body;
  let scalp;
  let undercut;
  const bones = [];
  gltf.scene.traverse((object) => {
    if (object.name === 'AevryndFemaleBodyBase') body = object;
    if (object.name === 'HairScalp') scalp = object;
    if (object.name === 'HairUndercutScalp') undercut = object;
    if (object.isBone) bones.push(object.name);
  });
  assert(body?.geometry.getAttribute('color'), `${path}: skin COLOR_0 is missing`);
  assert(scalp?.isMesh, `${path}: scalp layer is missing`);
  const scalpDensity = scalp.geometry.getAttribute('color');
  assert(scalpDensity, `${path}: scalp COLOR_0 density is missing`);
  let scalpMin = 1;
  let scalpMax = 0;
  for (let index = 0; index < scalpDensity.count; index += 1) {
    scalpMin = Math.min(scalpMin, scalpDensity.getW(index));
    scalpMax = Math.max(scalpMax, scalpDensity.getW(index));
  }
  assert(scalpMin < 0.12 && scalpMax > 0.99, `${path}: scalp density fade was not exported`);
  assert(undercut?.geometry.getAttribute('color'), `${path}: undercut density is missing`);
  const scalpMaterial = document.materials.find((entry) => entry.name === 'Aevrynd_Hair_Scalp');
  assert.equal(scalpMaterial?.alphaMode, 'BLEND', `${path}: scalp transparency mode is missing`);
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes, scalpMin, scalpMax };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');
console.log(
  `female-scalp-transition-v35: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, `
  + `LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, `
  + `${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller, `
  + `scalp alpha ${full.scalpMin.toFixed(3)}-${full.scalpMax.toFixed(3)}`,
);
