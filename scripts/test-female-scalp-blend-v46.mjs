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
  const undercutEntry = [...found.entries()].find(([name, object]) => name.startsWith('HairUndercutScalp') && object.isMesh);
  assert.equal(Boolean(undercutEntry), !lod, `${path}: undercut LOD state`);
  if (undercutEntry) assert(undercutEntry[1].geometry.getAttribute('color'), `${path}: undercut COLOR_0 missing`);
  if (!lod) {
    const material = document.materials.find(item => item.name === 'Aevrynd_Hair_Undercut_v46');
    assert.equal(material?.alphaMode, 'BLEND', `${path}: undercut blend mode`);
    assert(material?.pbrMetallicRoughness?.roughnessFactor >= 0.71, `${path}: undercut roughness`);
    assert((material?.extensions?.KHR_materials_specular?.specularFactor ?? 1) <= 0.15, `${path}: undercut specular`);
  }
  assert.equal(new Set(bones).size, 21, `${path}: bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: animation count`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text), `${path}: prohibited dependency`);
  return bytes.length;
}

const full = await inspect('.character-build/aevrynd-female-authoring-v46.glb', false);
const lod = await inspect('.character-build/aevrynd-female-authoring-v46-lod1.glb', true);
assert(full < 8 * 1024 * 1024, `full GLB exceeds 8 MiB: ${full}`);
assert(lod <= full * 0.80, 'LOD1 reduction below 20%');
console.log(JSON.stringify({full, lod, reduction: 1 - lod / full}));
