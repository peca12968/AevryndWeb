"""Direct native rigid eye bones and standard action on the actual r126 layers."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,math
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0138-native-current-gaze';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';OUT=S/'r0138-source/aevrynd-female-next-r0138-a-native-current-gaze.blend'
sp=importlib.util.spec_from_file_location('r138base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
MOVING=['AFN126_ORIGINAL_Eye_Eye_0','AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0'];FIXED=['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD','AFN126_ORIGINAL_Hair_Hair_0','AFN126_ORIGINAL_Eyelashes_Eyelashes_0','AFN126_ORIGINAL_MeniscusEyeSpec_MeniscusEye_0','AFN126_ORIGINAL_Mouth_Mouth_0']
KEYS=[(1,0,0),(5,-10,0),(9,-20,0),(13,-10,0),(17,0,0),(21,10,0),(25,20,0),(29,10,0),(33,0,0),(37,0,10),(41,0,0),(45,0,-10),(49,0,0)]
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item() if isinstance(a,np.generic) else str(a))+'\n',encoding='utf-8')
def geometry(o):
 _,W,T=b.u.b.geom(o);return W.copy(),T.copy()
def rawsig(o):
 d=o.data;V=q.arr(d.vertices,'co',len(d.vertices),3);d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,'i4');return {'vertices':a.hasharray(V),'triangles':a.hasharray(T),'uv':{u.name:a.hasharray(q.arr(u.data,'uv',len(u.data),2)) for u in d.uv_layers}}
def bone_names():return {'L':'AFN138_EYE_L','R':'AFN138_EYE_R'}
def angles(rig):return {k:[math.degrees(x) for x in rig.pose.bones[n].rotation_euler] for k,n in bone_names().items()}
def main():
 tick=time.time();assert not OUT.exists();save('direct-native-gaze-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-21T21:28:30+00:00','action':'Native rigid eye bone/weight construction and standard rotation Action on actual displayed source Eye/EyeScleraReflect layers; original geometry/UV/material preserved, no hidden rollback controls.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);protected=a.protected();fixed={n:geometry(bpy.data.objects[n]) for n in FIXED};moving={n:geometry(bpy.data.objects[n]) for n in MOVING};raw={n:rawsig(bpy.data.objects[n]) for n in MOVING};inspection=json.loads((E/'actual-current-optical-layers.json').read_text('utf-8'));eye=next(r for r in inspection['actualNativeLayers'] if r['name']==MOVING[0]);centers={side:np.array(eye['sides'][side]['posteriorFit']['center']) for side in ['L','R']};arm=bpy.data.armatures.new('AFN138_ACTUAL_OCULAR_ARMATURE');rig=bpy.data.objects.new('AFN138_ACTUAL_CURRENT_GAZE_RIG',arm);scene.collection.objects.link(rig);rig.show_in_front=True;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.context.view_layer.update();bpy.ops.object.mode_set(mode='EDIT');root=arm.edit_bones.new('AFN138_EYES_FRAME');mid=(centers['L']+centers['R'])*.5;root.head=mid;root.tail=mid+np.array([0,.02,0]);root.use_deform=False
 for side,name in bone_names().items():
  bone=arm.edit_bones.new(name);bone.head=centers[side];bone.tail=centers[side]+np.array([0,.012,0]);bone.roll=0;bone.parent=root;bone.use_connect=False
 bpy.ops.object.mode_set(mode='OBJECT');bindings=[]
 for name in MOVING:
  ob=bpy.data.objects[name];W,T=moving[name];assert not ob.modifiers and len(W)==len(ob.data.vertices) and not np.any((W[T,0].min(1)<0)&(W[T,0].max(1)>0));groupRows={}
  for side,boneName in bone_names().items():
   ids=np.flatnonzero(W[:,0]>0 if side=='L' else W[:,0]<0);assert len(ids)>0;group=ob.vertex_groups.new(name=boneName);group.add(ids.tolist(),1.,'REPLACE');groupRows[side]={'vertices':len(ids),'nativeVertexSelectionHash':a.hasharray(ids.astype('i4')),'anatomicalSide':'world+X' if side=='L' else 'world-X'}
  md=ob.modifiers.new('AFN138_NATIVE_ACTUAL_GAZE_SKINNING','ARMATURE');md.object=rig;md.use_vertex_groups=True;md.use_bone_envelopes=False;md.use_deform_preserve_volume=False;bindings.append({'object':name,'groups':groupRows,'materialAndUVRawGeometryUnchanged':rawsig(ob)==raw[name]});assert rawsig(ob)==raw[name]
 for side,name in bone_names().items():rig.pose.bones[name].rotation_mode='XYZ'
 for frame,yaw,pitch in KEYS:
  for name in bone_names().values():
   pb=rig.pose.bones[name];pb.rotation_euler=(math.radians(-pitch),0,math.radians(yaw));pb.keyframe_insert(data_path='rotation_euler',frame=frame,group=name)
 action=rig.animation_data.action;action.name='AFN138_NATIVE_CURRENT_GAZE_DEMO';action.use_fake_user=True;scene.frame_start=1;scene.frame_end=49;scene.render.fps=24;scene.frame_set(1);bpy.context.view_layer.update();neutralErrors={n:float(np.linalg.norm(geometry(bpy.data.objects[n])[0]-moving[n][0],axis=1).max()) for n in MOVING};assert max(neutralErrors.values())<5e-7
 for n,(W,T) in fixed.items():
  WW,TT=geometry(bpy.data.objects[n]);assert np.array_equal(W,WW) and np.array_equal(T,TT)
 assert protected==a.protected();rig['sourceCredit']='Aevrynd native eye rigid bones/weights/standard Action. Current source Eye/reflect/head/skin/hair Angelica / DarkNik original NikZava284, CC-BY4.0; body MakeHuman/Vitruvian CC0, full inherited source/rights/rollback retained. No exclusive artwork ownership.';rig['operation']='Pose native AFN138_EYE_L/R, XYZ Euler: world Z yaw; negative world X pitch gives upward gaze. Standard action AFN138_NATIVE_CURRENT_GAZE_DEMO frames1..49 at24fps. No drivers/addon/embedded handler required. Fixed-head eye-only operation, not blink/jaw/head tracking.';rig['testRange']='Initial engineering test yaw +/-20deg, pitch +/-10deg; not a global physiological/continuous contact acceptance.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 save('native-current-gaze-construction.json',{'actualRig':rig.name,'standardAction':action.name,'bones':bone_names(),'rootBone':'AFN138_EYES_FRAME','centersWorld':centers,'pivotMethod':'Actual source Eye posterior native vertex sphere fit; not centroid or hidden old eye positions. Source not exactly spherical; residuals in optical inspection.','binding':bindings,'rawEyeSignatures':raw,'neutralEvaluatedEyeDeviationM':neutralErrors,'neutralDeviationIsFloatEvaluationNotContactTolerance':True,'keyframes':[{'frame':f,'yawDeg':y,'pitchDeg':p} for f,y,p in KEYS],'fixedLayerNames':FIXED,'movingLayerNames':MOVING,'newCurrentHeadSkinDeformRigOrBlinkAuthored':False,'nativeBoneActionNotExternalRuntimeDependency':True})
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'actualRig':rig.name,'standardAction':action.name,'movingObjects':MOVING,'fixedObjects':FIXED,'rawOriginalEyeTopologyUVAndMaterialPreserved':True,'currentSkinHairMouthLashesTearFilmAndHiddenRollbackExactAtNeutral':True,'neutralEvaluatedEyeDeviationM':neutralErrors,'keyframeCount':len(KEYS),'frameRange':[1,49],'fps':24,'currentAppearanceFunctionContactRuntimeUnacceptedPendingActualViews':True,'secondsBeforePreview':time.time()-tick});views=[]
 for v in ['face','body-face','profile','oblique','back']:views.append(b.u.v.image('a-native-current-gaze',v));save('a-view-controls.json',views)
 # Real motion frames with the neutral capture camera/light state held fixed.
 motion=[];neutral=b.u.v.image('motion-neutral','face');skinHashes={n:[a.hasharray(v) for v in fixed[n]] for n in FIXED}
 for f,yaw,pitch in KEYS:
  scene.frame_set(f);bpy.context.view_layer.update()
  for n in FIXED:assert [a.hasharray(v) for v in geometry(bpy.data.objects[n])]==skinHashes[n],('Unrelated visible layer changed',f,n)
  got=angles(rig);assert all(abs(v[2]-yaw)<1e-4 and abs(v[0]+pitch)<1e-4 for v in got.values());file=E/('actual-gaze-face-frame-%03d.png'%f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);motion.append({'file':str(file),'frame':f,'yawDeg':yaw,'pitchDeg':pitch,'actualBoneEulerDegrees':got,'cameraLightExposureControl':neutral,'sampledNativeActionFrameNotContinuousContactProof':True});save('actual-gaze-motion-controls.json',motion)
 scene.frame_set(1);bpy.context.view_layer.update();assert protected==a.protected()
 for n in MOVING:assert rawsig(bpy.data.objects[n])==raw[n]
 bodyNeutral=b.u.v.image('motion-neutral','body-face');body=[]
 for f,yaw,pitch in [(1,0,0),(9,-20,0),(25,20,0),(37,0,10),(45,0,-10),(49,0,0)]:
  scene.frame_set(f);bpy.context.view_layer.update();file=E/('actual-gaze-body-frame-%03d.png'%f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);body.append({'file':str(file),'frame':f,'yawDeg':yaw,'pitchDeg':pitch,'actualBoneEulerDegrees':angles(rig),'cameraLightExposureControl':bodyNeutral});save('actual-gaze-body-controls.json',body)
 scene.frame_set(1);bpy.context.view_layer.update();save('authoring-motion-restoration.json',{'sourceFileUnmodifiedAfterSave':a.sha(OUT)==json.loads((E/'a-build-summary.json').read_text('utf-8'))['sha256'],'originalRawEyeGeometryUVAndAllNeutralFixedLayersRestored':all(rawsig(bpy.data.objects[n])==raw[n] for n in MOVING) and all([a.hasharray(v) for v in geometry(bpy.data.objects[n])]==skinHashes[n] for n in FIXED),'actualBoneEulerDegrees':angles(rig),'completeGazeOperationNotYetAccepted':True});print('R138_COMPLETE_CURRENT_NATIVE_GAZE_AND_REAL_MOTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
