"""Minimum reopen and actual visibility diagnosis after rejected first art.
No broad contact/dynamic audit and no new source saved.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0100-native-eyelid-assembly';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r100verify',Path(__file__).with_name('build-female-next-r0100-native-lid-assembly.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q
def save(x):(E/'minimum-saved-readback.json').write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
 tick=time.time();rows={};reference=None
 for tag,name in [('baseline','aevrynd-female-next-r0099-c-continuous-artist-body.blend'),('a','aevrynd-female-next-r0100-a-native-lid-assembly.blend'),('a2','aevrynd-female-next-r0100-a2-native-lid-backing.blend')]:
  path=S/name;bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];d,V=q.geom(skin);d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4');raw=q.arr(skin.data.vertices,'co',len(skin.data.vertices),3);loops=q.arr(skin.data.loops,'vertex_index',len(skin.data.loops),dtype='i4');slots=[p.name if p else None for p in skin.data.materials];UV={u.name:digest(q.arr(u.data,'uv',len(u.data),2)) for u in skin.data.uv_layers};sig={'rawVertices':digest(raw),'loops':digest(loops),'UV':UV,'materialSlots':slots,'faceMaterialIDs':digest(q.arr(skin.data.polygons,'material_index',len(skin.data.polygons),dtype='i4'))}
  if reference is None:reference=sig
  else:assert sig==reference,'Underlying complete C mesh/UV/material representation changed'
  rays=[]
  for side,sign in [('L',1),('R',-1)]:
   ed,EV=q.geom(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);centre=(EV.min(0)+EV.max(0))/2;chosen=np.flatnonzero((abs(V[T].mean(1)[:,0]-centre[0])<.023)&(abs(V[T].mean(1)[:,2]-centre[2])<.024));tree=BVHTree.FromPolygons(V.tolist(),T[chosen].tolist(),all_triangles=True)
   for dz in [0.,.002,-.002]:
    origin=Vector((centre[0],-.2,centre[2]+dz));hit,no,index,dist=tree.ray_cast(origin,Vector((0,1,0)),.2);rays.append({'side':side,'worldX':centre[0],'worldZ':centre[2]+dz,'skinFirstHitWorldY':hit.y if hit is not None else None,'opticalShellMinimumWorldY':float(EV[:,1].min()),'scope':'Actual neutral skin visibility ray only, not finite intersection or global signed-distance proof.'})
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'image':im.name,'relative':im.filepath,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  row={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'openedIndependently':True,'actualVertices':len(V),'actualTriangles':len(T),'finite':bool(np.isfinite(V).all()),'rawMeshUVAndMaterialBindingsEqualBaseline':sig==reference,'renderMaterialSlots':slots,'externalTextures':textures,'sourceRigBones':len(bpy.data.objects['AFN69_BODY_CONTROLS'].data.bones),'actualNeutralSkinRays':rays,'completeAppearanceOperationContactRuntimeAccepted':False}
  if tag!='baseline':
   donor=bpy.data.objects['AFN100_EDITABLE_NATIVE_LID_SCULPT'];row['editableNativeSculptVertices']=len(donor.data.vertices);row['nativeShapeKeys']=[k.name for k in donor.data.shape_keys.key_blocks];row['postDeformCorrectivePresent']='AFN100_NATIVE_LIDS_AFTER_ORIGINAL_DEFORM' in skin.modifiers
  rows[tag]=row;save({'sources':rows,'broadAuditStoppedAfterArtFailure':True,'noSourceSavedByVerification':True,'seconds':time.time()-tick});print('R100_MINIMUM_REOPEN',tag,flush=True)
 print('R100_MINIMUM_REOPEN_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
