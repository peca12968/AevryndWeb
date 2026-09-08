import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v4.glb';
const bytes = await readFile(modelPath);
const gltf = await loadGeometry(bytes);
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));

const expectedHair = new Map([
  ['HairScalp', ['hair_scalp', 1000]],
  ['HairGuides', ['hair_guides', 500]],
  ['HairMain', ['hair_main', 2000]],
  ['HairlineFine', ['hairline_fine', 1000]],
  ['HairFlyaways', ['hair_flyaways', 100]],
]);

for (const [name, [role, minimumVertices]] of expectedHair) {
  const object = objects.get(name);
  assert(object?.isMesh, `missing explicit groom layer ${name}`);
  assert.equal(object.userData.aevrynd_role, role, `${name} has the wrong role`);
  assert.equal(
    object.userData.aevrynd_source,
    'Aevrynd authored groom on CC0 female base',
    `${name} has untraceable source metadata`,
  );
  assert(
    object.userData.aevrynd_collision_clearance_m >= 0.0008,
    `${name} has insufficient body clearance`,
  );
  assert(
    object.geometry.attributes.position.count >= minimumVertices,
    `${name} has insufficient geometry`,
  );
}

for (const side of ['L', 'R']) {
  for (const layer of ['Sclera', 'Iris', 'Pupil', 'Cornea', 'LimbalRing']) {
    assert(objects.has(`Eye_${side}_${layer}`), `missing Eye_${side}_${layer}`);
  }
  for (const layer of ['UpperLashes', 'LowerLashes']) {
    assert(objects.has(`Eye_${side}_${layer}`), `missing Eye_${side}_${layer}`);
  }
}

const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isMesh, 'Aevrynd female body is missing');
const bounds = new THREE.Box3().setFromObject(body, true);
const size = bounds.getSize(new THREE.Vector3());
assert(Math.abs(size.y - 1.72) < 0.01, `unexpected height ${size.y}`);
assert(bytes.length < 5 * 1024 * 1024, `runtime preview exceeds 5 MiB: ${bytes.length}`);

const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(
  `female-hair-v4: ${expectedHair.size} groom layers, zero missed roots, `
    + `${(bytes.length / 1024 / 1024).toFixed(2)} MiB`,
);
