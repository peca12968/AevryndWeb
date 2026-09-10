import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { loadGeometry } from './load-character.mjs';

const path = process.argv[2] ?? new URL('../.character-build/aevrynd-female-authoring-v249-packed.glb', import.meta.url);
const bytes = await readFile(path);
assert(bytes.length < 15 * 1024 * 1024, '候選 GLB 超過 15MB 預算');
assert.equal(bytes.readUInt32LE(8), bytes.length, 'GLB 標頭長度不一致');
const jsonLength = bytes.readUInt32LE(12);
const document = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
assert(document.extensionsRequired?.includes('EXT_meshopt_compression'), '缺少 meshopt 壓縮');

const imageNames = new Set((document.images ?? []).map(image => image.name));
for (const name of [
  'aevrynd-female-skin-base-v248',
  'aevrynd-female-skin-roughness-v216',
  'aevrynd-female-skin-normal-v219',
  'aevrynd-hair-clump-atlas-v3',
  'aevrynd-hairline-root-atlas-v1',
  'aevrynd-iris-hazel-v5',
]) assert(imageNames.has(name), `缺少嵌入貼圖 ${name}`);
for (const image of document.images ?? []) {
  const view = document.bufferViews[image.bufferView];
  assert(view && view.byteLength > 0, `${image.name} 沒有有效 bufferView`);
}

const skinDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_Skin_Baked_v248');
assert(skinDocumentMaterial, '缺少 v248 烘焙皮膚材質');
assert.equal(skinDocumentMaterial.pbrMetallicRoughness.baseColorTexture.texCoord, 1, '皮膚底色未使用 atlas UV');
assert.equal(skinDocumentMaterial.pbrMetallicRoughness.metallicRoughnessTexture.texCoord, 1, '皮膚粗糙度未使用 atlas UV');
assert.equal(skinDocumentMaterial.normalTexture.texCoord, 1, '皮膚法線未使用 atlas UV');
const hairDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_HairCards_v166');
assert(hairDocumentMaterial?.pbrMetallicRoughness?.baseColorTexture, '髮卡缺少自有 atlas');
assert.equal(hairDocumentMaterial.alphaMode, 'BLEND', 'v194 應保留通過目視的 alpha blend 髮絲');
const fiberDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_HairDetailFibers_v246');
assert(fiberDocumentMaterial, '缺少 v246 幾何細髮絲材質');
assert(!fiberDocumentMaterial.alphaMode || fiberDocumentMaterial.alphaMode === 'OPAQUE', '幾何細髮絲不應依賴透明排序');
const scalpDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_Hair_Scalp');
assert(scalpDocumentMaterial, '缺少頭皮底層材質');
assert.equal(scalpDocumentMaterial.alphaMode, 'BLEND', 'v194 必須保留通過目視的柔和頭皮漸層');
const hairlineDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_HairlineRoots_v188');
assert(hairlineDocumentMaterial?.pbrMetallicRoughness?.baseColorTexture, '髮際線根髮缺少自有 atlas');
assert.equal(hairlineDocumentMaterial.alphaMode, 'BLEND', '髮際線根髮透明模式遺失');
const corneaDocumentMaterial = document.materials.find(material => material.name === 'Aevrynd_Eye_Cornea');
assert(corneaDocumentMaterial, '缺少可攜式角膜材質');
assert.equal(corneaDocumentMaterial.alphaMode, 'BLEND', '角膜透明模式遺失');
assert(Math.abs(corneaDocumentMaterial.pbrMetallicRoughness.baseColorFactor[3] - .04) < .001, '角膜透明度不是 v204 驗證值');
assert.equal(corneaDocumentMaterial.extensions?.KHR_materials_transmission?.transmissionFactor, 1, '角膜 transmission 遺失');
assert(Math.abs(corneaDocumentMaterial.extensions?.KHR_materials_ior?.ior - 1.376) < .001, '角膜 IOR 遺失');
const browDocumentMaterials = document.materials.filter(material => material.name.startsWith('Aevrynd_Brow_Hair_v39_'));
assert.equal(browDocumentMaterials.length, 2, '眉毛深色／暖色毛束材質分層缺失');
for (const material of browDocumentMaterials) {
  assert.equal(material.alphaMode, 'BLEND', `${material.name} 透明模式遺失`);
  assert(Math.abs(material.pbrMetallicRoughness.baseColorFactor[3] - .55) < .001, `${material.name} 透明度不是 v206 驗證值`);
}

const gltf = await loadGeometry(bytes);
gltf.scene.updateMatrixWorld(true);
gltf.scene.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
assert.equal(gltf.animations.length, 1, '變形驗證動畫缺失');

const requiredObjects = [
  'AevryndFemaleBodyBaseV118', 'AevryndFemaleRig', 'HairScalp',
  'HairCoverageTiles_v246', 'HairSilhouetteCards_v246', 'HairDetailFibers_v246',
  'HairlineNaturalCards_v214',
  'Clothing_Bandeau_v160', 'Clothing_BandeauBinding_v162', 'Clothing_BodyFitShorts_v135',
  'Eye_L_Cornea', 'Eye_R_Cornea', 'Eye_L_TearMeniscus', 'Eye_R_TearMeniscus',
  'Brow_L', 'Brow_R', 'Brow_L_Density', 'Brow_R_Density',
];
for (const name of requiredObjects) assert(gltf.scene.getObjectByName(name), `缺少必要分層 ${name}`);

let vertices = 0;
let triangles = 0;
let skinnedMeshes = 0;
let invalidNormals = 0;
const skinnedNames = [];
gltf.scene.traverse(node => {
  if (!node.isMesh) return;
  const geometry = node.geometry;
  const positions = geometry.attributes.position;
  const normals = geometry.attributes.normal;
  assert(positions && normals && geometry.index, `${node.name} 幾何屬性不完整`);
  vertices += positions.count;
  triangles += geometry.index.count / 3;
  for (const value of positions.array) assert(Number.isFinite(value), `${node.name} 含無效座標`);
  for (let index = 0; index < normals.count; index += 31) {
    const length = Math.hypot(normals.getX(index), normals.getY(index), normals.getZ(index));
    if (Math.abs(length - 1) > .035) invalidNormals++;
  }
  if (node.isSkinnedMesh) {
    skinnedMeshes++;
    skinnedNames.push(node.name);
    const weights = geometry.attributes.skinWeight;
    const joints = geometry.attributes.skinIndex;
    assert(weights && joints, `${node.name} 缺少蒙皮資料`);
    for (let index = 0; index < weights.count; index += 17) {
      const sum = weights.getX(index) + weights.getY(index) + weights.getZ(index) + weights.getW(index);
      assert(Math.abs(sum - 1) < .015, `${node.name} 蒙皮權重和為 ${sum}`);
      for (const joint of [joints.getX(index), joints.getY(index), joints.getZ(index), joints.getW(index)]) {
        assert(joint < node.skeleton.bones.length, `${node.name} 骨骼索引越界`);
      }
    }
  }
});
assert.equal(invalidNormals, 0, '存在未正規化法線');
assert(skinnedMeshes >= 4, `蒙皮分層數量異常 ${skinnedMeshes}: ${skinnedNames.join(', ')}`);
assert(vertices < 150000, '候選頂點超過即時預算');
assert(triangles < 200000, '候選三角形超過即時預算');

function meshWithMaterial(root, materialName) {
  let found = null;
  root.traverse(node => {
    if (found || !node.isMesh) return;
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    if (materials.some(material => material?.name === materialName)) found = node;
  });
  return found;
}
const body = meshWithMaterial(gltf.scene.getObjectByName('AevryndFemaleBodyBaseV118'), 'Aevrynd_Skin_Baked_v248');
assert(body, '身體分層內找不到 v248 烘焙皮膚 mesh');
assert(body?.geometry.attributes.uv1, '身體缺少第二 atlas UV');
const coverageHair = meshWithMaterial(gltf.scene.getObjectByName('HairCoverageTiles_v246'), 'Aevrynd_HairCards_v166');
const silhouetteHair = meshWithMaterial(gltf.scene.getObjectByName('HairSilhouetteCards_v246'), 'Aevrynd_HairCards_v166');
assert(coverageHair, '髮型分層內找不到 v246 coverage 髮卡 mesh');
assert(silhouetteHair, '髮型分層內找不到 v246 silhouette 髮卡 mesh');
assert(coverageHair.material.transparent, 'Three.js 未保留 coverage 髮卡透明度');
assert(silhouetteHair.material.transparent, 'Three.js 未保留 silhouette 髮卡透明度');
const detailFibers = meshWithMaterial(gltf.scene.getObjectByName('HairDetailFibers_v246'), 'Aevrynd_HairDetailFibers_v246');
assert(detailFibers, '髮型分層內找不到 v246 幾何細髮絲 mesh');
assert(!detailFibers.material.transparent, '幾何細髮絲錯誤啟用透明排序');

const bounds = new THREE.Box3().setFromObject(gltf.scene, true);
const size = bounds.getSize(new THREE.Vector3());
assert(size.y > 1.70 && size.y < 1.75, `人物身高異常 ${size.y}`);
assert(size.x > .86 && size.x < .92, `人物寬度異常 ${size.x}`);

console.log(JSON.stringify({
  passed: true,
  downloadMB: +(bytes.length / 1e6).toFixed(3),
  images: document.images.length,
  materials: document.materials.length,
  vertices,
  triangles,
  skinnedMeshes,
  skinnedNames,
  animation: gltf.animations[0].name,
  size: size.toArray(),
  skinUV: 1,
  hairAlphaMode: hairDocumentMaterial.alphaMode,
  scalpAlphaMode: scalpDocumentMaterial.alphaMode,
  hairlineAlphaMode: hairlineDocumentMaterial.alphaMode,
  corneaAlphaMode: corneaDocumentMaterial.alphaMode,
  browAlphaModes: browDocumentMaterials.map(material => material.alphaMode),
}, null, 2));









