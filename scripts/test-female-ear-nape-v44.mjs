import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadGeometry} from './load-character.mjs';


async function inspect(path, lod) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const text = bytes.subarray(20, 20 + jsonLength).toString();
  const document = JSON.parse(text);
  const gltf = await loadGeometry(bytes);
  const found = new Map();
  const bones = [];
  gltf.scene.traverse(object => { found.set(object.name, object); if (object.isBone) bones.push(object.name); });
  for (const expected of ['HairTempleClumps', 'HairNapeClumps', 'HairBoundaryClumps']) {
    const present = [...found.entries()].some(([name, object]) => name.startsWith(expected) && object.isMesh);
    assert.equal(present, !lod, `${path}: ${expected} LOD state`);
  }
  assert([...found.entries()].some(([name, object]) => name.startsWith('HairClumpsLarge') && object.isMesh && object.geometry.getAttribute('uv')), `${path}: large cards or UV missing`);
  if (lod) {
    assert(![...found.keys()].some(name => name.startsWith('HairClumpsMediumCards')), `${path}: medium cards retained in LOD1`);
    assert(![...found.keys()].some(name => name.startsWith('HairMain')), `${path}: HairMain retained in LOD1`);
    assert(![...found.keys()].some(name => name.startsWith('HairlineBaby')), `${path}: HairlineBaby retained in LOD1`);
    assert(![...found.keys()].some(name => name.startsWith('HairUndercutScalp')), `${path}: HairUndercutScalp retained in LOD1`);
  } else {
    assert([...found.entries()].some(([name, object]) => name.startsWith('HairClumpsMediumCards') && object.isMesh && object.geometry.getAttribute('uv')), `${path}: medium cards or UV missing`);
  }
  const material = document.materials.find(item => item.name === 'Aevrynd_Hair_Clumps_v42');
  assert.equal(material?.alphaMode, 'BLEND', `${path}: card blend mode`);
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  return bytes.length;
}

const full = await inspect('.character-build/aevrynd-female-authoring-v44.glb', false);
const lod = await inspect('.character-build/aevrynd-female-authoring-v44-lod1.glb', true);
assert(full < 8 * 1024 * 1024, `full GLB exceeds 8 MiB: ${full}`);
assert(lod <= full * 0.80, 'LOD1 reduction below 20%');
console.log(JSON.stringify({full, lod, reduction: 1 - lod / full}));
