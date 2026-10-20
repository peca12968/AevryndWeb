"""Minimum saved-data readback of visually rejected r80; no contact expansion."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0080-cone-offsets'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module('preserve80','verify-female-next-r0076-crowns.py');q=v.q;m=module('preserve80render','build-female-next-r0074-oral-controls.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();ref=q.read(E/'a-build-summary.json');assert sha(Path(ref['source']))==ref['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=ref['source']);bpy.context.scene.frame_set(1);names=list(q.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());native={n:v.signature(bpy.data.objects[n]) for n in names};mats={n.name:m.m.k.f.v.v32.material_signature(n) for n in bpy.data.materials if n.use_nodes};lights=m.q.lights();fly=q.hair(bpy.data.objects['AFN68_FLYAWAY_RENDER_CURVES']).copy();dental={n:q.arr(bpy.data.objects[n].data.vertices,'co',len(bpy.data.objects[n].data.vertices),3).copy() for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];A=np.array(o.matrix_world);attrs={}
 for at in o.data.attributes:
  if at.name.startswith('AFN69_'):attrs[at.name]=q.arr(at.data,'vector' if at.data_type=='FLOAT_VECTOR' else 'value',len(at.data),3 if at.data_type=='FLOAT_VECTOR' else 1,'f4' if at.data_type=='FLOAT_VECTOR' else 'i4').copy()
 assert sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==native;assert {n:m.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert lights==m.q.lights();assert np.array_equal(fly,q.hair(bpy.data.objects['AFN68_FLYAWAY_RENDER_CURVES']))
 for n,p in dental.items():assert np.array_equal(q.arr(bpy.data.objects[n].data.vertices,'co',len(p),3),p)
 o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];z=np.load(E/'a-lineage.npz');P=q.arr(o.data.position_data,'vector',len(o.data.position_data),3);assert np.isfinite(P).all() and np.array_equal(A,np.array(o.matrix_world));assert np.array_equal(q.arr(o.data.attributes['radius'].data,'value',len(P)),z['actualNativeRadii']);assert np.array_equal(np.array([c.points_length for c in o.data.curves]),z['childCounts'])
 for name,val in attrs.items():
  at=o.data.attributes[name];actual=q.arr(at.data,'vector' if at.data_type=='FLOAT_VECTOR' else 'value',len(at.data),3 if at.data_type=='FLOAT_VECTOR' else 1,'f4' if at.data_type=='FLOAT_VECTOR' else 'i4');assert np.array_equal(actual,val[z['curveParent']]),name
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();textures.append({'relative':im.filepath,'sha256':sha(p)})
 assert len(textures)==15 and not bpy.data.libraries
 result={'status':'PASS_REJECTED_SOURCE_DATA_PRESERVATION_ONLY','source':ref['output'],'sha256':ref['outputSha256'],'allFiveNativeCagesKeysUVWeightsDriversExact':True,'allOriginalMaterialsLightDentalAndNeutralFlyawayExact':True,'originalObjectMatrixAndRootFrameAttributeLineageExact':True,'actualCurves':len(o.data.curves),'actualPoints':len(P),'finiteSavedRadiiAndPositions':True,'contactConstructionNotIndependentlyQualifiedAfterVisualRejection':True,'headMotionNaturalDynamicsAndRuntimeNotQualified':True,'externalTextures':textures,'seconds':time.time()-tick};(E/'a-rejected-source-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R80_REJECTED_SOURCE_READBACK',time.time()-tick,flush=True)
if __name__=='__main__':main()
