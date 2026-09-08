import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadGeometry} from './load-character.mjs';

const fullPath=process.argv[2]||'.character-build/aevrynd-female-authoring-v41.glb';
const lodPath=process.argv[3]||'.character-build/aevrynd-female-authoring-v41-lod1.glb';
async function inspect(path){
 const bytes=await readFile(path);const jsonLength=bytes.readUInt32LE(12);const text=bytes.subarray(20,20+jsonLength).toString();const doc=JSON.parse(text);const gltf=await loadGeometry(bytes);const found=new Map();const bones=[];
 gltf.scene.traverse(o=>{found.set(o.name,o);if(o.isBone)bones.push(o.name);});
 for(const name of ['HairClumpsLarge','HairClumpsMediumCards']){const o=found.get(name);assert(o?.isMesh,`${path}: ${name} missing`);assert(o.geometry.getAttribute('position').count>9000,`${path}: ${name} density too low`);assert(o.geometry.getAttribute('uv'),`${path}: ${name} UV missing`);}
 const mat=doc.materials.find(x=>x.name==='Aevrynd_Hair_Clumps_v41');assert.equal(mat?.alphaMode,'BLEND',`${path}: groom alpha blend missing`);assert(mat?.pbrMetallicRoughness?.baseColorTexture,`${path}: groom texture missing`);
 assert.equal(new Set(bones).size,21,`${path}: bone count`);assert.equal(gltf.animations.length,1,`${path}: animation missing`);assert(!/MetaHuman|Unreal Engine|Epic Games/i.test(text),`${path}: prohibited dependency`);return bytes.length;
}
const full=await inspect(fullPath),lod=await inspect(lodPath);assert(full<8*1024*1024,`full exceeds 8 MiB: ${full}`);assert(lod<=full*.80,'LOD1 reduction below 20%');
console.log(`female-groom-v41: full ${(full/1048576).toFixed(2)} MiB, LOD1 ${(lod/1048576).toFixed(2)} MiB, ${((1-lod/full)*100).toFixed(1)}% smaller, 2 hierarchical card layers present`);
