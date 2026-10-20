"""Minimum independent reopening of rejected sparse-guide studies only.
No contact, motion, complete-groom realism or runtime qualification.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0090-native-scalp-groom';S=R/'engine/assets/characters/female-next/source'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r90minsource','build-female-next-r0081-editable-curly.py');q=m.q;v=mod('r90minnative','verify-female-next-r0076-crowns.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cap_signature(o):
 d=o.data;h=hashlib.sha256(q.arr(d.vertices,'co',len(d.vertices),3).tobytes());h.update(q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4').tobytes())
 for uv in d.uv_layers:h.update(q.arr(uv.data,'uv',len(d.loops),2).tobytes())
 return h.hexdigest()
def hair_signature(o):return hashlib.sha256(q.arr(o.data.position_data,'vector',len(o.data.position_data),3).tobytes()).hexdigest()
def prepare(p):bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def main():
 tick=time.time();src=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend';assert sha(src)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';prepare(src);names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:v.signature(bpy.data.objects[n]) for n in names};oldHair=hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']);oldCap=cap_signature(bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']);teeth={n:cap_signature(bpy.data.objects[n]) for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};facial={n:q.hair(bpy.data.objects[n]).copy() for n in ('AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')};mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};lights=m.m.q.lights();line=np.load(E/'a-guide-lineage.npz');rows=[]
 for summary in ('a-guide-invisible-build-summary.json','a-guide-build-summary.json'):
  ref=json.loads((E/summary).read_text());out=Path(ref['output']);assert sha(out)==ref['outputSha256'];prepare(out);assert {n:v.signature(bpy.data.objects[n]) for n in names}==sig;assert hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])==oldHair;assert cap_signature(bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE'])==oldCap;assert {n:cap_signature(bpy.data.objects[n]) for n in teeth}==teeth;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert lights==m.m.q.lights()
  for n,P in facial.items():assert np.array_equal(q.hair(bpy.data.objects[n]),P)
  guide=bpy.data.objects[ref['guideObject']];A=np.array(guide.matrix_world);P=q.arr(guide.data.vertices,'co',len(guide.data.vertices),3).astype('f8')@A[:3,:3].T+A[:3,3];error=float(np.linalg.norm(P-line['guidesWorld'].reshape(-1,3),axis=1).max());assert error<2e-6 and len(guide.data.vertices)==6144 and len(guide.data.edges)==6048
  curve=bpy.data.objects[ref['renderObject']];C=np.array([p.co[:3] for sp in curve.data.splines for p in sp.points]);B=np.array(curve.matrix_world);C=C@B[:3,:3].T+B[:3,3];assert np.isfinite(C).all() and len(curve.data.splines)==96;curveError=float(np.linalg.norm(C-P,axis=1).max());assert curveError<2e-6 and all(sp.type=='POLY' and len(sp.points)==64 for sp in curve.data.splines)
  scalp=bpy.data.objects[ref['scalpObject']];D=np.array(scalp.matrix_world);capP=q.arr(scalp.data.vertices,'co',len(scalp.data.vertices),3).astype('f8')@D[:3,:3].T+D[:3,3];capError=float(np.linalg.norm(capP-line['scalpWorld'],axis=1).max());assert capError<2e-6;ids=q.arr(scalp.data.attributes['AFN90_ActualBodyVertex'].data,'value',len(capP),dtype='i4');assert np.array_equal(ids,line['scalpActualBodyVertexIDs']);assert len(scalp.data.polygons)==15845 and len(scalp.data.uv_layers)==1;assert np.isfinite(q.arr(scalp.data.uv_layers[0].data,'uv',len(scalp.data.loops),2)).all()
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(textures)==15 and not bpy.data.libraries;rows.append({'source':str(out),'sha256':sha(out),'guideCages':96,'guidePoints':6144,'guideEdges':6048,'savedGuideMaximumWorldErrorM':error,'diagnosticCurveVsCageMaximumWorldErrorM':curveError,'scalpVertices':len(capP),'scalpTriangles':15845,'scalpSavedWorldMaximumErrorM':capError,'actualBodyVertexIDsExact':True,'originalCagesKeysUVWeightsDriversTeethHairGuideCapAndMaterialsLightsPreserved':True,'evaluatedBrowsLashesExactAtNeutral':True,'externalTextures':textures,'physicalFolliclesDenseHairMotionContactAndRuntimeAccepted':False});print('R90_SAVED_GUIDE_READBACK',summary,error,capError,flush=True)
 result={'status':'PASS_MINIMUM_REJECTED_STATIC_GUIDE_AND_SCALP_SOURCE_READBACK_ONLY','sources':rows,'sourceMaterialScope':'All originally referenced or fake-user materials; zero-user unpinned material datablocks may be omitted on save. One new opaque diagnostic material is only on guide bevel curves.','noNewCompleteCharacterCapabilityOrRealism':True,'seconds':time.time()-tick};(E/'minimum-saved-guide-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
