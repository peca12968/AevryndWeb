import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v21.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v21-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const documentText = bytes.subarray(20, 20 + jsonLength).toString();
  const gltf = await loadGeometry(bytes);
  let scalp;
  let boundary;
  const bones = [];
  gltf.scene.traverse((object) => {
    if (object.name === 'HairScalp') scalp = object;
    if (object.name === 'HairBoundaryClumps') boundary = object;
    if (object.isBone) bones.push(object.name);
  });
  assert(scalp?.isMesh, `${path}: replacement scalp is missing`);
  assert(boundary?.isGroup, `${path}: boundary clump group is missing`);
  assert.equal(boundary.children.filter((child) => child.isMesh).length, 2, `${path}: boundary material primitives regressed`);
  assert.equal(scalp.geometry.getAttribute('position').count, 2497, `${path}: replacement scalp vertex count regressed`);
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');
console.log(`female-hair-foundation-v21: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, ${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller`);
