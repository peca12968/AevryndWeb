"""Finish ORIGINAL terminal native brush job recovery, never regenerate the groom."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,traceback
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0136-native-curve-combing';S=R/'engine/assets/characters/female-next/source';REC=Path('C:/Users/USER/AppData/Local/Temp/quit.blend');OUT=S/'r0136-source/aevrynd-female-next-r0136-a-native-combed-bob.blend'
sp=importlib.util.spec_from_file_location('r136originalauthor',Path(__file__).with_name('build-female-next-r0136-native-curve-combing.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;aa=a.a;b.u.v.E=E
def save(n,x):a.save(n,x)
def main():
 tick=time.time();assert not OUT.exists();assert REC.stat().st_mtime>(E/'native-add-geometry.json').stat().st_mtime
 if hasattr(bpy.context.preferences.filepaths,'use_save_on_exit'):bpy.context.preferences.filepaths.use_save_on_exit=False
 # Recover only ORIGINAL authored curves into a fresh retained complete woman.
 # The terminal GUI recovery did not match the protected evaluated body hash;
 # it is not eligible to become the new complete-character baseline.
 protected=aa.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];oldObjects=set(bpy.data.objects);oldData={name:set(getattr(bpy.data,name)) for name in ['meshes','hair_curves','materials','node_groups','armatures','actions','images','collections']}
 with bpy.data.libraries.load(str(REC),link=False) as (src,dst):dst.objects=['AFN136_NATIVE_COMBED_ROOT_TIP_CURVES']
 original=dst.objects[0];recoveredMatrix=original.matrix_world.copy();recovered=original.data.copy();recovered.surface=None
 for ob in set(bpy.data.objects)-oldObjects:bpy.data.objects.remove(ob,do_unlink=True)
 for _ in range(4):
  for name,known in oldData.items():
   coll=getattr(bpy.data,name)
   for item in list(coll):
    if item not in known and item!=recovered and item.users==0:coll.remove(item)
 D=np.load(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz');V=D['world'];F=D['triangles'];mesh=bpy.data.meshes.new('AFN136_RECONNECTED_ACTUAL_NATIVE_SCALP');mesh.from_pydata(V.tolist(),[],F.tolist());mesh.update();scalp=bpy.data.objects.new('AFN136_ACTUAL_CURRENT_SCALP',mesh);bpy.context.scene.collection.objects.link(scalp);scalp.hide_render=True;uv=mesh.uv_layers.new(name='AFN136_NativeScalpUV');uv.data.foreach_set('uv',D['uv'][F.ravel()].astype('f4').ravel());h=bpy.data.objects.new('AFN136_NATIVE_COMBED_ROOT_TIP_CURVES',recovered);bpy.context.scene.collection.objects.link(h);h.matrix_world=recoveredMatrix;d=h.data;d.surface=scalp;d.surface_uv_map=uv.name
 raw=a.raw(d);rawHash=aa.hasharray(raw);counts=np.array([c.points_length for c in d.curves],'i4');assert counts.min()>=1 and np.isfinite(raw).all();starts=np.r_[0,np.cumsum(counts)[:-1]];roots=raw[starts].astype('f8');_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();baseline=json.loads((E.parent/'r0135-source-shape-fibres/a-build-summary.json').read_text('utf-8'));assert baseline['currentSkinHashes']==[aa.hasharray(W),aa.hasharray(T)];D=np.load(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz');V=D['world'];F=D['triangles'];tree=BVHTree.FromPolygons(V.tolist(),F.tolist(),all_triangles=True);hits=[tree.find_nearest(Vector(p)) for p in roots];fi=np.array([x[2] for x in hits],'i4');co=np.array([x[0] for x in hits]);dist=np.array([x[3] for x in hits]);tri=V[F[fi]];ab=tri[:,1]-tri[:,0];ac=tri[:,2]-tri[:,0];ap=co-tri[:,0];dot=lambda x,y:np.einsum('ij,ij->i',x,y);A=dot(ab,ab);B=dot(ab,ac);C=dot(ac,ac);den=A*C-B*B;u=(C*dot(ap,ab)-B*dot(ap,ac))/den;v=(A*dot(ap,ac)-B*dot(ap,ab))/den;bc=np.c_[1-u-v,u,v]
 from mathutils.kdtree import KDTree
 kd=KDTree(len(W))
 for j,p in enumerate(W):kd.insert(Vector(p),j)
 kd.balance();skinIDs=np.array([kd.find(Vector(p))[1] for p in V],'i4');rootIds=skinIDs[F[fi]];anchors=np.einsum('ij,ijk->ik',bc,W[rootIds]);a.attach(h,skin,rootIds,bc,anchors);a.caphelper.point_bound_cap(scalp,skin,np.repeat(skinIDs[:,None],3,axis=1),np.tile([1.,0.,0.],(len(V),1)),V)
 radius=np.concatenate([.000045*np.maximum(.06,(1-np.linspace(0,1,n))**.45) for n in counts]);rr=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');rr.data.foreach_set('value',radius.astype('f4'));mat=bpy.data.materials.new('AFN136_InitialBrownNativeHair');mat.use_nodes=True;nd=mat.node_tree.nodes;nd.clear();out=nd.new('ShaderNodeOutputMaterial');ha=nd.new('ShaderNodeBsdfHairPrincipled');ha.parametrization='MELANIN';ha.inputs['Melanin'].default_value=.7;ha.inputs['Melanin Redness'].default_value=.4;ha.inputs['Roughness'].default_value=.3;ha.inputs['Radial Roughness'].default_value=.3;mat.node_tree.links.new(ha.outputs[0],out.inputs['Surface']);d.materials.clear();d.materials.append(mat);bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render=True;bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_set(True);scalp.hide_render=True
 assert rawHash==aa.hasharray(a.raw(d));ops=json.loads((E/'native-brush-operations.json').read_text('utf-8'));initial=json.loads((E/'native-add-geometry.json').read_text('utf-8'));h['authoring']='Actual native Blender Add/Comb brush event operations; original saved recovery retained as actual geometry, no groom regeneration. Nonconstant comb curve counts remain a known failure; all original resulting curves retained.';h['scope']='Unaccepted appearance candidate, editable native curves and current-skin root translation only. No reliable complete native stroke replay, rigid head turn, natural dynamics, finite/self/continuous contact or engine acceptance.';h['sourceCredit']='Angelica / DarkNik original NikZava284 head/scalp/skin/reference bob CC-BY4.0; MakeHuman/Vitruvian body CC0. New native authoring Aevrynd, exact inherited rights retained; no exclusive ownership claim.'
 assert protected==aa.protected();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'native-follicle-lineage.npz',counts=counts,rootSkinVertexIds=rootIds,rootBarycentric=bc,rootRestWorld=roots)
 save('original-native-job-recovery.json',{'originalProcessId':6344,'recoverySource':str(REC),'recoveryMtimeUTC':datetime.datetime.fromtimestamp(REC.stat().st_mtime,datetime.timezone.utc).isoformat(),'recoverySha256':aa.sha(REC),'rawNativeGeometryBeforeAndAfterFinishHash':rawHash,'originalNativeCurvesPreservedExactly':True,'initialNativeAddCurves':initial['curves'],'finalCurves':len(counts),'curvePointCountHistogram':{str(int(n)):int((counts==n).sum()) for n in np.unique(counts)},'nativeCombChangedCurveCountKnownFailure':len(counts)!=initial['curves'],'noOriginalNativeJobRestartedOrGroomRegenerated':True})
 save('a-build-summary.json',{'source':str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'),'sourceSha256':'798c2496aadac717d967362c58afa88d38ceac584248c85f6d86afc618253631','output':str(OUT),'sha256':aa.sha(OUT),'bytes':OUT.stat().st_size,'hairObject':h.name,'scalpObject':scalp.name,'curves':len(counts),'points':len(raw),'allNativeGeometryRecoveredNotRegenerated':True,'nativeCombMaxComparableStrokePointDeltaM':max(x['maxActualPointDeltaM'] or 0 for x in ops),'nativeCombRootDeltaMaxM':None,'nativeRootsDistanceToOwnActualScalpMaxM':float(dist.max()),'actualNativeOperations':len(ops),'currentSkinHashes':[aa.hasharray(W),aa.hasharray(T)],'currentSkinExact':True,'originalCoarseHairAndScalpHidden':True,'curveCountChangedDuringCombKnownFailure':len(counts)!=initial['curves'],'naturalMotionAndFiniteSelfContinuousContactRuntimeUnaccepted':True,'recoveryFinishSecondsBeforePreview':time.time()-tick});rows=[]
 for v in ['face','body-face','profile','oblique','back']:rows.append(b.u.v.image('a-native-combed-bob',v));save('a-view-controls.json',rows)
 print('R136_ACTUAL_ORIGINAL_RECOVERED_NATIVE_COMB_COMPLETE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
def run():
 try:main()
 except:traceback.print_exc();save('recovery-finish-terminal-error.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'traceback':traceback.format_exc()})
 finally:bpy.ops.wm.quit_blender()
def load():bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));bpy.app.timers.register(run,first_interval=.5)
if __name__=='__main__':
 if bpy.app.background:bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));main()
 else:bpy.app.timers.register(load,first_interval=.5)
