import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

// CPU 測試仍用正式 GLTFLoader 與解碼器，只略過需要瀏覽器的圖片解碼。
function removeTextures(object) {
  if (!object || typeof object !== 'object') return;
  for (const key of Object.keys(object)) {
    if (key.endsWith('Texture')) delete object[key];
    else removeTextures(object[key]);
  }
}
export async function loadGeometry(bytes) {
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
