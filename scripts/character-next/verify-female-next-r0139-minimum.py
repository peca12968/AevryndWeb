"""Independent native current lid control/restore, then scoped actual contacts.
Both source skin and eyes are evaluated anew at each pose. No frozen skin oracle.
"""
from pathlib import Path
import bpy,numpy as np,json,time,math,sys,importlib.util
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
h=module('r139verifybuild','build-female-next-r0139-native-lid-follow.py');c=module('r139verifycontact','contact-female-next-r0138-ocular-surfaces.py');sign=module('r139verifysign','build-female-next-r0131-native-hair-material.py');a=h.a;E=h.E;a.b.u.v.E=E
MINIMUM='--minimum-only' in sys.argv
def save(n,x):h.save(n,x)
def hashes(n):return [a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])]
def Rx(x):return np.array([[1,0,0],[0,math.cos(x),-math.sin(x)],[0,math.sin(x),math.cos(x)]])
def setup(view):
 s=bpy.context.scene;m=a.b.u.v.image.__globals__['m'];m.rig.shade.settings();m.rig.k.b.camera(view);s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;bpy.context.view_layer.update();return {'camera':np.array(s.camera.matrix_world).tolist(),'lensMM':s.camera.data.lens,'lights':m.m.q.lights(),'resolution':640,'samples':s.cycles.samples,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'hairSubdiv':3}
def main():
 tick=time.time();build=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(build['output']);assert a.a.sha(src)==build['sha256'];names=[h.SKIN]+h.ATTACH+a.MOVING+h.STATIC
 bpy.ops.wm.open_mainfile(filepath=str(h.SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();raw={n:a.rawsig(bpy.data.objects[n]) for n in names};base={n:a.geometry(bpy.data.objects[n]) for n in names};materials={m.name:sign.signature(m) for m in bpy.data.materials};protected=a.a.protected();baselineEyeFrames={}
 frames=[1,37,49] if MINIMUM else list(range(1,50))
 for f in frames:
  bpy.context.scene.frame_set(f);bpy.context.view_layer.update();baselineEyeFrames[f]={n:a.geometry(bpy.data.objects[n])[0] for n in a.MOVING}
 bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];assert a.a.protected()==protected and {m.name:sign.signature(m) for m in bpy.data.materials if m.name in materials}==materials
 for n in names:assert a.rawsig(bpy.data.objects[n])==raw[n]
 weights=np.load(E/'native-current-lid-skinning.npz');construction=json.loads((E/'native-lid-follow-construction.json').read_text('utf-8'));skinWeights=weights['skinWeights'];allWeights={h.SKIN:skinWeights,**{n:weights[n+'Weights'] for n in h.ATTACH}};neutral={n:hashes(n) for n in names};fixed={n:hashes(n) for n in h.STATIC};centers={side:np.array(rig.data.bones[a.bone_names()[side]].head_local) for side in ['L','R']};rows=[];movement={n:0. for n in allWeights};outside=np.flatnonzero(skinWeights[:,1:].sum(1)==0);outRest=a.geometry(bpy.data.objects[h.SKIN])[0][outside].copy();stage=setup('face')
 for f in frames:
  s.frame_set(f);bpy.context.view_layer.update();assert all(hashes(n)==v for n,v in fixed.items());assert np.array_equal(a.geometry(bpy.data.objects[h.SKIN])[0][outside],outRest);errors={}
  for n in allWeights:
   P=base[n][0];WW,TT=a.geometry(bpy.data.objects[n]);ww=allWeights[n];expected=P*ww[:,0,None]
   for j,((side,kind),bone) in enumerate(h.BONES.items(),1):
    eyeAngle=rig.pose.bones[a.bone_names()[side]].rotation_euler.x;factor=.75 if kind=='UPPER' else .35;angle=eyeAngle*factor;assert abs(rig.pose.bones[bone].rotation_euler.x-angle)<1e-7;expected+=ww[:,j,None]*((P-centers[side])@Rx(angle).T+centers[side])
   err=float(np.linalg.norm(WW-expected,axis=1).max());assert err<1e-6,(n,f,err);errors[n]=err;movement[n]=max(movement[n],float(np.linalg.norm(WW-base[n][0],axis=1).max()))
  for n in a.MOVING:assert np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-baselineEyeFrames[f][n],axis=1).max()<5e-7
  rows.append({'frame':f,'independentNativeWeightedRotationErrorM':errors,'eyeAngles':a.angles(rig),'lidXDegrees':{n:math.degrees(rig.pose.bones[n].rotation_euler.x) for n in h.BONES.values()}})
 assert movement[h.SKIN]>.0005 and all(v>.0001 for v in movement.values());s.frame_set(1);bpy.context.view_layer.update();assert all(hashes(n)==v for n,v in neutral.items())
 action=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 rig.pose.bones[a.bone_names()['L']].rotation_euler.x=math.radians(-5);bpy.context.view_layer.update();single={}
 for n in allWeights:
  WW,TT=a.geometry(bpy.data.objects[n]);P=base[n][0];left=P[:,0]>0;delta=np.linalg.norm(WW-P,axis=1);single[n]={'leftMaxMovementM':float(delta[left].max()),'rightMaxMovementFromSourceM':float(delta[~left].max())};assert single[n]['leftMaxMovementM']>.0001 and single[n]['rightMaxMovementFromSourceM']<1e-6
 # Driver mute must remove real visible deformation while actual eye stays up.
 drivers=[f for f in rig.animation_data.drivers if 'AFN139_' in f.data_path];assert len(drivers)==4 and all(f.driver.is_valid for f in drivers)
 for f in drivers:f.mute=True
 for n in h.BONES.values():rig.pose.bones[n].rotation_euler=(0,0,0)
 bpy.context.view_layer.update();muted={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-base[n][0],axis=1).max()) for n in allWeights};assert max(muted.values())<1e-6
 for f in drivers:f.mute=False
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 rig.animation_data.action=action;rig.animation_data.action_slot=slot;s.frame_set(1);bpy.context.view_layer.update();assert all(hashes(n)==v for n,v in neutral.items())
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
 result={'source':str(src),'sha256':build['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualControlSkinLashWetLineMoved':movement,'nativeBoneGeometryFrames':rows,'allRawGeometryTopologyUVAndOriginalMaterialGraphsExact':True,'originalEyeGeometryAndRangeRetained':True,'otherVisibleLayersAndOutsideLidSupportFixed':True,'independentLeftEyePitch5Deg':single,'actualFollowDriversValid':True,'driverMuteActualSkinLashWetLineReturnErrorM':muted,'actualNeutralAndControlStateRestored':True,'allReferencedExternalTextures':textures,'minimumOnlyAfterVisibleFailure':MINIMUM,'numericSkinningErrorBoundM':1e-6,'boundIsEvaluationNotContactTolerance':True,'nativeAttachmentSourceMaximumRestGapsM':{n:r['restAttachmentDistanceMaxM'] for n,r in construction['actualAttachments'].items()},'attachmentOffsetsAndUniformLashIslandWeightsAreNotFollicleOrRenderOccupancyProof':True,'appearanceCompleteOperationFiniteContactAndRuntimeAcceptance':False,'seconds':time.time()-tick};save('minimum-saved-native-lid-readback.json',result)
 if MINIMUM:assert a.a.sha(src)==build['sha256'];print('R139_MINIMUM_ACTUAL_NATIVE_LID_EDIT_RESTORE_DONE',time.time()-tick,flush=True);return
 # Test the exact original failure pose first; both geometries move now.
 contacts=[];bad=False
 def pose(label):
  nonlocal bad
  W,T=a.geometry(bpy.data.objects[h.SKIN]);Skin=W[T];lo=Skin.min(1);hi=Skin.max(1)
  for n in a.MOVING:
   V,F=a.geometry(bpy.data.objects[n]);r=c.query(Skin,V[F],lo,hi);contacts.append({'pose':label,'object':n,'actualSkinWorldHash':a.a.hasharray(W),'actualOcularWorldHash':a.a.hasharray(V),'actualSkinTriangles':len(T),'actualOcularTriangles':len(F),'properSurfaceCrossings':len(r['properCrossings']),'allSurfaceContactPairs':len(r['intersections']),'degenerateCandidatePairs':r['degenerateCandidatePairs'],'firstProperSkinEyePairs':r['properCrossings'][:20].tolist()});bad=bad or bool(len(r['intersections']) or r['degenerateCandidatePairs'])
 rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(math.radians(-10),0,math.radians(-20))
 bpy.context.view_layer.update();pose('original-failure-yaw-20-pitch+10')
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 rig.animation_data.action=action;rig.animation_data.action_slot=slot;s.frame_set(1);bpy.context.view_layer.update();pose('neutral')
 if not bad:
  for f in range(1,50):
   s.frame_set(f);bpy.context.view_layer.update();pose('native-frame-%03d'%f)
   if bad:break
 if not bad:
  rig.animation_data.action=None
  for yaw in [-20,-10,0,10,20]:
   for pitch in [-10,0,10]:
    for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(math.radians(-pitch),0,math.radians(yaw))
    bpy.context.view_layer.update();pose('manual-yaw%+d-pitch%+d'%(yaw,pitch))
    if bad:break
   if bad:break
  for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
  rig.animation_data.action=action;rig.animation_data.action_slot=slot
 s.frame_set(1);bpy.context.view_layer.update();assert all(hashes(n)==v for n,v in neutral.items());save('actual-lid-ocular-surface-contact.json',{'source':str(src),'sha256':build['sha256'],'actualDeformedSkinAndActualEyePerPose':True,'skinNotFrozenToBaseline':True,'cases':contacts,'relatedRawSurfaceFailureObserved':bad,'allRequestedPoseObjectCasesCompleted':len(contacts)==132,'numericPredicateEpsilonM':c.EPS,'method':'Unchanged all actual displayed triangle AABB/SAT/coplanar coverage; no result exclusion or smaller poses.','globalSignedMinimumM':None,'finiteThicknessContainmentAlphaOpticalWetLayerSelfAndContinuousAccepted':False,'neutralRestored':True,'earlyStopAfterRelatedKnownFailure':bad,'seconds':time.time()-tick})
 # Matched baseline failure-pose image under the same actual primary stage.
 bpy.ops.wm.open_mainfile(filepath=str(h.SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();baseStage=setup('face');assert baseStage==stage;rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(math.radians(-10),0,math.radians(-20))
 bpy.context.view_layer.update();s.render.filepath=str(E/'matched-baseline-diagonal-yaw-20-pitch+10-face.png');bpy.ops.render.render(write_still=True);save('matched-baseline-diagonal-controls.json',{'baseline':str(h.SRC),'candidate':str(src),'actualPrimaryStageExactlyEqual':True,'stage':stage,'yawDeg':-20,'pitchDeg':10,'bothActualEyeAnglesRetained':True,'baselineImage':s.render.filepath})
 assert a.a.sha(src)==build['sha256'];print('R139_ACTUAL_NATIVE_LID_CONTROL_CONTACT_AND_MATCHED_FAILURE_POSE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
