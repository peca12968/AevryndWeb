import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v18.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v18-lod1.glb';

async function inspect(path) {
  const bytes = await readFile(path);
  const jsonLength = bytes.readUInt32LE(12);
  const documentText = bytes.subarray(20, 20 + jsonLength).toString();
  const document = JSON.parse(documentText);
  const gltf = await loadGeometry(bytes);
  let body;
  const bones = [];
  gltf.scene.traverse((object) => {
    if (object.name === 'AevryndFemaleBodyBase') body = object;
    if (object.isBone) bones.push(object.name);
  });
  assert(body?.geometry.getAttribute('color'), `${path}: skin COLOR_0 regressed`);
  const skin = document.materials.find((material) => material.name === 'Aevrynd_Skin_Clay');
  assert(skin?.normalTexture, `${path}: GLB skin normalTexture is missing`);
  assert(skin?.pbrMetallicRoughness?.metallicRoughnessTexture, `${path}: GLB skin roughness texture is missing`);
  const normalImage = document.images[document.textures[skin.normalTexture.index].source];
  const roughnessImage = document.images[document.textures[skin.pbrMetallicRoughness.metallicRoughnessTexture.index].source];
  assert.match(normalImage.name, /skin-normal-v2/i, `${path}: wrong normal image`);
  assert.match(roughnessImage.name, /skin-roughness-v2/i, `${path}: wrong roughness image`);
  assert.equal(normalImage.mimeType, 'image/png');
  assert.equal(roughnessImage.mimeType, 'image/png');
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');

console.log(`female-identity-v18: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, ${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller`);
