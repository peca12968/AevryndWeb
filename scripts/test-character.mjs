import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { classifyMaterial, layerDefinitions, refineMaterial } from '../src/character-materials.js';

const asset = await readFile(new URL('../public/assets/character-female-refined.glb', import.meta.url));
const downloadBytes = asset.length;
assert(downloadBytes < 25 * 1024 * 1024, '模型超過单一網站資產大小上限');
assert.equal(asset.readUInt32LE(8), asset.length);
const jsonLength = asset.readUInt32LE(12);
const json = JSON.parse(asset.subarray(20, 20 + jsonLength).toString());
const binary = asset.subarray(28 + jsonLength);
assert(json.extensionsRequired.includes('EXT_meshopt_compression'));
assert(json.images.length > 10);
for (const image of json.images) {
  const view = json.bufferViews[image.bufferView];
  assert(view.byteLength > 0 && view.byteOffset + view.byteLength <= binary.length);
}

// CPU 測試仍用正式 GLTFLoader 與解碼器，只略過需要瀏覽器的圖片解碼。
function removeTextures(object) {
  if (!object || typeof object !== 'object') return;
  for (const key of Object.keys(object)) {
    if (key.endsWith('Texture')) delete object[key];
    else removeTextures(object[key]);
  }
}
async function loadGeometry(bytes) {
const length = bytes.readUInt32LE(12);
const data = JSON.parse(bytes.subarray(20, 20 + length).toString());
const binary = bytes.subarray(28 + length);
removeTextures(data.materials);
delete data.images;
delete data.textures;
const packed = packDocument(data, binary);
return new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(packed.buffer.slice(packed.byteOffset, packed.byteOffset + packed.byteLength), '');
}
function packDocument(source, binary) {
const data = structuredClone(source);
delete data.buffers[0].uri;
const encoded = Buffer.from(JSON.stringify(data));
const padding = (4 - encoded.length % 4) % 4;
const header = Buffer.alloc(20);
header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4);
header.writeUInt32LE(28 + encoded.length + padding + binary.length, 8);
header.writeUInt32LE(encoded.length + padding, 12); header.writeUInt32LE(0x4e4f534a, 16);
const binHeader = Buffer.alloc(8); binHeader.writeUInt32LE(binary.length); binHeader.writeUInt32LE(0x004e4942, 4);
return Buffer.concat([header, encoded, Buffer.alloc(padding, 32), binHeader, binary]);
}
const gltf = await loadGeometry(asset);
gltf.scene.updateMatrixWorld(true);
gltf.scene.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
const layers = new Set();
let vertices = 0, triangles = 0, morphMeshes = 0;
gltf.scene.traverse(node => {
  if (!node.isMesh) return;
  const geometry = node.geometry;
  const positions = geometry.attributes.position;
  vertices += positions.count; triangles += geometry.index.count / 3;
  for (const value of positions.array) assert(Number.isFinite(value));
  const normals = geometry.attributes.normal;
  for (let i = 0; i < normals.count; i++) {
    const length = Math.hypot(normals.getX(i), normals.getY(i), normals.getZ(i));
    assert(Math.abs(length - 1) < .03, `法線長度異常 ${length}`);
  }
  for (const index of geometry.index.array) assert(index < positions.count);
  const materials = Array.isArray(node.material) ? node.material : [node.material];
  for (const source of materials) {
    const layer = classifyMaterial(source.name); layers.add(layer);
    const material = refineMaterial(source, 8);
    assert(material.isMeshPhysicalMaterial);
    assert('PHYSICAL' in material.defines, `${source.name} 缺少實體材質定義`);
    assert.equal(material.alphaTest, source.alphaTest);
    if (material.anisotropy > 0) assert(geometry.attributes.uv, `${source.name} 需要髮絲切線 UV`);
    if (layer === 'skin') {
      const shader = { fragmentShader: '#include <lights_physical_pars_fragment>' };
      material.onBeforeCompile(shader);
      assert(shader.fragmentShader.includes('vec3 skinDiffuse'));
      assert(!shader.fragmentShader.includes('#include <lights_physical_pars_fragment>'));
    }
  }
  if (node.isSkinnedMesh) {
    const weights = geometry.attributes.skinWeight, joints = geometry.attributes.skinIndex;
    for (let i = 0; i < weights.count; i++) {
      const sum = weights.getX(i) + weights.getY(i) + weights.getZ(i) + weights.getW(i);
      assert(Math.abs(sum - 1) < .015, `蒙皮權重 ${sum}`);
      for (const k of [joints.getX(i), joints.getY(i), joints.getZ(i), joints.getW(i)]) assert(k < node.skeleton.bones.length);
    }
  }
  if (node.morphTargetDictionary) {
    assert(node.morphTargetInfluences.every(value => value === 0), '初始塑形必須為中性');
    morphMeshes++;
    assert.equal(Object.keys(node.morphTargetDictionary).length, 10);
    assert.equal(geometry.morphAttributes.position.length, 10);
    for (const attribute of geometry.morphAttributes.position) {
      assert.equal(attribute.count, positions.count);
      for (const value of attribute.array) assert(Number.isFinite(value));
    }
  }
});
for (const layer of layerDefinitions) assert(layers.has(layer.id), `${layer.id} 分層缺少網格`);
assert(morphMeshes >= 1);
const bounds = new THREE.Box3().setFromObject(gltf.scene, true);
const size = bounds.getSize(new THREE.Vector3());
assert(size.y > 1.70 && size.y < 1.75, `人物身高異常 ${size.y}`);
assert(size.x > .9 && size.x < 1.15, `人物寬度異常 ${size.x}`);
let minimumBackClearance = Infinity;
for (const y of [1.28, 1.30, 1.32, 1.35]) {
  const ray = new THREE.Raycaster(new THREE.Vector3(0, y, -.4), new THREE.Vector3(0, 0, 1));
  const jacket = ray.intersectObject(gltf.scene.getObjectByName('Jacket'), true)[0];
  const inner = ray.intersectObject(gltf.scene.getObjectByName('InnerTop'), true)[0];
  assert(jacket && inner, '背部衣物取樣缺少曲面');
  minimumBackClearance = Math.min(minimumBackClearance, inner.distance - jacket.distance);
}
assert(minimumBackClearance > .002, '外套與內搭背部間距不足 2mm');

const body = gltf.scene.getObjectByName('Body');
let maxMorphDisplacement = 0;
body.traverse(node => {
  if (!node.morphTargetDictionary) return;
  const key = node.morphTargetDictionary.chinLength_maximum;
  for (let i = 0; i < node.geometry.attributes.position.count; i += 19) {
    node.morphTargetInfluences[key] = 0;
    const before = node.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(node.matrixWorld);
    node.morphTargetInfluences[key] = 1;
    const after = node.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(node.matrixWorld);
    maxMorphDisplacement = Math.max(maxMorphDisplacement, before.distanceTo(after));
  }
  node.morphTargetInfluences[key] = 0;
});
assert(maxMorphDisplacement > .001 && maxMorphDisplacement < .1, `塑形變位異常 ${maxMorphDisplacement}`);
let maxPackingError = null;
if (process.argv[2]) {
  const unpacked = await loadGeometry(await readFile(process.argv[2]));
  unpacked.scene.updateMatrixWorld(true);
  unpacked.scene.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
  const grid = new Map();
  const cell = .00025;
  const key = (x, y, z) => `${x},${y},${z}`;
  const point = new THREE.Vector3();
  unpacked.scene.getObjectByName('Body').traverse(node => {
    if (!node.isMesh) return;
    for (let i = 0; i < node.geometry.attributes.position.count; i++) {
      node.getVertexPosition(i, point).applyMatrix4(node.matrixWorld);
      const id = key(Math.floor(point.x / cell), Math.floor(point.y / cell), Math.floor(point.z / cell));
      if (!grid.has(id)) grid.set(id, []);
      grid.get(id).push(point.clone());
    }
  });
  maxPackingError = 0;
  body.traverse(node => {
    if (!node.isMesh) return;
    for (let i = 0; i < node.geometry.attributes.position.count; i += 7) {
      node.getVertexPosition(i, point).applyMatrix4(node.matrixWorld);
      const cx = Math.floor(point.x / cell), cy = Math.floor(point.y / cell), cz = Math.floor(point.z / cell);
      let nearest = Infinity;
      for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
        for (const candidate of grid.get(key(cx + x, cy + y, cz + z)) ?? []) nearest = Math.min(nearest, candidate.distanceTo(point));
      }
      if (!Number.isFinite(nearest)) {
        for (const bucket of grid.values()) for (const candidate of bucket) nearest = Math.min(nearest, candidate.distanceTo(point));
        console.log('packing-outlier', point.toArray(), nearest);
        assert(nearest < .0002, '壓縮幾何與來源差異');
      }
      maxPackingError = Math.max(maxPackingError, nearest);
    }
  });
  assert(maxPackingError < .0002, `壓縮造成超過 0.2mm 的身體變形：${maxPackingError}`);
}
console.log(JSON.stringify({ passed: true, downloadMB: +(downloadBytes / 1e6).toFixed(2), layers: layers.size, vertices, triangles, morphMeshes, height: size.y, maxMorphDisplacement, maxPackingError, minimumBackClearance }, null, 2));
