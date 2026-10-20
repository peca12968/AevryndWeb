"""Minimum independent reopening of visually rejected complete fibre sources.
No broad contact/motion/runtime certification after appearance rejection.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r91verifyhelpers',Path(__file__).with_name('verify-female-next-r0090-rain-and-flow.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);m=h.m;q=h.q;native=h.native;helpers=h.helpers
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend');names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];base={n:native.signature(bpy.data.objects[n]) for n in names};caps={n:helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']};old=helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']);facial={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};lights=m.m.q.lights();rig=h.rig_signature();texts=set(bpy.data.texts.keys());rows=[]
 for tag,lineage in [('a','actual-fibre-lineage.npz'),('b','b-actual-fibre-lineage.npz')]:
  ref=json.loads((E/(tag+'-build-summary.json')).read_text(encoding='utf8'));path=Path(ref['output']);assert sha(path)==ref['outputSha256'];h.open_file(path);assert {n:native.signature(bpy.data.objects[n]) for n in names}==base;assert {n:helpers.cap_signature(bpy.data.objects[n]) for n in caps}==caps;assert helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])==old;assert h.rig_signature()==rig;assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert lights==m.m.q.lights();assert set(bpy.data.texts.keys())==texts and not bpy.data.libraries
  for n,P in facial.items():assert np.array_equal(q.hair(bpy.data.objects[n]),P)
  z=np.load(E/lineage);o=bpy.data.objects[ref['curveObject']];P=q.hair(o);wanted=z['world'].reshape(-1,3);err=float(np.linalg.norm(P-wanted,axis=1).max());assert err<2e-6 and np.isfinite(P).all();counts=np.array([c.points_length for c in o.data.curves]);assert len(counts)==21908 and np.all(counts==64) and np.array_equal(counts,z['counts']);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;radius=q.arr(d.attributes['radius'].data,'value',len(P))*np.linalg.norm(np.array(o.matrix_world)[:3,0]);assert np.isfinite(radius).all();radiusError=float(np.max(abs(radius-z['radiusWorld'].ravel())));assert radiusError<1e-10;assert not o.modifiers and not o.constraints and not o.parent and o.data.surface is None
  external=[];packed=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();external.append({'relative':im.filepath,'sha256':sha(p)})
   elif im.name.startswith('TEX-rain_hair_'):
    assert tag=='a' and im.packed_file;packed.append({'name':im.name,'sha256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest()})
  assert len(external)==15 and len(packed)==(3 if tag=='a' else 0)
  if tag=='a':
   cage=bpy.data.objects[ref['sectionCage']];profiles=np.load(E/'section-profiles.npz');wantedC=np.concatenate([(profiles[k][:,None,:]+profiles[k[:-len('_centres')]+'_rings']).reshape(-1,3) for k in profiles.files if k.endswith('_centres')]);C=h.world(cage);assert cage.hide_render and len(C)==17*48*64;ce=float(np.linalg.norm(C-wantedC,axis=1).max());assert ce<2e-6
   for name in ['AFN90_RAIN_HAIR_MAIN','AFN90_RAIN_HAIR_PONYTAIL','AFN90_RAIN_HAIR_STRAND']:assert bpy.data.objects[name].hide_render
  else:
   cage=bpy.data.objects[ref['guideCage']];controllers=np.load(E/'studio-guide-controllers.npz');C=h.world(cage);ce=float(np.linalg.norm(C-controllers['world'].reshape(-1,3),axis=1).max());assert ce<2e-6 and len(C)==172*64 and len(cage.data.edges)==172*63 and cage.hide_render;assert not any('ellie' in ob.name.lower() for ob in bpy.data.objects);assert np.array_equal(z['owner'][:172],np.arange(172))
  rows.append({'tag':tag,'source':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'status':'PASS_MINIMUM_SAVED_REJECTED_ART_SOURCE_ONLY','actualCurves':len(counts),'pointsEach':64,'actualPoints':len(P),'savedFibreMaximumWorldErrorM':err,'savedRadiusMaximumErrorM':radiusError,'savedControllerMaximumWorldErrorM':ce,'allAttemptedRootsRetained':True,'rootScope':'Saved actual target-scalp triangle/barycentric/normal metadata; no moving attachment or finite contact proof.','originalCagesKeysUVWeightsDriversRig52BonesTeethOldCurlyCapNativeGuidesBrowsLashesMaterialsLightsUnchanged':True,'sourceStudioRigCodeNotImportedOrRequired':True,'externalTextures':external,'packedRainMaps':packed,'liveGuideOperationNaturalMotionContactRuntimeQualified':False});print('R91_SAVED_ART_READBACK',tag,err,ce,flush=True)
 (E/'minimum-saved-readback.json').write_text(json.dumps({'status':'PASS_MINIMUM_TWO_REJECTED_COMPLETE_ART_SOURCES','sources':rows,'noBroadChecksAfterVisualRejection':True,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
