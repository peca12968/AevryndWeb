import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadGeometry } from './load-character.mjs';

const fullPath=process.argv[2]||'.character-build/aevrynd-female-authoring-v40.glb';
const lodPath=process.argv[3]||'.character-build/aevrynd-female-authoring-v40-lod1.glb';
const expected={Lip_Upper:[195,256],Lip_Lower:[195,256],Mouth_WetLine:[130,128],Mouth_OralCavity:[193,336],Mouth_UpperTeeth:[432,840],Mouth_Tongue:[170,336]};

async function inspect(path){
  const bytes=await readFile(path);const jsonLength=bytes.readUInt32LE(12);const text=bytes.subarray(20,20+jsonLength).toString();const doc=JSON.parse(text);const gltf=await loadGeometry(bytes);
  const found=new Map();const bones=[];gltf.scene.traverse(o=>{found.set(o.name,o);if(o.isBone)bones.push(o.name);});
  for(const [name,[vertices,triangles]] of Object.entries(expected)){
    const obj=found.get(name);assert(obj?.isMesh,`${path}: ${name} missing`);assert.equal(obj.geometry.getAttribute('position').count,vertices,`${path}: ${name} vertices`);assert.equal(obj.geometry.getIndex().count/3,triangles,`${path}: ${name} triangles`);
  }
  assert.equal(new Set(bones).size,21,`${path}: bone count`);assert.equal(gltf.animations.length,1,`${path}: animation missing`);assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text),`${path}: prohibited dependency`);return bytes.length;
}
const full=await inspect(fullPath),lod=await inspect(lodPath);assert(full<8*1024*1024,`full exceeds 8 MiB: ${full}`);assert(lod<=full*.80,'LOD1 reduction below 20%');
console.log(`female-mouth-v40: full ${(full/1048576).toFixed(2)} MiB, LOD1 ${(lod/1048576).toFixed(2)} MiB, ${((1-lod/full)*100).toFixed(1)}% smaller, 6 mouth layers present`);
