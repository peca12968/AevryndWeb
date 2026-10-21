"""Minimum complete-source readback and exact limits of the new art body."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r104saved',Path(__file__).with_name('verify-female-next-r0101-saved-lids.py'));f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f);q=f.q;f.E=E;f.v.E=E
def save(n,x):f.save(n,x)
def sha(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def contact(V,T):
 rows=[]
 for side in ['L','R']:
  dd,EV,ET=f.geom(bpy.data.objects['AFN104_NATIVE_'+side+'_SCLERA']);verts=V[T];selected=np.flatnonzero(np.all(verts.max(1)>=EV.min(0),axis=1)&np.all(verts.min(1)<=EV.max(0),axis=1));used,inverse=np.unique(T[selected],return_inverse=True);tree=BVHTree.FromPolygons(V[used].tolist(),inverse.reshape(-1,3).tolist(),all_triangles=True);optic=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True);pairs=tree.overlap(optic);witness=[]
  for start in range(0,min(len(pairs),250000),4096):
   batch=np.array(pairs[start:start+4096],'i4');ids=selected[batch[:,0]];hits=f.intersects(V[T[ids]],EV[ET[batch[:,1]]])
   for i in np.flatnonzero(hits):witness.append({'skinTriangle':int(ids[i]),'opticalTriangle':int(batch[i,1])})
   if len(witness)>=16:break
  rows.append({'side':side,'bvhCandidatePairs':len(pairs),'storedIntersectionOrTouchWitnessPairs':witness[:16],'witnessCountNotGlobalPenetrationTotal':True,'scope':'Actual evaluated neutral triangle surfaces against native sclera/cornea approximation only; no finite/global/self/hair/cloth/continuous claim.'})
 return rows
from mathutils.bvhtree import BVHTree
def main():
 tick=time.time();checks={};f.calibration();names=[('a','aevrynd-female-next-r0104-a-native-artist-ocular.blend','AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'),('b','aevrynd-female-next-r0104-b-native-head-volume-union.blend','AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'),('b2','aevrynd-female-next-r0104-b2-native-head-material-repair.blend','AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'),('b3','aevrynd-female-next-r0104-b3-native-head-skin-domain.blend','AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD')]
 for tag,name,bodyName in names:
  p=S/name;bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[bodyName];d,V,T=f.geom(skin);assert np.isfinite(V).all();textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    path=Path(bpy.path.abspath(im.filepath));assert path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path),'bytes':path.stat().st_size})
  checks[tag]={'source':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'openedIndependently':True,'renderSkin':bodyName,'vertices':len(V),'triangles':len(T),'finite':True,'externalTextures':textures,'actualVisibleMeshSlots':[x.name if x else None for x in skin.data.materials],'completeAppearanceOperationContactRuntimeAccepted':False};save('minimum-saved-readback.json',checks);print('R104_MINIMUM_OPEN',tag,flush=True)
  if tag!='b3':continue
  V=V.copy();T=T.copy();uv=q.arr(d.uv_layers['VitruvianUV.UDIM'].data,'uv',len(d.loops),2);d.calc_loop_triangles();loops=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');values=uv[loops];centres=V[T].mean(1);mouth=(abs(centres[:,0])<.04)&(centres[:,2]>1.36)&(centres[:,2]<1.415)&(centres[:,1]<-.07);span=np.ptp(values[mouth],axis=1).max(1);edges=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);un,ix,inc=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True);orientation=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));checks[tag].update({'unusedVertices':len(V)-len(np.unique(T)),'openEdges':int((inc==1).sum()),'nonTwoIncidentEdges':int((inc!=2).sum()),'orientationConflictEdges':int(((inc==2)&(orientation!=0)).sum()),'mouthTriangleUVSpanQuantiles':np.quantile(span,[0,.5,.95,1]),'mouthTrianglesUVSpanAboveQuarterTile':int((span>.25).sum()),'neutralNativeOpticalSurfaceCheck':contact(V,T)});save('minimum-saved-readback.json',checks)
  face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
  for ob in [face,oral]:
   if ob.animation_data:ob.animation_data.action=None
  hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];rows=[]
  for value in [0.,1.,0.]:
   f.deliver(value);dd,W,TT=f.geom(skin);actual=float(face.evaluated_get(bpy.context.evaluated_depsgraph_get())['blink_left']);assert actual==value;rows.append({'assignedBlink':value,'evaluatedBlink':actual,'actualNewDisplayedSkinMaximumWorldMoveM':float(np.linalg.norm(W-V,axis=1).max()),'actualGroomRootCentreMaximumWorldErrorM':f.r99.root_error(hair,W),'finite':bool(np.isfinite(W).all()),'scope':'New static displayed head/body is not driven by inherited blink. Existing control sources are retained; this is a missing operation, not a pass.'})
  save('displayed-body-blink-input-failure.json',{'source':str(p),'states':rows,'newBodyStaticNotCompleteOperation':True,'noExtraMotionRenderAfterStaticFailure':True,'scope':'Actual assigned/evaluated input and displayed geometry readback; source control availability does not prove new displayed-skin deformation.'})
 save('saved-foundation-check-summary.json',{'sources':len(checks),'seconds':time.time()-tick,'completeAppearanceOrOperationAccepted':False});print('R104_MINIMUM_SAVED_FOUNDATIONS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
