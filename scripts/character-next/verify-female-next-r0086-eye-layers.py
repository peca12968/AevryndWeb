"""Minimum saved-source readback after visible iris regression; no broad tests."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0086-eye-layers'
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
k=mod('r86build','build-female-next-r0086-eye-layers.py');m=k.m;q=m.q;v=mod('r86native','verify-female-next-r0076-crowns.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();ref=json.loads((E/'a-build-summary.json').read_text());src=Path(ref['source']);out=Path(ref['output']);assert sha(src)==ref['sourceSha256'];assert sha(out)==ref['outputSha256']
 bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();names=m.rig.native_names();signatures={n:v.signature(bpy.data.objects[n]) for n in names};hn=('AFN81_EDITABLE_CURLY_GUIDES','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES');hair={n:q.hair(bpy.data.objects[n]).copy() for n in hn};unchanged=('AFN74_SKIN_AND_EXISTING_OCULAR_LINING','AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID');geometry={n:q.geom(bpy.data.objects[n])[1].copy() for n in unchanged};mats={a.name:m.rig.k.f.v.v32.material_signature(a) for a in bpy.data.materials if a.use_nodes};lights=m.m.q.lights()
 bpy.ops.wm.open_mainfile(filepath=str(out));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==signatures
 for n in hn:assert np.array_equal(q.hair(bpy.data.objects[n]),hair[n]),n
 for n in unchanged:assert np.array_equal(q.geom(bpy.data.objects[n])[1],geometry[n]),n
 assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert m.m.q.lights()==lights
 guards=[]
 for name in names[:4]:
  rows=[a for a in ref['layers'] if a['source']==name];source=bpy.data.objects[name];assert source.hide_render and source.hide_get();guards.append(k.validate(source,rows));sd,_=q.geom(source);sourceLoops=q.arr(sd.loops,'vertex_index',len(sd.loops),dtype='i4')
  for row in rows:
   d,p=q.geom(bpy.data.objects[row['object']]);pi=q.arr(d.attributes['AFN86_SourcePointID'].data,'value',len(p),dtype='i4');ci=q.arr(d.attributes['AFN86_SourceCornerID'].data,'value',len(d.loops),dtype='i4');li=q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4');assert np.array_equal(pi[li],sourceLoops[ci]),row['object']
 ctrl=bpy.data.objects[ref['controls']];assert all(ctrl[a['visibilityProperty']] for a in ref['layers']);textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();textures.append({'relative':im.filepath,'sha256':sha(p)})
 assert len(textures)==15 and not bpy.data.libraries;assert sha(out)==ref['outputSha256']
 result={'status':'PASS_MINIMUM_REJECTED_NEUTRAL_SOURCE_READBACK_ONLY','source':str(out),'sha256':ref['outputSha256'],'originalNativeGeometryUVKeysWeightsDriversMaterialIndicesExact':True,'originalMaterialTreesAndLightsExact':True,'originalEvaluatedSkinDentalHairBrowsLashesExactAtNeutral':True,'derivedNeutralPartitions':guards,'sourcePointFaceCornerUVNormalsAndPolygonLoopsCorrespond':True,'eachSourceFaceExactlyOnce':True,'externalTextures':textures,'savedSourceUnmodified':True,'appearance':'REJECT_IRIS_BROWN_DETAIL_LOSS_BLACK_WHITE_REGRESSION','causeNotIsolated':'Geometry/UV and captured normals correspondence alone do not prove material attribute/texture evaluation or renderer shading equivalence. No exact shader-cause claim.','independentToggleRestoreOrPosedMotionQualified':False,'newOpticalSolidAnatomyFiniteContactNaturalDynamicsRuntimeQualified':False,'broadTestsStoppedAfterVisualRejection':True,'seconds':time.time()-tick}
 (E/'minimum-source-readback.json').write_text(json.dumps(result,indent=2)+'\n');print('R86_MINIMUM_REJECTED_READBACK_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
