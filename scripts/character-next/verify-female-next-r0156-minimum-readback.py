"""Minimum rejected-source/archive reopen and local counterexample check only."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0156-anatomical-blink';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('r156verify','build-female-next-r0156-anatomical-blink.py');a=h.a;c=mod('r156contact','contact-female-next-r0138-ocular-surfaces.py');w=mod('r156edge','build-female-next-r0138-native-sockets.py')
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
tick=time.time();b=json.loads((E/'a-build-summary.json').read_text());old=Path(b['source']);bpy.ops.wm.open_mainfile(filepath=str(old));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};rest={n:a.geometry(bpy.data.objects[n])[0] for n in names};rig=bpy.data.objects[b['actualRig']];rig.animation_data.action=bpy.data.actions[b['originalGazeAction']]
for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(0,0,0)
for prop in ['blink_L','blink_R']:rig[prop]=0.
s.frame_set(9);bpy.context.view_layer.update();gaze={n:a.geometry(bpy.data.objects[n])[0] for n in names}
p=M/'r0156-source'/Path(b['output']).name;assert a.a.sha(p)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in names};assert all(np.array_equal(a.geometry(bpy.data.objects[n])[0],rest[n]) for n in names);rig=bpy.data.objects[b['actualRig']];action=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=bpy.data.actions[b['originalGazeAction']]
for prop in ['blink_L','blink_R']:rig[prop]=0.
s.frame_set(9);bpy.context.view_layer.update();assert all(np.array_equal(a.geometry(bpy.data.objects[n])[0],gaze[n]) for n in names);rig.animation_data.action=action;rig.animation_data.action_slot=slot
for name in a.bone_names().values():rig.pose.bones[name].rotation_euler=(0,0,0)
rig.update_tag();rows=[]
for frame in [1,9,11,24]:
 s.frame_set(frame);bpy.context.view_layer.update();delta={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-rest[n],axis=1).max()) for n in names};rows.append({'frame':frame,'blink':[float(rig[x]) for x in ['blink_L','blink_R']],'layerMovementMaximumM':delta})
assert max(rows[-1]['layerMovementMaximumM'].values())==0
textures=[];libs=[]
for lib in bpy.data.libraries:
 q=Path(bpy.path.abspath(lib.filepath)).resolve();assert q.is_relative_to(M.resolve());libs.append({'file':str(q),'sha256':a.a.sha(q)})
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and im.filepath:
  q=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert q.is_relative_to(M.resolve()) and q.is_file();textures.append({'file':str(q),'sha256':a.a.sha(q)})
assert len(textures)==16 and len(libs)==1
s.frame_set(11);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];V,T=a.geometry(skin);ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();poly=np.empty(len(mesh.loop_triangles),'i4');mesh.loop_triangles.foreach_get('polygon_index',poly);ev.to_mesh_clear();ids=np.flatnonzero(poly==186630);assert len(ids)==8;cases=[]
for name in a.MOVING:
 W,F=a.geometry(bpy.data.objects[name]);result=c.query(V[T[ids]],W[F],V[T[ids]].min(1),V[T[ids]].max(1));pairs=result['properCrossings'];cases.append({'object':name,'actualTestedSkinTriangles':len(ids),'actualTestedEyeTriangles':len(F),'properCrossingPairs':len(pairs),'firstWitnesses':[{'actualSkinTriangle':int(ids[si]),'eyeTriangle':int(ei),'independentFiniteEdgeFaceWitnesses':w.witness(V[T[ids[si]]],W[F[ei]])} for si,ei in pairs[:3]],'scopedOnlyOriginalImplicatedPolygon':True})
save('original-failed-wall-only-contact-readback.json',{'frame':11,'originalRawPolygon':186630,'cases':cases,'numericEpsilonM':1e-12,'wholeSkinOtherPosesFiniteSelfContinuousNotCheckedOrAccepted':True,'zeroLocalCrossingsWouldNotEstablishBlinkAcceptance':True})
s.frame_set(1);bpy.context.view_layer.update();assert all(np.array_equal(a.geometry(bpy.data.objects[n])[0],rest[n]) for n in names);assert a.a.sha(p)==b['sha256'];save('independent-minimum-source-archive-readback.json',{'source':str(p),'sha256':b['sha256'],'rawSevenMeshesUVAndNeutralExact':True,'recordedGazeFrame9ExactAgainst155B':True,'all49GazeNotRepeatedAfterVisibleRejection':True,'actualBlinkReadback':rows,'allSevenRestorationM':0,'relativeTexturesWithinArchive':textures,'relativeLibrariesWithinArchive':libs,'sourceUnmodified':True,'completeBlinkOrAppearanceOrContactOrRuntimeAccepted':False});print('R156_REJECTED_SOURCE_ARCHIVE_REOPEN_GAZE_BLINK_RESTORE_LOCAL_WALL_ONLY_DONE',time.time()-tick,flush=True)
