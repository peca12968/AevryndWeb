import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath = process.argv[2] || '.character-build/aevrynd-female-authoring-v25.glb';
const lodPath = process.argv[3] || '.character-build/aevrynd-female-authoring-v25-lod1.glb';

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
  const color = body?.geometry.getAttribute('color');
  assert(color, `${path}: skin COLOR_0 is missing`);
  let minimum = 1;
  let maximum = 0;
  for (let index = 0; index < color.count; index += 1) {
    minimum = Math.min(minimum, color.getX(index), color.getY(index), color.getZ(index));
    maximum = Math.max(maximum, color.getX(index), color.getY(index), color.getZ(index));
  }
  assert(maximum - minimum > 0.05, `${path}: exported regional skin color variation is too weak`);
  const skin = document.materials.find((entry) => entry.name === 'Aevrynd_Skin_Clay');
  assert(skin?.normalTexture, `${path}: GLB skin normal texture is missing`);
  assert(skin?.pbrMetallicRoughness?.metallicRoughnessTexture, `${path}: GLB skin roughness texture is missing`);
  const normalImage = document.images[document.textures[skin.normalTexture.index].source];
  const roughnessImage = document.images[document.textures[skin.pbrMetallicRoughness.metallicRoughnessTexture.index].source];
  assert.match(normalImage.name, /skin-normal-v2/i, `${path}: wrong normal image`);
  assert.match(roughnessImage.name, /skin-roughness-v2/i, `${path}: wrong roughness image`);
  assert.equal(new Set(bones).size, 21, `${path}: unexpected runtime bone count`);
  assert.equal(gltf.animations.length, 1, `${path}: deformation action is missing`);
  assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(documentText), `${path}: prohibited dependency found`);
  return { bytes, minimum, maximum };
}

const full = await inspect(fullPath);
const lod = await inspect(lodPath);
assert(full.bytes.length < 8 * 1024 * 1024, `full preview exceeds 8 MiB: ${full.bytes.length}`);
assert(lod.bytes.length <= full.bytes.length * 0.80, 'LOD1 does not reduce at least 20% of GLB bytes');

console.log(
  `female-skin-detail-v25: full ${(full.bytes.length / 1048576).toFixed(2)} MiB, `
  + `LOD1 ${(lod.bytes.length / 1048576).toFixed(2)} MiB, `
  + `${((1 - lod.bytes.length / full.bytes.length) * 100).toFixed(1)}% smaller, `
  + `COLOR_0 ${(full.minimum).toFixed(3)}-${(full.maximum).toFixed(3)}`,
);
