"""One anatomical cavity reconstruction, preserving the original ocular meshes.
Conservative outer halfspace construction envelope, not a collision proof.
Original r138 action ranges, rendering and contact predicate remain unchanged.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,math,json,time,datetime,importlib.util
from mathutils import Vector
sp=importlib.util.spec_from_file_location('socketbase',Path(__file__).with_name('contact-female-next-r0138-ocular-surfaces.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c);a=c.a;E=a.E
SRC=a.OUT;OUT=a.S/'r0138-source/aevrynd-female-next-r0138-b-native-socket-walls.blend'
SKIN=a.FIXED[0]
def save(n,x):a.save(n,x)
def witness(A,B):
 # Independent finite segment/triangle Moller-Trumbore predicate. No SAT axes.
 hits=[]
 for edgeTri,faceTri,label in [(A,B,'skin-edge/eye-face'),(B,A,'eye-edge/skin-face')]:
  e1=faceTri[1]-faceTri[0];e2=faceTri[2]-faceTri[0]
  for i,j in [(0,1),(1,2),(2,0)]:
   p=edgeTri[i];d=edgeTri[j]-p;h=np.cross(d,e2);det=np.dot(e1,h)
   if abs(det)<1e-25:continue
   inv=1/det;s=p-faceTri[0];u=inv*np.dot(s,h);q=np.cross(s,e1);v=inv*np.dot(d,q);t=inv*np.dot(e2,q)
   if 0<=u<=1 and 0<=v and u+v<=1 and 0<=t<=1:hits.append({'method':label,'segment':(i,j),'t':float(t),'u':float(u),'v':float(v),'worldPoint':(p+t*d).tolist()})
 return hits
def directions():
 bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=3,radius=1.);bm.normal_update();n=np.array([tuple(f.normal.normalized()) for f in bm.faces],dtype='f8');bm.free();return n
def build_envelope(name,center,V,n):
 local=V-center;r=float(np.linalg.norm(local,axis=1).max());samples=[]
 for yaw in range(-20,21):
  y=math.radians(yaw);cy,sy=math.cos(y),math.sin(y);Rz=np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])
  for pitch in range(-10,11):
   p=math.radians(-pitch);cp,ss=math.cos(p),math.sin(p);Rx=np.array([[1,0,0],[0,cp,-ss],[0,ss,cp]]);samples.append(local@(Rz@Rx).T)
 points=np.concatenate(samples);omega=2*math.acos(math.cos(math.radians(.5)/2)**2);gridBound=2*r*math.sin(omega/2);clearance=.00015;floatGuard=.000002
 h=np.concatenate([(points@n[i:i+32].T).max(0) for i in range(0,len(n),32)])+gridBound+clearance+floatGuard
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=2*(r+.01))
 for normal,dist in zip(n,h):
  cut=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-9,plane_co=Vector(normal*dist),plane_no=Vector(normal),clear_outer=True,clear_inner=False)
  edges=[x for x in cut['geom_cut'] if isinstance(x,bmesh.types.BMEdge) and x.is_valid and x.is_boundary]
  if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert len(bm.faces)>20 and all(e.is_manifold for e in bm.edges),'Cutter not closed'
 bm.normal_update();v=np.array([tuple(x.co) for x in bm.verts]);res=float((v@n.T-h).max());assert res<2e-7,('Cutter construction residual',res)
 volume=bm.calc_volume(signed=True);assert volume>0
 mesh=bpy.data.meshes.new(name+'_MESH');bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob);ob.location=center
 ob['role']='Original authored conservative ocular sweep cavity construction tool; not a rendered layer or accepted collision proxy.'
 return ob,{'sourcePointCount':len(local),'samplePointCount':len(points),'directionCount':len(n),'maxOriginalRadiusM':r,'gridStepDeg':1,'nearestGridYawPitchErrorEachDeg':.5,'relativeRotationAngleBoundRad':omega,'continuousVertexDisplacementBoundM':gridBound,'fixedConstructionClearanceM':clearance,'floatGuardM':floatGuard,'planeResidualM':res,'cutterVertices':len(v),'cutterFaces':len(mesh.polygons),'closedManifold':True,'signedVolumeM3':volume,'scope':'Halfspace intersection outer construction from actual rigid ocular vertices, with bounded rotations. This is a construction premise; native output and contact require independent verification, no proxy-to-global claim.'}
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[SKIN];assert skin.type=='MESH' and not skin.data.shape_keys and not skin.modifiers
 fixed={n:a.geometry(bpy.data.objects[n]) for n in a.FIXED[1:]};raw={n:a.rawsig(bpy.data.objects[n]) for n in a.MOVING};W,T=a.geometry(skin);Skin=W[T];lo=Skin.min(1);hi=Skin.max(1);witnesses=[]
 for n in a.MOVING:
  V,F=a.geometry(bpy.data.objects[n]);r=c.query(Skin,V[F],lo,hi);counts=[];details=[]
  for si,ei in r['properCrossings']:
   hits=witness(Skin[si],V[F[ei]]);counts.append(len(hits))
   if len(details)<12:details.append({'skinFace':int(si),'eyeFace':int(ei),'finiteEdgeFaceWitnesses':hits})
  assert all(x>=2 for x in counts),'SAT crossings not corroborated by independent finite edges'
  witnesses.append({'object':n,'SATProperCrossingPairs':len(counts),'independentFiniteEdgeFaceCorroboratedPairs':sum(x>=2 for x in counts),'firstWitnesses':details})
 save('independent-source-crossing-witnesses.json',{'sources':[str(a.SRC),str(SRC)],'candidateFrame':1,'evidence':witnesses,'signedPenetrationDepthNotMeasured':True,'predicateUnchangedM':c.EPS})
 rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];normals=directions();reports=[];cutters=[]
 save('b-anatomical-socket-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalRoundStartUTC':'2026-10-21T21:28:30+00:00','firstCompletePreviewDeadlineUTC':'2026-10-21T21:58:30+00:00','additionalBPreviewDeadlineUTC':'2026-10-21T22:25:00+00:00','construction':'Native Boolean DIFFERENCE actual ocular sweep cavity; original ocular meshes/poses/ranges retained; no masking or tolerance change.'})
 for side,boneName in a.bone_names().items():
  center=np.array(rig.data.bones[boneName].head_local,dtype='f8');vs=[]
  for n in a.MOVING:
   V,F=a.geometry(bpy.data.objects[n]);vs.append(V[V[:,0]>0 if side=='L' else V[:,0]<0])
  ob,report=build_envelope('AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION',center,np.concatenate(vs),normals);report.update(side=side,centerWorld=center.tolist());cutters.append(ob)
  bpy.ops.object.select_all(action='DESELECT');skin.select_set(True);bpy.context.view_layer.objects.active=skin;md=skin.modifiers.new('AFN138_'+side+'_NATIVE_SOCKET_DIFFERENCE','BOOLEAN');md.operation='DIFFERENCE';md.solver='EXACT';md.object=ob
  bpy.ops.object.modifier_apply(modifier=md.name);ob.hide_render=True;ob.hide_set(True);ob.display_type='WIRE';reports.append(report);print('R138_NATIVE_SOCKET_BUILT',side,report,flush=True)
 # The same originally declared engineering ranges; no reduced pose or eyeball.
 for name in a.bone_names().values():
  pb=rig.pose.bones[name];constraint=pb.constraints.new('LIMIT_ROTATION');constraint.name='AFN138_ORIGINAL_DECLARED_GAZE_RANGE';constraint.owner_space='LOCAL';constraint.use_limit_x=constraint.use_limit_y=constraint.use_limit_z=True;constraint.min_x=math.radians(-10);constraint.max_x=math.radians(10);constraint.min_y=constraint.max_y=0;constraint.min_z=math.radians(-20);constraint.max_z=math.radians(20);pb.lock_location=(True,True,True);pb.lock_scale=(True,True,True);pb.lock_rotation[1]=True
 root=rig.pose.bones['AFN138_EYES_FRAME'];root.lock_location=(True,True,True);root.lock_rotation=(True,True,True);root.lock_scale=(True,True,True)
 for n,(V,F) in fixed.items():
  VV,FF=a.geometry(bpy.data.objects[n]);assert np.array_equal(V,VV) and np.array_equal(F,FF)
 assert all(a.rawsig(bpy.data.objects[n])==raw[n] for n in a.MOVING)
 WW,TT=a.geometry(skin);assert np.isfinite(WW).all() and len(TT)>len(T)*.9
 # Require all removed/new skin positions to be confined to the socket region.
 oldCoords=set(map(tuple,W));newCoords=set(map(tuple,WW));changedOld=np.array(list(oldCoords-newCoords)).reshape(-1,3);changedNew=np.array(list(newCoords-oldCoords)).reshape(-1,3)
 centers=np.array([r['centerWorld'] for r in reports]);radius=.04
 for changed in [changedOld,changedNew]:
  if len(changed):assert (np.linalg.norm(changed[:,None,:]-centers[None,:,:],axis=2).min(1)<radius).all(),'Skin changed beyond ocular region'
 save('b-native-socket-construction.json',{'source':str(SRC),'output':str(OUT),'reference':'Existing actual artist Eye/EyeScleraReflect and source socket/eyelid anatomy, full r126 attribution/rights retained. Rebuilt cavity follows original optical globe and unchanged initial gaze range.','eyesUnmodified':raw,'fixedOtherVisibleLayersUnmodified':True,'eyeCentersUseActualNativeBoneFloat32RestHeads':True,'construction':reports,'oldSkinVertices':len(W),'newSkinVertices':len(WW),'oldSkinTriangles':len(T),'newSkinTriangles':len(TT),'removedSourceSkinCoordinates':len(changedOld),'newSkinCoordinates':len(changedNew),'changesConfinedWithinOcularRegionRadiusM':radius,'skinRawTopologyChangedSocketWallReconstruction':True,'originalLidClosurePlateMethodsNotReused':True,'numericContactPredicateUnchangedM':c.EPS,'allContactClaimsMustBeRetested':True,'noFullFiniteOrContinuousContactAcceptance':True})
 scene.frame_set(1);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 save('b-build-summary.json',{'source':str(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualRig':rig.name,'standardAction':rig.animation_data.action.name,'fullCharacterScopeNotYetAccepted':True,'secondsBeforePreview':time.time()-tick})
 views=[]
 for v in ['face','body-face','profile','oblique','back']:
  views.append(a.b.u.v.image('b-native-socket-walls',v));save('b-view-controls.json',views)
 neutral=a.b.u.v.image('b-motion-neutral','face');rows=[]
 for f,y,p in [(1,0,0),(9,-20,0),(25,20,0),(37,0,10),(45,0,-10),(49,0,0)]:
  scene.frame_set(f);bpy.context.view_layer.update();file=E/('b-gaze-face-frame-%03d.png'%f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);rows.append({'frame':f,'yaw':y,'pitch':p,'file':str(file),'cameraLightExposure':neutral,'actualBoneAngles':a.angles(rig)});save('b-gaze-motion-controls.json',rows)
 scene.frame_set(1);bpy.context.view_layer.update();print('R138_B_COMPLETE_NATIVE_SOCKET_HEAD_BODY_AND_MOTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
