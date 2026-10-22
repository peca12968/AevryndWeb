"""Reopen both complete archive sources; corroborate existing 19 failure pairs.
No new candidate, sweep, source write or complete-contact acceptance.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0155-native-blink';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
def module(n,f):
 s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('r155mirror','build-female-next-r0155-margin-blink.py');a=h.a;socket=module('r155witness','build-female-next-r0138-native-sockets.py')
def read(n):return json.loads((E/n).read_text('utf-8-sig'))
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item() if isinstance(x,np.generic) else str(x))+'\n').encode())
tick=time.time();results=[];reference=None
for label in ['a','b']:
 b=read(label+'-build-summary.json');p=M/'r0155-source'/Path(b['output']).name;assert a.a.sha(p)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[b['actualSkin']];names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};neutral={n:a.geometry(bpy.data.objects[n])[0].copy() for n in names}
 if reference is None:reference=raw
 else:assert reference==raw
 libs=[];textures=[]
 for lib in bpy.data.libraries:
  q=Path(bpy.path.abspath(lib.filepath)).resolve();assert q.is_relative_to(M.resolve()) and q.is_file();libs.append({'file':str(q),'sha256':a.a.sha(q)})
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   q=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert q.is_relative_to(M.resolve()) and q.is_file();textures.append({'file':str(q),'sha256':a.a.sha(q)})
 assert len(textures)==16 and len(libs)==1
 action=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=bpy.data.actions[b['originalGazeAction']]
 for prop in ['blink_L','blink_R']:rig[prop]=0.
 rig.update_tag();s.frame_set(9);bpy.context.view_layer.update();gaze=float(np.linalg.norm(a.geometry(bpy.data.objects[a.MOVING[0]])[0]-neutral[a.MOVING[0]],axis=1).max());assert gaze>.001
 rig.animation_data.action=action;rig.animation_data.action_slot=slot;motion=[]
 for frame in [1,9,11,24]:
  s.frame_set(frame);bpy.context.view_layer.update();d={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-neutral[n],axis=1).max()) for n in names};motion.append({'frame':frame,'blink':[float(rig[x]) for x in ['blink_L','blink_R']],'actualLayerMaximumDisplacementM':d})
  if frame==11:
   assert d[skin.name]>.001
   if label=='b':
    V,T=a.geometry(skin);W,F=a.geometry(bpy.data.objects[a.MOVING[1]]);pairs=read('b-actual-ocular-triangle-contact.json')['cases'][1]['firstProperFacePairs'];witnesses=[]
    table=bpy.data.objects['AFN155_CURRENT_SKIN_BLINK_FIELD'].data;skin.data.calc_loop_triangles()
    for si,ei in pairs:
     hits=socket.witness(V[T[si]],W[F[ei]]);assert len(hits)>=2
     ids=T[si];normal=np.cross(V[ids[1]]-V[ids[0]],V[ids[2]]-V[ids[0]]);normal/=np.linalg.norm(normal)
     witnesses.append({'evaluatedSkinTriangle':si,'eyeReflectTriangle':ei,'actualSkinVertexIndices':ids,'skinWorldTriangle':V[ids],'reflectWorldTriangle':W[F[ei]],'skinWorldUnitNormal':normal,'nativeBlinkAnglesRad':[table.attributes['AFN155_ANGLE'].data[int(i)].value for i in ids],'nativeBlinkRadialM':[table.attributes['AFN155_RADIAL'].data[int(i)].value for i in ids],'independentFiniteSegmentTriangleWitnesses':hits})
    save('b-independent-crossing-location-witness.json',{'source':str(p),'frame':11,'all19RecordedCrossingsCorroborated':True,'pairs':witnesses,'noSignedDepthFiniteThicknessSelfContinuousOrAnatomicalWallLineageClaim':True,'nextConstructionQuestion':'Determine original face/socket-wall lineage and deformation-domain ownership of these exact vertices before rebuilding blocking anatomy. Do not hide/delete implicated faces or globally push Skin.'})
 assert max(motion[-1]['actualLayerMaximumDisplacementM'].values())==0
 s.frame_set(1);bpy.context.view_layer.update();assert all(np.array_equal(a.geometry(bpy.data.objects[n])[0],neutral[n]) for n in names);assert a.a.sha(p)==b['sha256'];results.append({'label':label,'source':str(p),'sha256':b['sha256'],'relativeLibrariesWithinArchive':libs,'relativeTexturesWithinArchive':textures,'rawSevenMeshesUVIdenticalBetweenStates':True,'gazeFrame9MovementM':gaze,'blinkPoseReadback':motion,'allSevenNeutralRestorationM':0,'sourceUnmodified':True,'completeBlinkAccepted':False});save('independent-mirror-source-readback.json',{'results':results,'related19CrossingsNotWaived':True,'runtimeNotTested':True})
print('R155_AB_ARCHIVE_REOPEN_16_TEXTURES_GAZE_BLINK_RESTORE_19_INDEPENDENT_CROSSINGS_DONE',time.time()-tick,flush=True)
