"""Independent displayed-skin blink/restoration and actual deformed eye-surface checks."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0144-current-skin-blink'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
h=module('r144readback','build-female-next-r0144-current-skin-blink.py');a=h.a;contact=module('r144contact','contact-female-next-r0138-ocular-surfaces.py');sig=module('r144materials','build-female-next-r0131-native-hair-material.py')
def save(n,x):h.save(n,x)
def snapshot(names):return {n:a.geometry(bpy.data.objects[n]) for n in names}
def polygon_signature(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.data;loops=np.empty(len(mesh.loops),dtype='i4');mesh.loops.foreach_get('vertex_index',loops);counts=np.empty(len(mesh.polygons),dtype='i4');mesh.polygons.foreach_get('loop_total',counts)
 return {'loopVertexHash':a.a.hasharray(loops),'faceLoopCountsHash':a.a.hasharray(counts),'polygons':len(mesh.polygons),'vertices':len(mesh.vertices)}

def eye_controls(rig):return {n:list(rig.pose.bones[n].rotation_euler) for n in a.bone_names().values()}

def main():
 tick=time.time();build=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(build['output']);sha=build['sha256'];assert a.a.sha(src)==sha;affected=[h.h.SKIN]+h.h.ATTACH+a.MOVING;names=a.FIXED+a.MOVING
 bpy.ops.wm.open_mainfile(filepath=str(h.SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();protected=a.a.protected();raw={n:a.rawsig(bpy.data.objects[n]) for n in names};materials={m.name:sig.signature(m) for m in bpy.data.materials};baseline=snapshot(names);originalAction=bpy.data.objects[build['actualRig']].animation_data.action.name;reference={};referencePolygons={};referenceControls={}
 for f in range(1,50):
  scene.frame_set(f);bpy.context.view_layer.update();reference[f]=snapshot(affected);referencePolygons[f]={n:polygon_signature(bpy.data.objects[n]) for n in affected};referenceControls[f]=eye_controls(bpy.data.objects[build['actualRig']])
 bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;rig=bpy.data.objects[build['actualRig']];skin=bpy.data.objects[h.h.SKIN];scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected
 assert {n:a.rawsig(bpy.data.objects[n]) for n in names}==raw and {m.name:sig.signature(m) for m in bpy.data.materials if m.name in materials}==materials
 assert skin.modifiers[0].name=='AFN144_ACTUAL_DISPLAYED_SKIN_BLINK' and skin.modifiers[1].type=='ARMATURE'
 # Original displayed meshes remain the authoritative targets; no helper mesh substitutes.
 demo=rig.animation_data.action;demoSlot=rig.animation_data.action_slot;rig.animation_data.action=bpy.data.actions[originalAction]
 for p in h.PROPS.values():rig[p]=0.
 rig.update_tag();gaze=[]
 for f in range(1,50):
  scene.frame_set(f);bpy.context.view_layer.update();now=snapshot(affected);errors={}
  for n in affected:
   assert polygon_signature(bpy.data.objects[n])==referencePolygons[f][n],(f,n,'evaluated polygon loops changed');assert now[n][0].shape==reference[f][n][0].shape;errors[n]=float(np.linalg.norm(now[n][0]-reference[f][n][0],axis=1).max());assert errors[n]<2e-6,(f,n,errors[n])
  assert eye_controls(rig)==referenceControls[f],(f,'native eye controls changed')
  gaze.append({'frame':f,'maximumActualVertexDeviationM':errors,'actualNativeEyeControls':eye_controls(rig),'exactEvaluatedPolygonLoopsAndCounts':True,'derivedTriangleRowsDifferent':{n:int(np.any(now[n][1]!=reference[f][n][1],axis=1).sum()) for n in affected},'originalActualEyeMovementFromNeutralM':{n:float(np.linalg.norm(reference[f][n][0]-reference[1][n][0],axis=1).max()) for n in a.MOVING}})
 assert max(max(x['originalActualEyeMovementFromNeutralM'].values()) for x in gaze)>.001
 save('original-gaze49-preservation-readback.json',{'source':str(src),'sha256':sha,'all49ActualGazeFrames':gaze,'exactUnderlyingEvaluatedPolygonTopology':True,'derivedTriangleArraysNotClaimedExact':True,'numericEvaluationBoundNotContactToleranceM':2e-6,'originalSourceEyeMovementRequiredAboveM':.001,'seconds':time.time()-tick})
 del reference
 rig.animation_data.action=demo;rig.animation_data.action_slot=demoSlot;scene.frame_set(1);bpy.context.view_layer.update();base=snapshot(names);neutral={n:float(np.linalg.norm(base[n][0]-baseline[n][0],axis=1).max()) for n in names};assert max(neutral.values())<2e-6
 display={n:{'hideRender':bpy.data.objects[n].hide_render,'type':bpy.data.objects[n].type,'materials':[m.name if m is not None else None for m in bpy.data.objects[n].data.materials]} for n in names};a.b.u.v.image.__globals__['m'].rig.shade.settings();bpy.context.view_layer.update();assert display=={n:{'hideRender':bpy.data.objects[n].hide_render,'type':bpy.data.objects[n].type,'materials':[m.name if m is not None else None for m in bpy.data.objects[n].data.materials]} for n in names}
 actual=[];cases=[];details={};bad=False;firstFailure=None;maxMove={n:0. for n in affected};alpha1Geometry=None
 for f in range(1,18):
  scene.frame_set(f);bpy.context.view_layer.update();now=snapshot(names);W,T=now[h.h.SKIN];assert np.isfinite(W).all();assert all(np.isfinite(V).all() for V,F in now.values());props={s:float(rig[p]) for s,p in h.PROPS.items()}
  for n in affected:maxMove[n]=max(maxMove[n],float(np.linalg.norm(now[n][0]-base[n][0],axis=1).max()))
  actual.append({'frame':f,'actualControls':props,'skinWorldHash':a.a.hasharray(W),'actualAllDisplayedLayersFinite':True})
  if f==9:alpha1Geometry=now
  if not bad:
   Skin=W[T];low=Skin.min(1);high=Skin.max(1)
   for n in a.MOVING:
    V,F=now[n];r=contact.query(Skin,V[F],low,high);key='frame%03d-'%f+n;details[key+'-proper']=r['properCrossings'];details[key+'-all']=r['intersections'];failure=len(r['intersections'])>0 or r['degenerateCandidatePairs']>0
    row={'pose':'native-blink-%03d'%f,'frame':f,'actualControls':props,'object':n,'actualSkinFaces':len(T),'actualEyeFaces':len(F),'actualSkinWorldHash':a.a.hasharray(W),'actualEyeWorldHash':a.a.hasharray(V),'aabbCandidatePairs':r['candidatePairs'],'properTriangleSurfaceCrossingPairs':len(r['properCrossings']),'allTriangleSurfaceContactPairs':len(r['intersections']),'coplanarContactPairs':len(r['coplanarContacts']),'degenerateCandidatePairs':r['degenerateCandidatePairs'],'firstProperSkinEyeFacePairs':r['properCrossings'][:20].tolist(),'allActualTriangleFacesCoveredNotVertexSamples':True};cases.append(row)
    if failure:bad=True;firstFailure=row;break
 # Preserve any original contact witnesses before independent controller checks.
 np.savez_compressed(E/'actual-blink-ocular-surface-contact-pairs.npz',**details)
 save('actual-blink-ocular-surface-contact.json',{'source':str(src),'sourceSha256':sha,'cases':cases,'allRequested17FrameTwoObjectCasesCompleted':not bad and len(cases)==34,'relatedRawSurfaceFailureObserved':bad,'firstRelatedFailure':firstFailure,'earlyStopAfterRelatedKnownFailure':bad,'actualSkinReevaluatedPerPoseNotFrozen':True,'numericPredicateEpsilonM':contact.EPS,'epsilonIsNumericalClassificationNotPhysicalClearanceTolerance':True,'method':'All actual evaluated native Skin and Eye/reflect triangles per sampled pose. Float64 AABB candidate coverage and original SAT predicate with coplanar axes.','noFailingFacesRemovedNoEyeScaledNoRangeShrunkNoToleranceRelaxed':True,'globalSignedMinimumM':None,'finiteThicknessContainmentLidSelfOtherLayersAlphaAndContinuousAccepted':False,'seconds':time.time()-tick})
 # Independent actual manual control, unilateral isolation, and exact return.
 rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 for p in h.PROPS.values():rig[p]=0.
 rig.update_tag();bpy.context.view_layer.update();rest=snapshot(names);manual=[]
 for l,r in [(1.,0.),(0.,1.),(.5,.5),(1.,1.),(0.,0.)]:
  rig[h.PROPS['L']]=l;rig[h.PROPS['R']]=r;rig.update_tag();bpy.context.view_layer.update();now=snapshot(names);movement={n:float(np.linalg.norm(now[n][0]-rest[n][0],axis=1).max()) for n in names};opposite=None
  if (l,r) in [(1.,0.),(0.,1.)]:
   unaffected=rest[h.h.SKIN][0][:,0]<-.002 if l else rest[h.h.SKIN][0][:,0]>.002;opposite=float(np.linalg.norm(now[h.h.SKIN][0][unaffected]-rest[h.h.SKIN][0][unaffected],axis=1).max());assert opposite<2e-6
  if l or r:assert movement[h.h.SKIN]>.001
  else:assert max(movement.values())<2e-6
  manual.append({'L':l,'R':r,'actualDisplayedMeshMovementM':movement,'oppositeSideSkinMaxMovementM':opposite})
 rig.animation_data.action=demo;rig.animation_data.action_slot=demoSlot;scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();returned=snapshot(names);restore={n:float(np.linalg.norm(returned[n][0]-base[n][0],axis=1).max()) for n in names};assert max(restore.values())<2e-6 and a.a.protected()==protected
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
 assert a.a.sha(src)==sha;np.savez_compressed(E/'actual-blink-ocular-surface-contact-pairs.npz',**details)
 save('actual-blink-ocular-surface-contact.json',{'source':str(src),'sourceSha256':sha,'cases':cases,'allRequested17FrameTwoObjectCasesCompleted':not bad and len(cases)==34,'relatedRawSurfaceFailureObserved':bad,'firstRelatedFailure':firstFailure,'earlyStopAfterRelatedKnownFailure':bad,'actualSkinReevaluatedPerPoseNotFrozen':True,'numericPredicateEpsilonM':contact.EPS,'epsilonIsNumericalClassificationNotPhysicalClearanceTolerance':True,'method':'All actual evaluated native Skin and Eye/reflect triangles per sampled pose. Exact float64 AABB candidate coverage and original SAT predicate with coplanar axes.','noFailingFacesRemovedNoEyeScaledNoRangeShrunkNoToleranceRelaxed':True,'globalSignedMinimumM':None,'finiteThicknessContainmentLidSelfOtherLayersAlphaAndContinuousAccepted':False,'seconds':time.time()-tick})
 save('minimum-saved-current-skin-blink-readback.json',{'source':str(src),'sha256':sha,'bytes':src.stat().st_size,'independentlyReopened':True,'actualDisplayedSkinHasNativeBlinkModifier':True,'actualControllers':h.PROPS,'actualDisplayBeforeAndAfterPresetIdentical':True,'actualDisplay':display,'originalRawGeometryTopologyUVAndOriginalMaterialGraphsExact':True,'hiddenRollbackExact':True,'noForeignHairAssetOrClosingCapOrHiddenHeadOperationUsed':True,'neutralDisplayedGeometryErrorsM':neutral,'numericEvaluationBoundNotContactToleranceM':2e-6,'all49OriginalGazeFramesActualVerticesAndEvaluatedPolygonTopologyRetained':gaze,'derivedTriangleArrayEqualityNotClaimed':True,'triangulationDiagnostic':'gaze-topology-mismatch-diagnostic.json','originalFailedVerifierPreserved':'independent-verifier-as-executed-attempt1.py','all17ActualBlinkFrames':actual,'actualDisplayedMeshMaximumBlinkMovementM':maxMove,'independentActualManualControls':manual,'actualNeutralAndControlStateRestored':True,'actualRestorationErrorsM':restore,'allReferencedExternalTextures':textures,'relatedRawEyeSkinSurfaceFailureObserved':bad,'newCompleteUsableBlinkAcceptedByThisReadback':False,'completeAppearanceFunctionContactRuntimeNotAutomaticallyAccepted':True,'scope':'Saved actual current-skin control/geometry/restoration and original gaze preservation; visual operation judgment and contact are separate. Stop complete-operation acceptance on any related known failure. Finite/self/continuous/runtime and full anatomy remain unaccepted.','seconds':time.time()-tick})
 print('R144_INDEPENDENT_ACTUAL_BLINK_RESTORE_GAZE49_AND_DEFORMED_SURFACE_CHECK_DONE',bad,len(cases),max(restore.values()),time.time()-tick,flush=True)
if __name__=='__main__':main()
