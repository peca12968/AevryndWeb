import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v3.glb';
const bytes = await readFile(modelPath);
const gltf = await loadGeometry(bytes);
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));

const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isMesh, 'Aevrynd female body is missing');
assert.equal(body.userData.aevrynd_identity_revision, 3, 'identity revision is not embedded');
assert(body.userData.aevrynd_identity_changed_vertices >= 2500, 'identity edit is unexpectedly sparse');
assert(body.userData.aevrynd_identity_max_delta_m <= 0.003, 'identity edit exceeds the broad-form safety limit');

const expectedHair = [
  'Brow_L', 'Brow_R',
  'Eye_L_UpperLashes', 'Eye_L_LowerLashes',
  'Eye_R_UpperLashes', 'Eye_R_LowerLashes',
];
for (const name of expectedHair) {
  const object = objects.get(name);
  assert(object?.isMesh, `missing authored hair layer ${name}`);
  assert.equal(object.userData.aevrynd_root_method, 'multires_bvh_raycast', `${name} was not surface anchored`);
  assert(object.geometry.attributes.position.count > 150, `${name} has insufficient strand geometry`);
}

for (const side of ['L', 'R']) {
  for (const layer of ['Sclera', 'Iris', 'Pupil', 'Cornea', 'LimbalRing']) {
    assert(objects.has(`Eye_${side}_${layer}`), `missing Eye_${side}_${layer}`);
  }
}

const bounds = new THREE.Box3().setFromObject(gltf.scene, true);
const size = bounds.getSize(new THREE.Vector3());
assert(Math.abs(size.y - 1.72) < 0.01, `unexpected height ${size.y}`);
assert(bytes.length < 3 * 1024 * 1024, `authoring preview exceeds 3 MiB: ${bytes.length}`);

const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-face-v3: ${expectedHair.length} anchored hair layers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);

