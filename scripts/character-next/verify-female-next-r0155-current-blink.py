"""Independent real poses, preservation/restoration, then cheap coverage falsifier."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0155-native-blink'
sp=importlib.util.spec_from_file_location('r155readback',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def gh(names):return {n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}
def main():
 tick=time.time();before=json.loads((E/'manifest-before.json').read_text());src=before['workingCompleteWomanReference'];bpy.ops.wm.open_mainfile(filepath=src['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};baseline={}
 for frame in range(1,50):s.frame_set(frame);bpy.context.view_layer.update();baseline[frame]=gh(names)
 results=[]
 for label in ['a','b']:
  b=json.loads((E/(label+'-build-summary.json')).read_text());assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];s.frame_set(1);bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in names};assert gh(names)==baseline[1];blinkAction=rig.animation_data.action;slot=rig.animation_data.action_slot;gaze=bpy.data.actions[b['originalGazeAction']];rig.animation_data.action=gaze
  for p in ['blink_L','blink_R']:rig[p]=0.
  rig.update_tag();bpy.context.view_layer.update()
  for frame in range(1,50):s.frame_set(frame);bpy.context.view_layer.update();assert gh(names)==baseline[frame],('Protected gaze changed',label,frame)
  rig.animation_data.action=blinkAction;rig.animation_data.action_slot=slot;s.frame_set(1);bpy.context.view_layer.update();rest={n:a.geometry(bpy.data.objects[n])[0].copy() for n in names};rows=[];movement={n:0. for n in [names[0],*h.h.ATTACH]}
  for frame in range(1,25):
   s.frame_set(frame);bpy.context.view_layer.update();controls=[float(rig[p]) for p in ['blink_L','blink_R']];assert all(-1e-7<=v<=1.0000001 for v in controls)
   for n in movement:movement[n]=max(movement[n],float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-rest[n],axis=1).max()))
   for n in [a.FIXED[1],a.FIXED[4],*a.MOVING]:assert np.array_equal(a.geometry(bpy.data.objects[n])[0],rest[n])
   rows.append({'frame':frame,'controls':controls})
  assert all(v>1e-4 for v in movement.values());s.frame_set(24);bpy.context.view_layer.update();restoration={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-rest[n],axis=1).max()) for n in names};assert max(restoration.values())==0;s.frame_set(1);bpy.context.view_layer.update();results.append({'label':label,'source':b['output'],'sha256':b['sha256'],'originalSevenRawMeshesUVAndAll49GazePosesExact':True,'actual24BlinkFrames':rows,'maximumActualLayerMovementM':movement,'originalUnchangedHairMouthAndEyesExact':True,'neutralRestorationM':restoration,'completedClosureNotProvedByMovement':True})
  h.save('independent-current-blink-readback.json',{'results':results,'completeOperationAccepted':False,'gazePreservationAndMotionRestorationOnly':True})
 # B is still a failed/incomplete closure if real eye surface remains uncovered.
 s.frame_set(11);bpy.context.view_layer.update();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];V,T=a.geometry(skin);tree=BVHTree.FromPolygons([Vector(x) for x in V],T.tolist(),all_triangles=True);a.b.u.v.m.rig.k.b.camera('face');bpy.context.view_layer.update();origin=s.camera.matrix_world.translation.copy();eye=bpy.data.objects[a.MOVING[0]];W,F=a.geometry(eye);eyeTree=BVHTree.FromPolygons([Vector(x) for x in W],F.tolist(),all_triangles=True);witness=[];tested=0
 for target in W[F].mean(1):
  direction=Vector(target)-origin;direction.normalize();ep,_,efi,ed=eyeTree.ray_cast(origin,direction,2.);tested+=1
  if ep is None:continue
  sp,_,sfi,sd=tree.ray_cast(origin,direction,2.)
  if sp is None or sd-ed>.001:
   witness.append({'eyeFace':int(efi),'eyeWorld':list(ep),'eyeDistanceM':ed,'firstSkinFace':int(sfi) if sp is not None else None,'firstSkinWorld':list(sp) if sp is not None else None,'firstSkinDistanceM':sd if sp is not None else None,'eyeBeforeSkinM':sd-ed if sp is not None else None,'rayOriginWorld':list(origin),'rayDirectionWorld':list(direction)})
   if len(witness)>=12:break
 h.save('closed-eye-skin-coverage-witness.json',{'candidate':'b','frame':11,'blinkControls':[float(rig[p]) for p in ['blink_L','blink_R']],'actualSkinTriangles':len(T),'actualEyeTriangles':len(F),'sampledEyeTriangleCentroidRaysTested':tested,'uncoveredEyePointWitnesses':witness,'witnessMeaning':'Concrete perspective rays where actual eye mesh is at least1mm before first actual Skin hit, or no Skin hit. Skin coverage gap witnesses only;1mm is conservative witness selection, never contact/closure acceptance tolerance. No absence/global visibility/pass inferred from sampling; lashes/hair/wet alpha are not inferred as opaque coverage.','finiteThicknessSelfContinuousContactAccepted':False,'completeBlinkAccepted':False})
 # Fresh independent read renders demonstrate the delivered source, not the
 # inconsistent first in-memory B capture. Existing open frame24 is retained.
 clip=[]
 for frame,view,tag in [(9,'face','b-reopened-half-face'),(11,'body-face','b-reopened-closed-body')]:
  s.frame_set(frame);bpy.context.view_layer.update();a.b.u.v.m.rig.shade.settings();a.b.u.v.m.rig.k.b.camera(view);s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/(tag+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);clip.append({'frame':frame,'view':view,'file':s.render.filepath,'blink_L':float(rig['blink_L']),'blink_R':float(rig['blink_R']),'actualSkinHash':a.a.hasharray(a.geometry(skin)[0]),'camera':np.array(s.camera.matrix_world).tolist(),'resolution':320,'samples':8,'seed':s.cycles.seed,'exposure':s.view_settings.exposure})
 h.save('b-independent-reopened-view-controls.json',clip);s.frame_set(1);bpy.context.view_layer.update();assert gh(names)==baseline[1];print('R155_INDEPENDENT_AB_49_GAZE_24_BLINK_RESTORE_COVERAGE_WITNESS_DONE',len(witness),time.time()-tick,flush=True)
if __name__=='__main__':main()
