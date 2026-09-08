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
  const large = [...found.entries()].find(([name, object]) => name.startsWith('HairClumpsLarge') && object.isMesh)?.[1];
  assert(large?.geometry.getAttribute('uv'), `${path}: large cards or UV missing`);
  const medium = [...found.entries()].find(([name, object]) => name.startsWith('HairClumpsMediumCards') && object.isMesh)?.[1];
  assert.equal(Boolean(medium), !lod, `${path}: medium card LOD state`);
  if (medium) assert(medium.geometry.getAttribute('uv'), `${path}: medium card UV missing`);
  const material = document.materials.find(item => item.name === 'Aevrynd_Hair_Clumps_v45');
  assert.equal(material?.alphaMode, 'BLEND', `${path}: card blend mode`);
  assert(material?.pbrMetallicRoughness?.baseColorTexture, `${path}: card alpha texture missing`);
  assert(material?.pbrMetallicRoughness?.roughnessFactor >= 0.57, `${path}: roughness too low`);
  assert((material?.extensions?.KHR_materials_specular?.specularFactor ?? 1) <= 0.15, `${path}: specular too high`);
  if (lod) {
    for (const name of ['HairMain', 'HairlineBaby', 'HairTempleClumps', 'HairNapeClumps', 'HairBoundaryClumps', 'HairUndercutScalp']) {
      assert(![...found.keys()].some(value => value.startsWith(name)), `${path}: ${name} retained in LOD1`);
    }
  }
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  return bytes.length;
}

const full = await inspect('.character-build/aevrynd-female-authoring-v45.glb', false);
const lod = await inspect('.character-build/aevrynd-female-authoring-v45-lod1.glb', true);
assert(full < 8 * 1024 * 1024, `full GLB exceeds 8 MiB: ${full}`);
assert(lod <= full * 0.80, 'LOD1 reduction below 20%');
console.log(JSON.stringify({full, lod, reduction: 1 - lod / full}));
