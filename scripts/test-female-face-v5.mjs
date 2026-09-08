import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v5.glb';
const bytes = await readFile(modelPath);
const gltf = await loadGeometry(bytes);
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));

const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isMesh, 'Aevrynd female body is missing');
assert.equal(body.userData.aevrynd_face_detail_revision, 5, 'face detail revision is missing');
assert.equal(body.userData.aevrynd_missed_mouth_samples, 0, 'mouth crease has missed surface samples');

for (const side of ['L', 'R']) {
  for (const layer of ['Iris', 'Pupil', 'LimbalRing']) {
    const object = objects.get(`Eye_${side}_${layer}`);
    assert(object?.isMesh, `missing Eye_${side}_${layer}`);
    assert.equal(object.userData.aevrynd_eye_scale_revision, 5, `${side} ${layer} was not calibrated`);
  }
  const tear = objects.get(`Eye_${side}_TearMeniscus`);
  assert(tear?.isMesh, `missing Eye_${side}_TearMeniscus`);
  assert.equal(tear.userData.aevrynd_role, 'tear_meniscus', `${side} tear role is wrong`);
  assert(tear.geometry.attributes.position.count >= 200, `${side} tear geometry is too sparse`);
}

const mouth = objects.get('Mouth_Crease');
assert(mouth?.isMesh, 'mouth crease layer is missing');
assert.equal(mouth.userData.aevrynd_role, 'mouth_crease', 'mouth crease role is wrong');
assert(mouth.geometry.attributes.position.count >= 300, 'mouth crease geometry is too sparse');

for (const name of ['HairScalp', 'HairGuides', 'HairMain', 'HairlineFine', 'HairFlyaways']) {
  const hair = objects.get(name);
  assert(hair?.isMesh, `missing inherited groom layer ${name}`);
  assert(hair.userData.aevrynd_collision_clearance_m >= 0.0008, `${name} lost body clearance`);
}

const bounds = new THREE.Box3().setFromObject(body, true);
const size = bounds.getSize(new THREE.Vector3());
assert(Math.abs(size.y - 1.72) < 0.01, `unexpected body height ${size.y}`);
assert(bytes.length < 5 * 1024 * 1024, `runtime preview exceeds 5 MiB: ${bytes.length}`);

const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-face-v5: 3 new facial layers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
