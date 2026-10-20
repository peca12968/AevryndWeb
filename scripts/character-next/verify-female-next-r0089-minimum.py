"""Minimum independent source readback after visual rejection.
Native preservation, finite saved curves, explicit expected output and texture
availability only. No broad motion/contact/runtime acceptance for failed art.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0089-posterior-growth';S=R/'engine/assets/characters/female-next/source'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('r89min_source','build-female-next-r0081-editable-curly.py');q=m.q;native=module('r89min_native','verify-female-next-r0076-crowns.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def prepare(p):
 bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def cap(o):
 d=o.data;h=hashlib.sha256(q.arr(d.vertices,'co',len(d.vertices),3).tobytes());h.update(q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4').tobytes())
 for uv in d.uv_layers:h.update(q.arr(uv.data,'uv',len(d.loops),2).tobytes())
 return h.hexdigest()
def curveNative(o):
 return hashlib.sha256(q.arr(o.data.position_data,'vector',len(o.data.position_data),3).tobytes()+np.array([c.points_length for c in o.data.curves],'i4').tobytes()).hexdigest()
def main():
 tick=time.time();src=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend';assert sha(src)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';prepare(src);names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:native.signature(bpy.data.objects[n]) for n in names};dent={n:cap(bpy.data.objects[n]) for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};nativeHair=curveNative(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']);growthSig=cap(bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']);otherCurves={n:q.hair(bpy.data.objects[n]).copy() for n in ('AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')};mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users>0 or x.use_fake_user)};purgeable=[x.name for x in bpy.data.materials if x.use_nodes and x.users==0 and not x.use_fake_user];save('readback-material-scope.json',{'comparedReferencedOrFakeUserMaterialNames':list(mats),'sourceZeroUserUnpinnedMaterials':purgeable,'reason':'Blender omits zero-user, no-fake-user datablocks during save. They are not displayed or referenced source materials; no geometry/colour/tolerance criterion changed.'});lights=m.m.q.lights();rows={}
 for tag,npz,key,obj in [('a','a-posterior-bundle-lineage.npz','authoredEvaluatedWorld','AFN81_EDITABLE_CURLY_GUIDES'),('b','b-parted-bob-lineage.npz','actualChildWorld','AFN89_PARTED_BOB_RENDER_CURVES'),('c','c-authored-braid-lineage.npz','actualNeutralWorld','AFN89_PUBLISHER_AUTHORED_BRAID_GUIDES')]:
  p=E/(tag+'-build-summary.json')
  if not p.exists():continue
  ref=json.loads(p.read_text(encoding='utf-8-sig'));out=Path(ref['output']);assert sha(out)==ref['outputSha256'];prepare(out);assert {n:native.signature(bpy.data.objects[n]) for n in names}==sig;assert {n:cap(bpy.data.objects[n]) for n in dent}==dent;assert curveNative(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])==nativeHair;assert cap(bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE'])==growthSig;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert m.m.q.lights()==lights
  for n,P in otherCurves.items():assert np.array_equal(q.hair(bpy.data.objects[n]),P),n
  z=np.load(E/npz);o=bpy.data.objects[obj];P=q.hair(o);assert np.isfinite(P).all() and P.shape==z[key].shape;err=float(np.linalg.norm(P-z[key],axis=1).max());assert err<2e-6;d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in d.curves]);radius=q.arr(d.attributes['radius'].data,'value',len(P));assert np.isfinite(radius).all() and radius.min()>0
  expectedCounts=z['actualCounts' if tag=='c' else 'sourceCounts'];expectedRadii=z['actualRadii' if tag=='c' else 'sourceRadii'];assert np.array_equal(counts,expectedCounts) and np.array_equal(radius,expectedRadii)
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(textures)==15 and not bpy.data.libraries
  row={'status':'PASS_MINIMUM_SAVED_NEUTRAL_READBACK_ONLY','source':str(out),'sha256':sha(out),'actualCurves':len(counts),'actualPoints':len(P),'savedOutputMaximumWorldErrorM':err,'actualCountsAndRadiiMatchLineage':True,'originalNativeCagesKeysUVWeightsDriversDentalCurlyGuidesAndCapPreserved':True,'originalBrownMaterialTreesAndLightsPreserved':True,'originalEvaluatedBrowsLashesPreservedAtNeutral':True,'externalTextures':textures,'noNewContactMotionNaturalDynamicsOrRuntimeAcceptance':True};save(tag+'-minimum-source-readback.json',row);rows[tag]=row;print('R89_MINIMUM_SAVED_READBACK',tag,len(counts),err,flush=True)
 save('minimum-source-readback.json',{'status':'PASS_SCOPED_REJECTED_SOURCES_ONLY','candidates':rows,'seconds':time.time()-tick,'noBroadTestsAfterVisualRejection':True})
if __name__=='__main__':main()
