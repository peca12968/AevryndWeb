from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
from mathutils import Vector
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0213-anatomical-section-cage';F=Path('F:/AevryndEvidence/r0213-anatomical-section-cage');t=json.loads((E/'before.json').read_text());spec=importlib.util.spec_from_file_location('r213base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
assert sha(t['artistInput'])==t['artistInputSHA256'];bpy.ops.wm.open_mainfile(filepath=t['artistInput']);src=bpy.data.objects['straight_hair_to_shoulder'];body=src.data.surface;SV,ST=a.geometry(body);allUV=src.data.surface_uv_map;sourceCapMask=np.load(E.parent/'r0198-native-birth-owned-scalp/source-guide-and-cap-construction.npz')['sourceCapMask'];sourceCap=SV[np.unique(ST[sourceCapMask])];assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);TV,TT=a.geometry(bpy.data.objects[a.FIXED[0]]);targetFaces=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz')['actualCurrentScalpFaces'];targetCap=TV[np.unique(TT[targetFaces])]
def landmarks(V,cap):
 crown=V[np.argmax(V[:,2])];c=float(crown[2]);earBand=V[(V[:,2]>c-.13)&(V[:,2]<c-.055)];left=earBand[np.argmin(earBand[:,0])];right=earBand[np.argmax(earBand[:,0])];mid=cap[abs(cap[:,0])<.025];front=mid[np.argmin(mid[:,1])];rear=mid[mid[:,1]>np.quantile(mid[:,1],.7)];nape=rear[np.argmin(rear[:,2])];ear=(left+right)/2;z=np.array([nape[2]-.10,nape[2],ear[2],front[2],c-.012,c]);assert np.all(np.diff(z)>.002),('landmark order',z.tolist());return {'crown':crown.tolist(),'earLateralLeft':left.tolist(),'earLateralRight':right.tolist(),'earPlaneCentre':ear.tolist(),'capFrontHairline':front.tolist(),'capRearNape':nape.tolist(),'semanticZKnots':z.tolist(),'landmarkSelectionNotFullAnatomicalAcceptance':True},z
SL,SZ=landmarks(SV,sourceCap);TL,TZ=landmarks(TV,targetCap)
def section(V,T,z):
 tri=V[T];keep=(tri[:,:,2].min(1)<=z)&(tri[:,:,2].max(1)>z);tri=tri[keep];points=[]
 for i,j in [(0,1),(1,2),(2,0)]:
  a,b=tri[:,i],tri[:,j];mask=(a[:,2]<=z)&(b[:,2]>z)|(b[:,2]<=z)&(a[:,2]>z);aa,bb=a[mask],b[mask];u=(z-aa[:,2])/(bb[:,2]-aa[:,2]);points.append(aa+u[:,None]*(bb-aa))
 P=np.vstack(points);assert len(P)>8;middle=P[abs(P[:,0])<.014];assert len(middle)>2;return np.array([P[:,0].min(),P[:,0].max(),middle[:,1].min(),middle[:,1].max()]),P
def rings(V,T,z):
 result=[];out=[]
 for i,v in enumerate(z):
  actual=min(v,float(z[-2]));q,P=section(V,T,actual);result.append(q);out.append(P)
 return np.array(result),out
SR,SP=rings(SV,ST,SZ);TR,TP=rings(TV,TT,TZ);assert (SR[:,1]-SR[:,0]>0).all() and (TR[:,1]-TR[:,0]>0).all();assert (SR[:,3]-SR[:,2]>0).all() and (TR[:,3]-TR[:,2]>0).all();np.savez_compressed(E/'actual-anatomical-section-cage.npz',sourceZ=SZ,targetZ=TZ,sourceRings=SR,targetRings=TR,sourceBodyWorld=SV,sourceBodyTriangles=ST,targetSkinWorld=TV,targetSkinTriangles=TT,sourceSectionPoints=np.vstack(SP),sourceSectionOffsets=np.r_[0,np.cumsum([len(q) for q in SP])],targetSectionPoints=np.vstack(TP),targetSectionOffsets=np.r_[0,np.cumsum([len(q) for q in TP])]);q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceLandmarks':SL,'targetLandmarks':TL,'sourceSectionBounds':[row.tolist() for row in SR],'targetSectionBounds':[row.tolist() for row in TR],'worldMetresActualSkinTrianglePlaneIntersections':True,'no206DiskMappingOr212FailedFieldUsed':True,'sectionOrientationPositive':True,'oneSharedSupportDeadlineUTC':t['supportDeadlineUTC']};(E/'anatomical-section-measurement.json').write_bytes((json.dumps(q,indent=2)+'\n').encode())
# Source/current spatial inspection only; gray copies do not change woman.
for ob in bpy.data.objects:ob.hide_render=True
gray=bpy.data.materials.new('AFN213_REFERENCE_ONLY_GRAY');gray.diffuse_color=(.25,.25,.25,1);gray.use_nodes=True;bs=next(x for x in gray.node_tree.nodes if x.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.25,.25,.25,1);bs.inputs['Roughness'].default_value=.65
refs=[]
for name,V,T in [('SOURCE',SV,ST),('CURRENT',TV,TT)]:
 me=bpy.data.meshes.new('AFN213_REF_'+name);me.from_pydata(V.tolist(),[],T.tolist());me.update();ob=bpy.data.objects.new(me.name,me);s.collection.objects.link(ob);me.materials.append(gray);refs.append(ob)
camera=s.camera;camera.data.type='PERSP';camera.data.lens=85;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.seed=61061;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5
for ob,L in zip(refs,[SL,TL]):
 for other in refs:other.hide_render=other!=ob
 target=Vector((0,-.025,(L['crown'][2]+L['capRearNape'][2])/2));originalLights=[o for o in s.objects if o.type=='LIGHT']
 for light in originalLights:light.hide_render=False
 for view,direction in [('front',Vector((0,-1,0))),('profile',Vector((1,0,0)))]:
  camera.location=target+direction*.72;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(F/f'actual-{ob.name.split("_")[-1].lower()}-head-spatial-reference-{view}.png');bpy.ops.render.render(write_still=True)
print('R213_ACTUAL_SOURCE_CURRENT_HEAD_SECTIONS_AND_SPATIAL_VIEWS_SAVED',json.dumps(q),flush=True)
