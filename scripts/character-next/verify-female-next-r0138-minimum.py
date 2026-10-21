"""Independent reopen, evaluated native gaze and actual ocular/skin surfaces.
Finite thickness/containment, continuous all-avatar contacts remain unaccepted.
"""
from pathlib import Path
import bpy,numpy as np,json,time,math,importlib.util
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
c=module('r138verifycontact','contact-female-next-r0138-ocular-surfaces.py');a=c.a;E=a.E
sign=module('r138verifysign','build-female-next-r0131-native-hair-material.py');a.b.u.v.E=E
def save(n,x):a.save(n,x)
def hgeom(o):return [a.a.hasharray(x) for x in a.geometry(o)]
def stage(scene):
 def mat(o):return [list(r) for r in o.matrix_world]
 return {'camera':mat(scene.camera),'lens':scene.camera.data.lens,'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,'lights':{o.name:{'matrix':mat(o),'energy':o.data.energy,'colour':list(o.data.color),'type':o.data.type} for o in scene.objects if o.type=='LIGHT'},'res':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'samples':scene.cycles.samples,'seed':scene.cycles.seed}
def rotation(yaw,pitch):
 y=math.radians(yaw);p=math.radians(-pitch);cy,sy,cp,sp=math.cos(y),math.sin(y),math.cos(p),math.sin(p);return np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])@np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();base={n:a.geometry(bpy.data.objects[n]) for n in a.MOVING+a.FIXED};raw={n:a.rawsig(bpy.data.objects[n]) for n in a.MOVING};mats={m.name:sign.signature(m) for m in bpy.data.materials};protected=a.a.protected();results={}
 for tag in ['a','b']:
  build=json.loads((E/(tag+'-build-summary.json')).read_text('utf-8'));src=Path(build['output']);assert a.a.sha(src)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];assert rig.animation_data.action.name=='AFN138_NATIVE_CURRENT_GAZE_DEMO';assert a.a.protected()==protected
  assert {m.name:sign.signature(m) for m in bpy.data.materials if m.name in mats}==mats
  fixed={n:hgeom(bpy.data.objects[n]) for n in a.FIXED};neutral={n:a.geometry(bpy.data.objects[n])[0] for n in a.MOVING};ownNeutral={n:hgeom(bpy.data.objects[n]) for n in a.MOVING}
  for n in a.MOVING:assert a.rawsig(bpy.data.objects[n])==raw[n]
  for n in a.FIXED[1:]:assert fixed[n]==[a.a.hasharray(x) for x in base[n]]
  if tag=='a':assert fixed[a.FIXED[0]]==[a.a.hasharray(x) for x in base[a.FIXED[0]]]
  centers={side:np.array(rig.data.bones[name].head_local,dtype='f8') for side,name in a.bone_names().items()};rows=[];bounds=[];eyeMotion={n:0. for n in a.MOVING}
  # Same neutral stage held through all 49 actual frames and independent edits.
  mm=a.b.u.v.image.__globals__['m'];mm.rig.shade.settings();mm.rig.k.b.camera('face');bpy.context.view_layer.update();stageBefore=stage(scene)
  for f in range(1,50):
   scene.frame_set(f);bpy.context.view_layer.update();assert stage(scene)==stageBefore;assert all(hgeom(bpy.data.objects[n])==v for n,v in fixed.items());errors={}
   for n in a.MOVING:
    W,T=a.geometry(bpy.data.objects[n]);V,F=base[n];target=V.copy()
    for side,name in a.bone_names().items():
     ids=V[:,0]>0 if side=='L' else V[:,0]<0;pb=rig.pose.bones[name];yaw=math.degrees(pb.rotation_euler.z);pitch=-math.degrees(pb.rotation_euler.x);assert abs(yaw)<=20.00001 and abs(pitch)<=10.00001;target[ids]=(V[ids]-centers[side])@rotation(yaw,pitch).T+centers[side]
    err=float(np.linalg.norm(W-target,axis=1).max());assert err<1e-6,('Actual native geometry does not follow declared eye rotation',tag,f,n,err);errors[n]=err;eyeMotion[n]=max(eyeMotion[n],float(np.linalg.norm(W-neutral[n],axis=1).max()))
   rows.append({'frame':f,'boneEulerDegrees':a.angles(rig),'independentAnalyticMaxErrorM':errors})
  assert all(x>.002 for x in eyeMotion.values());scene.frame_set(1);bpy.context.view_layer.update();assert all(hgeom(bpy.data.objects[n])==v for n,v in ownNeutral.items())
  action=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=None
  for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
  rig.pose.bones[a.bone_names()['L']].rotation_euler.z=math.radians(5);bpy.context.view_layer.update();leftOnly={}
  for n in a.MOVING:
   W,T=a.geometry(bpy.data.objects[n]);ids=base[n][0][:,0]>0;dl=float(np.linalg.norm(W[ids]-neutral[n][ids],axis=1).max());dr=float(np.linalg.norm(W[~ids]-neutral[n][~ids],axis=1).max());assert dl>.0005 and dr<1e-9;leftOnly[n]={'leftMovementM':dl,'rightMovementM':dr}
  rig.pose.bones[a.bone_names()['L']].rotation_euler=(0,0,0);rig.animation_data.action=action;rig.animation_data.action_slot=slot;scene.frame_set(1);bpy.context.view_layer.update();assert all(hgeom(bpy.data.objects[n])==v for n,v in ownNeutral.items())
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
  result={'source':str(src),'sha256':build['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'rawEyeGeometryTopologyUVExact':True,'allOriginalMaterialGraphsExact':True,'hiddenRollbackExact':True,'otherVisibleLayersExactToR126':True,'actualCurrentSkinFixedDuringGaze':True,'all49Frames':rows,'maxActualOcularDisplacementM':eyeMotion,'leftEyeOnly5DegActualMovement':leftOnly,'actualGeometryAndActionNeutralRestored':True,'actualStageInvariantAcross49Frames':True,'analyticEvaluationNumericBoundM':1e-6,'evaluationBoundIsNotContactTolerance':True,'allReferencedExternalTextures':textures,'finiteContainmentContinuousAndRuntimeAccepted':False};results[tag]=result;save('minimum-saved-native-gaze-readback.json',{'sources':results,'seconds':time.time()-tick})
  if tag=='a':continue
  # Full actual triangle surface tests at every native action frame and all
  # independent diagonal engineering extrema. No vertex-only substitute.
  W,T=a.geometry(bpy.data.objects[a.FIXED[0]]);Skin=W[T];lo=Skin.min(1);hi=Skin.max(1);contacts=[];bad=False
  def contact(label):
   nonlocal bad
   for n in a.MOVING:
    V,F=a.geometry(bpy.data.objects[n]);r=c.query(Skin,V[F],lo,hi);row={'pose':label,'object':n,'skinTriangles':len(T),'ocularTriangles':len(F),'aabbCandidatePairs':r['candidatePairs'],'properSurfaceCrossingPairs':len(r['properCrossings']),'allSurfaceContactPairs':len(r['intersections']),'coplanarPairs':len(r['coplanarContacts']),'degenerateCandidatePairs':r['degenerateCandidatePairs'],'firstCrossings':r['properCrossings'][:20].tolist()};contacts.append(row);bad=bad or bool(len(r['intersections']) or r['degenerateCandidatePairs'])
  for f in range(1,50):
   scene.frame_set(f);bpy.context.view_layer.update();contact('native-frame-%03d'%f)
   if bad:break
  if not bad:
   rig.animation_data.action=None
   for yaw in [-20,-10,0,10,20]:
    for pitch in [-10,0,10]:
     for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(math.radians(-pitch),0,math.radians(yaw))
     bpy.context.view_layer.update();contact('manual-yaw%+d-pitch%+d'%(yaw,pitch))
     if bad:break
    if bad:break
   for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(0,0,0)
   rig.animation_data.action=action;rig.animation_data.action_slot=slot
  scene.frame_set(1);bpy.context.view_layer.update();assert all(hgeom(bpy.data.objects[n])==v for n,v in ownNeutral.items()) and all(hgeom(bpy.data.objects[n])==v for n,v in fixed.items())
  result['relatedOcularSkinSurfaceFailureObserved']=bad;save('b-actual-ocular-surface-contact.json',{'source':str(src),'sha256':build['sha256'],'cases':contacts,'relatedSurfaceCrossingContactOrDegeneracyObserved':bad,'allRequestedDiscretePosesCompleted':len(contacts)==128,'numericPredicateEpsilonM':c.EPS,'method':'Unchanged all actual triangle AABB/SAT/coplanar predicate from source diagnostic. Every final displayed ocular/skin triangle participates; no result-dependent exclusion or smaller pose. Actual anatomical Boolean cavity reconstruction is recorded separately.','actualFullBoneActionAndManualDiagonalPoses':True,'finiteThicknessContainmentGlobalSignedMinimumAndContinuousAccepted':False,'globalSignedMinimumM':None,'contactRepresentation':'Evaluated raw geometric Eye/EyeScleraReflect vs reconstructed skin triangle surfaces. No opacity, alpha or refractive optical/wet-layer occupied-volume interpretation; no all-avatar claim.','neutralRestored':True,'seconds':time.time()-tick})
  save('minimum-saved-native-gaze-readback.json',{'sources':results,'seconds':time.time()-tick})
  # Two actual diagonal corners show combined native controls, same full head.
  if not bad:
   rig.animation_data.action=None
   for yaw,pitch in [(-20,10),(20,-10)]:
    for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(math.radians(-pitch),0,math.radians(yaw))
    bpy.context.view_layer.update();scene.render.filepath=str(E/('b-diagonal-yaw%+d-pitch%+d-face.png'%(yaw,pitch)));bpy.ops.render.render(write_still=True)
   for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(0,0,0)
   rig.animation_data.action=action;rig.animation_data.action_slot=slot;scene.frame_set(1);bpy.context.view_layer.update()
  if not bad:
   mm.rig.k.b.camera('body-face');bpy.context.view_layer.update();bodyStage=stage(scene);bodyRows=[]
   for f in [9,25,37,45,49]:
    scene.frame_set(f);bpy.context.view_layer.update();assert stage(scene)==bodyStage;file=E/('b-gaze-body-frame-%03d.png'%f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);bodyRows.append({'frame':f,'file':str(file),'stage':bodyStage,'actualBoneEulerDegrees':a.angles(rig)})
   save('b-actual-gaze-body-controls.json',bodyRows);scene.frame_set(1);bpy.context.view_layer.update()
  assert a.a.sha(src)==build['sha256'] and a.a.protected()==protected
 print('R138_NATIVE_GAZE_INDEPENDENT_REOPEN_ACTUAL_GEOMETRY_AND_CONTACT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
