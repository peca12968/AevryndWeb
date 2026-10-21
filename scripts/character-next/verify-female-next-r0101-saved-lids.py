"""Independent saved model, delivered blink, actual scoped triangle contacts.
SAT narrows BVH candidates; no global/continuous/hair occupancy certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0101-articulated-eyelid-topology';S=R/'engine/assets/characters/female-next/source'
def mod(name,file):
 sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r101saved','build-female-next-r0098-native-head.py');q=m.q;v=m.v;v.E=E;r99=mod('r101roots','verify-female-next-r0099-saved-motion.py');h=r99.h
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def geom(ob):
 d,P=q.geom(ob);d.calc_loop_triangles();return d,P,q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4')
def intersects(A,B):
 ea=np.roll(A,-1,axis=1)-A;eb=np.roll(B,-1,axis=1)-B;na=np.cross(ea[:,0],ea[:,1]);nb=np.cross(eb[:,0],eb[:,1]);cross=np.cross(ea[:,:,None,:],eb[:,None,:,:]).reshape(-1,9,3);axes=np.concatenate((na[:,None,:],nb[:,None,:],cross,np.cross(na[:,None,:],ea),np.cross(nb[:,None,:],eb)),axis=1);length=np.linalg.norm(axes,axis=2);valid=length>1e-18;axes/=np.maximum(length,1e-30)[:,:,None];pa=np.einsum('bvi,bki->bkv',A,axes);pb=np.einsum('bvi,bki->bkv',B,axes);separated=((pa.max(2)<pb.min(2)-1e-10)|(pb.max(2)<pa.min(2)-1e-10))&valid;return ~separated.any(1)
def calibration():
 a=np.array([[0,0,0],[1,0,0],[0,1,0]],float);cases=[(a+[0,0,.1],False),(a+[1,1,0],False),(np.array([[.1,.1,0],[.2,.1,0],[.1,.2,0]]),True),(np.array([[.25,.25,-1],[.25,.25,1],[.75,.25,0]]),True)];assert all(bool(intersects(a[None],b[None])[0])==answer for b,answer in cases)
def contact(V,T):
 rows=[]
 for side in ['L','R']:
  ed,EV,ET=geom(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);lower=EV.min(0);upper=EV.max(0);verts=V[T];selected=np.flatnonzero(np.all(verts.max(1)>=lower,axis=1)&np.all(verts.min(1)<=upper,axis=1));used,inverse=np.unique(T[selected],return_inverse=True);a=BVHTree.FromPolygons(V[used].tolist(),inverse.reshape(-1,3).tolist(),all_triangles=True);b=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True);pairs=a.overlap(b);witness=[];inspected=0;cap=250000
  for start in range(0,min(len(pairs),cap),4096):
   batch=np.array(pairs[start:start+4096],'i4');ids=selected[batch[:,0]];hit=intersects(V[T[ids]],EV[ET[batch[:,1]]]);inspected+=len(batch)
   for j in np.flatnonzero(hit):witness.append({'actualSkinTriangle':int(ids[j]),'opticalShellTriangle':int(batch[j,1])})
   if len(witness)>=16:break
  rows.append({'side':side,'actualSkinNearbyTriangles':len(selected),'opticalTriangles':len(ET),'bvhCandidatePairs':len(pairs),'narrowPhaseInspectedPairs':inspected,'triangleSurfaceIntersectionOrTouchWitnesses':witness[:16],'allCandidatesInspected':inspected==len(pairs),'witnessCountIsNotGlobalPenetrationTotal':True,'numericSATIntervalToleranceM':1e-10,'globalSignedMinimumM':None,'scope':'Actual evaluated triangle surfaces at this pose against retained sclera/cornea approximation. Not all tissue volumes, self, hair, clothing or continuous-time proof.'})
 return rows
def deliver(blink):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];face['blink_left']=face['blink_right']=blink;oral['jaw_open']=0
 for ob in [face,oral]:ob.update_tag()
 for name in m.m.rig.native_names():ob=bpy.data.objects[name];ob.update_tag();ob.data.shape_keys.update_tag()
 bpy.data.objects['AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT'].data.shape_keys.update_tag();bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'].update_tag();bpy.context.view_layer.update()
def lash_error(V):
 helper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];H=q.geom(helper)[1];rows=json.loads((E/'b2-lash-root-bindings.json').read_text('utf8'));worst=0
 for row in rows:
  tri=V[np.array(row['actualSkinTriangle'])];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal);radius=row['sourceRootRadiusNative']*np.linalg.norm(np.array(helper.matrix_world)[:3,0]);expected=np.array(row['barycentric'])@tri+normal*radius;worst=max(worst,float(np.linalg.norm(H[row['pointStart']]-expected)))
 return worst
def frame(i):
 s=bpy.context.scene;m.m.rig.shade.settings();m.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/('blink-control-%02d.png'%i));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);return s.render.filepath
def main():
 tick=time.time();calibration();save('contact-sat-calibration.json',{'parallelSeparated':True,'coplanarDisjointDespiteOverlappingAABB':True,'coplanarContainedContact':True,'noncoplanarIntersection':True,'scope':'Narrow phase calibration; no model contact result.'});baseFile=S/'aevrynd-female-next-r0099-c-continuous-artist-body.blend';bpy.ops.wm.open_mainfile(filepath=str(baseFile));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();names=m.m.rig.native_names();native={name:q.signature(bpy.data.objects[name]) for name in names};rig=h.rig_signature();dd,C,CT=geom(bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN']);baselineHair=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();radii=q.arr(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'].data.attributes['radius'].data,'value',24800*17);baselineLashRadii=q.arr(bpy.data.objects['AFN57_NATIVE_LASHES'].data.attributes['radius'].data,'value',6998) if 'radius' in bpy.data.objects['AFN57_NATIVE_LASHES'].data.attributes else None;removed=np.load(E/'b-anatomical-lid-lineage.npz')['removedFineFaceIDs'];keep=np.ones(len(CT),bool);keep[removed]=False;uvReference={u.name:hashlib.sha256(q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2)[keep].tobytes()).hexdigest() for u in dd.uv_layers};texturesBase={im.filepath:hashlib.sha256(Path(bpy.path.abspath(im.filepath)).read_bytes()).hexdigest() for im in bpy.data.images if im.source=='FILE' and not im.packed_file and im.filepath};results={}
 for tag in ['a','a2','b','b2']:
  summary=json.loads((E/(tag+'-build-summary.json')).read_text('utf8'));path=Path(summary['output']);bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[summary['renderSkin']];d,V,T=geom(skin);slots=[x.name if x else None for x in skin.data.materials];assert np.isfinite(V).all() and all(slots);textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath));digest=hashlib.sha256(p.read_bytes()).hexdigest();assert p.is_file() and texturesBase[im.filepath]==digest;textures.append({'relative':im.filepath,'sha256':digest,'bytes':p.stat().st_size})
  assert len(textures)==15;results[tag]={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'openedIndependently':True,'vertices':len(V),'triangles':len(T),'finite':True,'renderMaterialSlots':slots,'externalTextures':textures,'completeAppearanceOperationContactRuntimeAccepted':False};save('minimum-saved-readback.json',results);print('R101_MINIMUM_OPEN',tag,flush=True)
  if tag!='b2':continue
  assert rig==h.rig_signature();assert all(native[name]==q.signature(bpy.data.objects[name]) for name in names);hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];P=q.hair(hair);assert np.array_equal(radii,q.arr(hair.data.attributes['radius'].data,'value',24800*17));hairDiff=float(np.linalg.norm(P-baselineHair,axis=1).max());assert hairDiff<6e-6;sourceIDs=q.arr(d.attributes['AFN101_OriginalCIndex'].data,'value',len(V),dtype='i4');valid=sourceIDs>=0;outside=float(np.linalg.norm(V[valid]-C[sourceIDs[valid]],axis=1).max());assert outside<4e-6;retained=json.loads((E/'b-build-summary.json').read_text('utf8'))['retainedFineFaces'];uvHashes={u.name:hashlib.sha256(q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2)[:retained].tobytes()).hexdigest() for u in d.uv_layers};assert uvReference==uvHashes;edges=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);lo=np.minimum(edges[:,0],edges[:,1]);hi=np.maximum(edges[:,0],edges[:,1]);un,ix,inc=np.unique(lo.astype('u8')*len(V)+hi,return_inverse=True,return_counts=True);orientation=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));results[tag].update({'sourceNativeBodyOpticsRawMeshKeysUVWeightsAndRig52Preserved':True,'legacyBodyBlinkInputRoutesChangedIntentionally':6,'originalRetainedBodyWorldMaximumErrorM':outside,'originalRetainedUVLoopsExact':True,'hairAllControlsMaximumWorldDifferenceFromC_M':hairDiff,'all24800CurrentGroomRootCentresMaximumWorldErrorM':r99.root_error(hair,V),'actualUnusedVertices':len(V)-len(np.unique(T)),'openEdges':int((inc==1).sum()),'nonTwoIncidentEdges':int((inc!=2).sum()),'orientationConflictEdges':int(((inc==2)&(orientation!=0)).sum()),'closedEdgesNotSelfOrFiniteContactCertificate':True});save('minimum-saved-readback.json',results)
  rows=[v.image('b2-independent-reopen','profile'),v.image('b2-independent-reopen','oblique')];lights=[(ob,ob.matrix_world.copy()) for ob in bpy.context.scene.objects if ob.type=='LIGHT']
  for ob,mat in lights:ob.location.x=-ob.location.x;ob.rotation_euler=(Vector(m.m.rig.k.b.TARGET)-ob.location).to_track_quat('-Z','Y').to_euler()
  bpy.context.view_layer.update();rows.append(v.image('b2-second-light','oblique'))
  for ob,mat in lights:ob.matrix_world=mat
  bpy.context.view_layer.update();save('b2-independent-view-controls.json',rows)
  face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];actions={ob.name:ob.animation_data.action if ob.animation_data else None for ob in [face,oral]};props={ob.name:{k:ob[k] for k in (['blink_left','blink_right'] if ob==face else ['jaw_open'])} for ob in [face,oral]}
  for ob in [face,oral]:
   if ob.animation_data:ob.animation_data.action=None
  motion=[];baseline=None;contactFailed=False
  for i,value in enumerate([0.,.25,.5,.75,1.,0.]):
   deliver(value);dd,W,TT=geom(skin);HP=q.hair(hair);assert np.array_equal(TT,T);actualBlink=float(face.evaluated_get(bpy.context.evaluated_depsgraph_get())['blink_left']);assert actualBlink==value
   if baseline is None:baseline=(W.copy(),HP.copy())
   row={'blink':value,'evaluatedBlinkLeft':actualBlink,'actualWholeSkinMaximumWorldMoveM':float(np.linalg.norm(W-baseline[0],axis=1).max()),'actualGroomMaximumWorldMoveM':float(np.linalg.norm(HP-baseline[1],axis=1).max()),'actualSkinRootCentreMaximumWorldErrorM':r99.root_error(hair,W),'all412LashRootCentreFrameMaximumWorldErrorM':lash_error(W),'finite':bool(np.isfinite(W).all() and np.isfinite(HP).all()),'file':frame(i)}
   if i in [0,2,4] and not contactFailed:
    row['scopedOpticalSurfaceContact']=contact(W,TT);contactFailed=any(x['triangleSurfaceIntersectionOrTouchWitnesses'] or not x['allCandidatesInspected'] for x in row['scopedOpticalSurfaceContact'])
   motion.append(row);save('evaluated-blink-and-contact.json',{'source':str(path),'sourceSha256':results[tag]['sha256'],'states':motion,'completeOperationAccepted':False,'globalFiniteSelfHairClothingContinuousRuntimeCertified':False,'scope':'Actual saved complete woman: assigned/evaluated blink samples, exact topology and root-frame readback. Pose samples are not continuous-time proof.'})
  save('evaluated-blink-and-contact.json',{'source':str(path),'sourceSha256':results[tag]['sha256'],'states':motion,'neutralSkinRestoreMaximumWorldErrorM':float(np.linalg.norm(W-baseline[0],axis=1).max()),'neutralGroomRestoreMaximumWorldErrorM':float(np.linalg.norm(HP-baseline[1],axis=1).max()),'completeOperationAccepted':False,'globalFiniteSelfHairClothingContinuousRuntimeCertified':False,'scope':'Actual saved complete woman: assigned/evaluated blink samples and scoped actual triangle-surface contacts only.','seconds':time.time()-tick})
  for ob in [face,oral]:
   for k,value in props[ob.name].items():ob[k]=value
   if ob.animation_data:ob.animation_data.action=actions[ob.name]
   ob.update_tag()
  bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 print('R101_SAVED_LIDS_AFFECTED_VERIFICATION_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
