import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v39.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v39-lod1.glb';

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
    const brow = found.get(`Brow_${side}`);
    const density = found.get(`Brow_${side}_Density`);
    assert(brow && density?.isMesh, `${path}: brow ${side} hierarchy is missing`);
    let browVertices = 0;
    brow.traverse((object) => {
      if (object.isMesh) browVertices += object.geometry.getAttribute('position').count;
    });
    assert.equal(browVertices, 1800, `${path}: invalid brow topology`);
    assert.equal(density.geometry.getAttribute('position').count, 175, `${path}: invalid brow density topology`);
    const color = density.geometry.getAttribute('color');
    assert(color && color.itemSize === 4, `${path}: brow density COLOR_0 alpha is missing`);
    let minAlpha = 1;
    let maxAlpha = 0;
    for (let index = 0; index < color.count; index += 1) {
      minAlpha = Math.min(minAlpha, color.getW(index));
      maxAlpha = Math.max(maxAlpha, color.getW(index));
    }
    assert(minAlpha < 0.03 && maxAlpha > 0.40, `${path}: brow density fade is invalid`);
  }
  assert.equal(document.materials.find((entry) => entry.name === 'Aevrynd_Brow_Density_v39')?.alphaMode, 'BLEND');
  assert(found.get('HairScalp')?.geometry.getAttribute('color'), `${path}: scalp density is missing`);
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
  `female-brows-v39: full ${(fullBytes / 1048576).toFixed(2)} MiB, `
  + `LOD1 ${(lodBytes / 1048576).toFixed(2)} MiB, `
  + `${((1 - lodBytes / fullBytes) * 100).toFixed(1)}% smaller, 2 fiber + 2 density layers present`,
);
