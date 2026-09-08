import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const modelPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v7.glb';
const bytes = await readFile(modelPath);
const jsonLength = bytes.readUInt32LE(12);
const documentText = bytes.subarray(20, 20 + jsonLength).toString();
const document = JSON.parse(documentText);
const gltf = await loadGeometry(bytes);
const objects = new Map();
gltf.scene.traverse((object) => objects.set(object.name, object));

const body = objects.get('AevryndFemaleBodyBase');
assert(body?.isMesh, 'Aevrynd female body is missing');
assert.equal(body.userData.aevrynd_eyelid_revision, 7, 'eyelid revision is missing');
assert.equal(body.userData.aevrynd_eyelid_changed_vertices, 275, 'unexpected eyelid edit coverage');
assert(body.userData.aevrynd_eyelid_max_delta_m <= 0.0006, 'eyelid edit exceeds safety limit');

for (const side of ['L', 'R']) {
  for (const layer of ['UpperLashes', 'LowerLashes', 'TearMeniscus']) {
    const object = objects.get(`Eye_${side}_${layer}`);
    assert(object?.isMesh, `missing Eye_${side}_${layer}`);
    assert.equal(object.userData.aevrynd_eyelid_follow_revision, 7, `${side} ${layer} did not follow the eyelid`);
  }
}

for (const name of ['HairScalp', 'HairGuides', 'HairMain', 'HairlineFine', 'HairFlyaways']) {
  assert(objects.get(name)?.isMesh, `missing inherited groom layer ${name}`);
}
for (const name of ['aevrynd-skin-basecolor-v1', 'aevrynd-sclera-basecolor-v1', 'aevrynd-iris-hazel-v1']) {
  assert((document.images || []).some((image) => image.name === name), `runtime GLB does not embed ${name}`);
}

assert(bytes.length < 5 * 1024 * 1024, `runtime preview exceeds 5 MiB: ${bytes.length}`);
assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), 'prohibited platform dependency found');

console.log(`female-eyelids-v7: 275 bounded edits, 6 followed layers, ${(bytes.length / 1024 / 1024).toFixed(2)} MiB`);
