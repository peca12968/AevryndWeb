"""Saved-source material/geometry readback and short actual affected poses.
No complete-action, natural-hair, rendered finite-contact or runtime pass.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';S=R/'engine/assets/characters/female-next/source'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r99saved','verify-female-next-r0090-rain-and-flow.py');v=mod('r99savedviews','render-female-next-r0091-matched.py');v.E=E;p=mod('r99parity','verify-female-next-r0081-curly.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def geom(o):
 d,V=q.geom(o);d.calc_loop_triangles();return V,q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4')
def slots(o):return [x.name if x else None for x in o.data.materials]
def root_error(hair,V):
 ids=np.column_stack([q.arr(hair.data.attributes['AFN97_ScalpVertex'+str(j)].data,'value',24800,dtype='i4') for j in range(3)]);w=q.arr(hair.data.attributes['AFN97_RootBarycentric'].data,'vector',24800,3).astype('f8');tri=V[ids];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];A=np.array(hair.matrix_world);radius=q.arr(hair.data.attributes['AFN97_RootRadiusNative'].data,'value',24800)*np.linalg.norm(A[:3,0]);expect=np.sum(tri*w[:,:,None],axis=1)+normal*radius[:,None];actual=q.hair(hair).reshape(24800,17,3);return float(np.linalg.norm(actual[:,0]-expect,axis=1).max())
def render_motion(i):
 s=bpy.context.scene;m.rig.shade.settings();m.rig.k.b.camera('oblique');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/('affected-motion-%02d.png'%i));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);return s.render.filepath
def second_light(tag):
 lights=[(o,o.matrix_world.copy()) for o in bpy.context.scene.objects if o.type=='LIGHT']
 for o,mat in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(m.rig.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.view_layer.update();row=v.image(tag+'-second-light','oblique')
 for o,mat in lights:o.matrix_world=mat
 bpy.context.view_layer.update();return row
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0098-b-native-artist-head.blend');names=m.rig.native_names();native={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();teeth={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID']};helpers={n:h.native.signature(bpy.data.objects[n]) for n in ['AFN59_BROWS_NATIVE_POINT_POSES','AFN59_LASHES_NATIVE_POINT_POSES']};lights=m.m.q.lights();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};hairName='AFN97_TUCKED_ARTIST_BOB_CHILDREN';hair=bpy.data.objects[hairName];baseHair=q.hair(hair).reshape(24800,17,3).copy();radius=q.arr(hair.data.attributes['radius'].data,'value',24800*17).copy();sourceHeadSlots=slots(bpy.data.objects['AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR']);save('prior-head-material-persistence-scope.json',{'r98OriginalSavedHeadRawMaterialSlots':sourceHeadSlots,'r98FileUnmodified':True,'sourceHash':sha(S/'aevrynd-female-next-r0098-b-native-artist-head.blend'),'scope':'Prior material-tree signatures did not verify actual head slot bindings. This is a new saved-object finding; prior historical reports are preserved, not silently rewritten.'});results=json.loads((E/'minimum-saved-readback.json').read_text('utf8')) if (E/'minimum-saved-readback.json').exists() else {};second={}
 for tag in (['a2','c'] if all(k in results for k in ['a','a2','b']) else ['a','a2','b','c']):
  ref=json.loads((E/(tag+'-build-summary.json')).read_text('utf8'));path=Path(ref['output']);assert sha(path)==ref['outputSha256'];h.open_file(path);assert rig==h.rig_signature() and lights==m.m.q.lights();assert teeth=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in teeth};assert helpers=={n:h.native.signature(bpy.data.objects[n]) for n in helpers};assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert native['AFN60_BODY_ORAL_AND_OCULAR_LINING']==h.native.signature(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);ocularExact=all(native[n]==h.native.signature(bpy.data.objects[n]) for n in names if n!='AFN60_BODY_ORAL_AND_OCULAR_LINING');assert ocularExact or tag=='a';hair=bpy.data.objects[hairName];P=q.hair(hair).reshape(baseHair.shape);assert np.isfinite(P).all() and np.array_equal(radius,q.arr(hair.data.attributes['radius'].data,'value',24800*17));render=bpy.data.objects[ref['renderSkin']];V,T=geom(render);assert np.isfinite(V).all();materialSlots=slots(render)
  if tag!='a':assert all(x is not None for x in materialSlots) and 'AFN57_CANONICAL_SKIN' in materialSlots
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    pp=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and pp.is_file();textures.append({'relative':im.filepath,'sha256':sha(pp)})
  assert len(textures)==15 and not bpy.data.libraries
  row={'source':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'independentlyReopened':True,'originalBodyControlCagesKeysUVWeightsDriversRig52TeethBrowsLashesAndMaterialTreesPreserved':True,'originalOcularRawAndAllKeyDataExact':ocularExact,'renderMaterialSlots':materialSlots,'externalTextures':textures,'all24800SourceChildrenAndCorrectRadiusCloseTipPreserved':True,'freeHairControlsMaximumWorldChangeFromR98M':float(np.linalg.norm(P[:,1:]-baseHair[:,1:],axis=2).max()),'newCompleteOperationAppearanceNaturalMotionContactRuntimeAccepted':False}
  if tag=='c':
   line=np.load(E/'c-continuous-artist-lineage.npz');err=float(np.linalg.norm(V-line['actualRestWorld'],axis=1).max());expected=P-line['hairNewWorld'];hairSavedError=float(np.linalg.norm(expected,axis=2).max());re=root_error(hair,V);row.update({'skinRestReadbackMaximumWorldErrorM':err,'skinReadbackWithin4MicrometreGuard':err<4e-6,'savedHairMaximumWorldErrorM':hairSavedError,'savedHairWithin6MicrometreGuard':hairSavedError<6e-6,'actualSkinAll24800RootCentreMaximumWorldErrorM':re,'rootReadbackWithin6MicrometreGuard':re<6e-6,'actualContinuousSkinVertices':len(V),'actualContinuousSkinTriangles':len(T),'originalArtistSourceBodyAndUVRetainedInBlend':bool(bpy.data.objects.get(ref['originalSourceObject'])),'bindRestCorrectionMaximumNativeMagnitudeM':float(np.linalg.norm(q.arr(render.data.attributes['AFN99_BindRestCorrection'].data,'vector',len(render.data.vertices),3),axis=1).max()),'controlCageTriangulationNodeInputs':next({socket.name:str(socket.default_value) for socket in n.inputs if hasattr(socket,'default_value')} for md in bpy.data.objects[ref['controlCage']].modifiers if md.type=='NODES' for n in md.node_group.nodes if n.bl_idname=='GeometryNodeTriangulate')});save('minimum-saved-readback.json',{**results,tag:row});v.image('c-independent-reopen','face')
   edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);_,inc=np.unique(edges[:,0].astype('u8')*len(V)+edges[:,1],return_counts=True);closed=bool(np.all(inc==2));tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);witness=[];inspected=0
   for index in np.linspace(0,P.size//3-1,2048,dtype=int):
    pt=P.reshape(-1,3)[index];co,no,fi,dist=tree.find_nearest(Vector(pt));inspected+=1
    if dist<=.00006*np.linalg.norm(np.array(hair.matrix_world)[:3,0])+1e-6:continue
    inside=[p.parity(tree,pt,d) for d in [(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]]
    if closed and all(x is True for x in inside):witness.append({'curve':int(index//17),'point':int(index%17),'world':pt,'unsignedActualSkinDistanceM':dist,'threeRayOddParity':inside})
    if len(witness)>=8:break
   row['scopedStaticContact']={'actualSurface':render.name,'closedTwoIncidentEdges':closed,'selfIntersectionNotCertified':True,'plannedAuthoringControlSamples':2048,'inspected':inspected,'authoringControlPointOddParityWitnesses':witness,'countsNotGlobalTotals':True,'globalSignedMinimumM':None,'actualRenderedSplineFiniteRootBodySelfContinuousContactCertified':False};save('minimum-saved-readback.json',{**results,tag:row})
  if tag in ['a2','c']:second[tag]=second_light(tag);save('second-light-view-controls.json',second)
  results[tag]=row;save('minimum-saved-readback.json',results);print('R99_MINIMUM_SAVED',tag,row.get('skinRestReadbackMaximumWorldErrorM'),row.get('savedHairMaximumWorldErrorM'),flush=True)
 # Actual independent saved source, five separate affected states and restore.
 ref=json.loads((E/'c-build-summary.json').read_text('utf8'));skin=bpy.data.objects[ref['renderSkin']];hair=bpy.data.objects[hairName];baseV,baseT=geom(skin);baseP=q.hair(hair).reshape(baseHair.shape).copy();cage=bpy.data.objects[ref['controlCage']];cageV,cageT=geom(cage);rigObj=bpy.data.objects['AFN69_BODY_CONTROLS'];bone=rigObj.pose.bones['Head'];matrix=bone.matrix_basis.copy();face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];original={k:face[k] for k in ['blink_left','blink_right']};jaw=oral['jaw_open'];motion=[]
 states=[('neutral',0,0,0),('head-yaw',12,0,0),('blink',0,1,0),('jaw-open',0,0,.35),('neutral-restore',0,0,0)]
 for i,(label,yaw,blink,jawValue) in enumerate(states):
  bone.matrix_basis=matrix;face['blink_left']=face['blink_right']=blink;oral['jaw_open']=jawValue
  if yaw:m.rig.axis_pose(rigObj,'Head',(0,0,1),yaw)
  bpy.context.view_layer.update();current,tt=geom(skin);hp=q.hair(hair).reshape(baseP.shape);cv,ct=geom(cage);finite=bool(np.isfinite(current).all() and np.isfinite(hp).all());row={'state':label,'headYawDegrees':yaw,'blink':blink,'jawOpen':jawValue,'finite':finite,'maximumActualSkinWorldDisplacementM':float(np.linalg.norm(current-baseV,axis=1).max()),'maximumActualHairControlWorldDisplacementM':float(np.linalg.norm(hp-baseP,axis=2).max()),'targetCageTrianglesChangedFromBindNeutral':None if ct.shape!=cageT.shape else int(np.count_nonzero(np.any(ct!=cageT,axis=1))),'actualSkinRootCentreMaximumWorldErrorM':root_error(hair,current),'scope':'Actual displayed whole skin/groom sampled authoring control state. Not natural hair physics, valid full operation or finite/continuous contact proof.'}
  if finite:row['file']=render_motion(i)
  motion.append(row);save('affected-motion-scope.json',{'states':motion,'completeOperationAccepted':False,'naturalHairPhysicsOrContinuousContactsAccepted':False})
 bone.matrix_basis=matrix
 for k,val in original.items():face[k]=val
 oral['jaw_open']=jaw;bpy.context.view_layer.update();restoreV,_=geom(skin);restoreP=q.hair(hair).reshape(baseP.shape);save('affected-motion-scope.json',{'source':ref['output'],'sha256':ref['outputSha256'],'states':motion,'exactNeutralSkinRestore':bool(np.array_equal(restoreV,baseV)),'exactNeutralGroomRestore':bool(np.array_equal(restoreP,baseP)),'completeOperationAccepted':False,'naturalHairPhysicsOrContinuousContactsAccepted':False,'seconds':time.time()-tick});save('second-light-view-controls.json',second)
 for a,b in [(second['a2'],second['c'])]:assert {k:v for k,v in a.items() if k!='file'}=={k:v for k,v in b.items() if k!='file'}
 print('R99_SAVED_AND_AFFECTED_MOTION_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
