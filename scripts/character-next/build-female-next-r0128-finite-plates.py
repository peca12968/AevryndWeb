"""Replace original blind sockets and separate actual finite outer lid plates.
Original accepted full r126 woman is the source, not the r127 failed warp.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls';PRE=E.parent/'r0127-native-lid-closure';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';OUT=S/'r0128-source/aevrynd-female-next-r0128-a-finite-native-plates.blend'
sp=importlib.util.spec_from_file_location('r128platebase',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def main():
 tick=time.time();assert not OUT.exists();save('finite-plate-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct Blender source face separation and finite outer tarsal-plate construction, source closed pockets replaced; unaccepted complete construction stage before own articulation.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));protected=a.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];native=np.load(PRE/'native-head-topology.npz');P=native['world'];T=native['triangles'];pdom=np.load(E/'authored-native-plate-domains.npz');sdom=np.load(E/'actual-native-lid-domains.npz');plateFaces=set(np.r_[pdom['L_plateFaces'],pdom['R_plateFaces']]);socketFaces=set(np.r_[sdom['L_socketFaces'],sdom['R_socketFaces']]);lookup={tuple(sorted(t)):i for i,t in enumerate(T)};k=KDTree(len(P))
 for i,p in enumerate(P):k.insert(Vector(p),i)
 k.balance();W=np.array([skin.matrix_world@v.co for v in skin.data.vertices]);nativeIds=np.full(len(W),-1,dtype=np.int32)
 for i in np.flatnonzero(W[:,2]>1.4):
  _,j,dist=k.find(Vector(W[i]))
  if dist<5e-7:nativeIds[i]=j
 removed=[];sourceFaceMap=[]
 for face in skin.data.polygons:
  ids=nativeIds[list(face.vertices)];fi=lookup.get(tuple(sorted(ids))) if len(ids)==3 and min(ids)>=0 else None
  if fi in plateFaces or fi in socketFaces:removed.append(face.index);sourceFaceMap.append(fi)
 assert len(removed)==len(plateFaces)+len(socketFaces),(len(removed),len(plateFaces),len(socketFaces));attr=skin.data.attributes.new('AFN128_OriginalCompleteVertex','INT','POINT');attr.data.foreach_set('value',np.arange(len(W),dtype=np.int32));bm=bmesh.new();bm.from_mesh(skin.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in removed],context='FACES_ONLY');loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(skin.data);bm.free();skin.data.update();original=bpy.data.objects['AFN126_ORIGINAL_Head_Head_0'];parts=[]
 for side in ['L','R']:
  bm=bmesh.new();bm.from_mesh(original.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table();assert all(len(f.verts)==3 for f in bm.faces);keep=set(pdom[side+'_plateFaces']);bmesh.ops.delete(bm,geom=[f for i,f in enumerate(bm.faces) if i not in keep],context='FACES_ONLY');loose=[v for v in bm.verts if not v.link_faces]
  if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
  me=bpy.data.meshes.new('AFN128_'+side+'_TARSAL_OUTER_NATIVE');bm.to_mesh(me);bm.free();me.transform(original.matrix_world);me.uv_layers.active.name='AngelicaOriginalUV';me.materials.clear();me.materials.append(bpy.data.materials['AFN126_NATIVE_ARTIST_HEAD_MATERIAL']);ob=bpy.data.objects.new('AFN128_'+side+'_FINITE_TARSAL_PLATE',me);bpy.context.scene.collection.objects.link(ob)
  for f in me.polygons:f.use_smooth=True;f.material_index=0
  mod=ob.modifiers.new('AFN128_EXPLICIT_INNER_WALL_AND_ROLLED_BORDER','SOLIDIFY');mod.thickness=.0005;mod.offset=-1.;mod.use_rim=True;mod.use_even_offset=True;ob['anatomicalRole']='Outer source skin / backing inner wall / finite plate rim. Approximate0.5mm artist thickness; not subject-calibrated anatomy or collision proof.';parts.append(ob.name)
 assert a.protected()==protected;skin['AFN128_scope']='Native blind socket faces replaced by actual separated finite outer lid plates. Source face/body outside selected source domains retained, original r126 full .blend rollback. Construction only, own articulation pending.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'finite-plate-source-lineage.npz',originalCompleteWorld=W,originalCompleteNativeIds=nativeIds,removedCompleteFaceIds=removed,removedNativeFaceIds=sourceFaceMap)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkinObject':skin.name,'finitePlateObjects':parts,'removedNativeBlindSocketTriangles':len(socketFaces),'reconstructedNativeOuterPlateTriangles':len(plateFaces),'sourceOutsideAnatomicalDomainsRetained':True,'completeNeutralReviewAndAllContactsPending':True,'oldHiddenRollbackExact':protected==a.protected(),'seconds':time.time()-tick});print('R128_COMPLETE_FINITE_PLATE_CONSTRUCTION_SAVED',time.time()-tick,flush=True)
if __name__=='__main__':main()
