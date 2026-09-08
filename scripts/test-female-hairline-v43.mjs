import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadGeometry} from './load-character.mjs';

async function inspect(path, lod) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const text = bytes.subarray(20, 20 + jsonLength).toString();
  const gltf = await loadGeometry(bytes);
  const found = new Map();
  const bones = [];
  gltf.scene.traverse(object => { found.set(object.name, object); if (object.isBone) bones.push(object.name); });
  const baby = [...found.entries()].find(([name, object]) => name.startsWith('HairlineBaby') && object.isMesh)?.[1];
  assert(baby, `${path}: HairlineBaby missing; hair nodes=${[...found.keys()].filter(name => name.startsWith('Hair')).join(',')}`);
  assert(found.get('HairClumpsLarge')?.geometry.getAttribute('uv'), `${path}: large card UV missing`);
  if (lod) {
    assert(!found.has('HairClumpsMediumCards'), `${path}: medium cards retained in LOD1`);
    assert(!found.has('HairMain'), `${path}: HairMain retained in LOD1`);
  } else {
    assert(found.get('HairClumpsMediumCards')?.geometry.getAttribute('uv'), `${path}: medium card UV missing`);
  }
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  return bytes.length;
}

const full = await inspect('.character-build/aevrynd-female-authoring-v43.glb', false);
const lod = await inspect('.character-build/aevrynd-female-authoring-v43-lod1.glb', true);
assert(full < 8 * 1024 * 1024, 'full GLB exceeds 8 MiB');
assert(lod <= full * 0.80, 'LOD1 reduction below 20%');
console.log(JSON.stringify({full, lod, reduction: 1 - lod / full}));
