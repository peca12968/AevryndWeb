import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v2.glb';
const bytes = await readFile(modelPath);
const gltf = await loadGeometry(bytes);

const expected = [
  'AevryndFemaleBodyBase',
  ...['L', 'R'].flatMap((side) =>
    ['Sclera', 'Iris', 'Pupil', 'Cornea', 'LimbalRing'].map((layer) => `Eye_${side}_${layer}`),
  ),
];
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));
for (const name of expected) assert(objects.has(name), `missing explicit layer ${name}`);

const bounds = new THREE.Box3().setFromObject(gltf.scene, true);
const size = bounds.getSize(new THREE.Vector3());
assert(Math.abs(size.y - 1.72) < 0.01, `unexpected exported height ${size.y}`);

for (const side of ['L', 'R']) {
  const sclera = objects.get(`Eye_${side}_Sclera`);
  const iris = objects.get(`Eye_${side}_Iris`);
  const pupil = objects.get(`Eye_${side}_Pupil`);
  assert(sclera.isMesh && iris.isMesh && pupil.isMesh, `${side} eye layers are not meshes`);
  assert(iris.geometry.attributes.uv, `${side} iris has no UVs`);
  assert(pupil.geometry.attributes.position.count >= 90, `${side} pupil is undersampled`);
}

const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
assert(documentText.includes('aevrynd-iris-hazel-v1'), 'authored iris texture is missing');
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-authoring-v2: ${expected.length} layers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB, height ${size.y.toFixed(3)} m`);
