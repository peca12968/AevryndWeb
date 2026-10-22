"""Repair imported head tangent-space chart binding; no texture/colour edits.
Only author a candidate when actual normal-map UV and explicit texture UV disagree.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0147-outer-lid-surface';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0146-source/aevrynd-female-next-r0146-a-connected-palpebral-lining.blend';OUT=S/'r0147-source/aevrynd-female-next-r0147-a-head-tangent-chart.blend'
sp=importlib.util.spec_from_file_location('r147surfacebase',Path(__file__).with_name('build-female-next-r0146-connected-lining.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
def save(n,x):h.E=E;h.save(n,x)
def main():
 tick=time.time();assert not OUT.exists();digest=a.a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.c.h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected=a.a.protected();before={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};material=bpy.data.materials['AFN126_NATIVE_ARTIST_HEAD_MATERIAL'];nt=material.node_tree;nodes=nt.nodes;uvnodes=[n for n in nodes if n.type=='UVMAP'];normal=[n for n in nodes if n.type=='NORMAL_MAP'];assert len(uvnodes)==len(normal)==1;uvnode=uvnodes[0];nm=normal[0];target=uvnode.uv_map;assert target in skin.data.uv_layers
 active=skin.data.uv_layers.active.name;render=next(u.name for u in skin.data.uv_layers if u.active_render);used=nm.uv_map or render;specified=nm.uv_map;N=len(skin.data.loops);allUV={u.name:h.values(u.data,'uv',N,2) for u in skin.data.uv_layers};beforeUV={n:a.a.hasharray(v) for n,v in allUV.items()};uvReport={'textureUVExplicitNode':uvnode.name,'textureUVChart':target,'normalMapNode':nm.name,'normalMapSpace':nm.space,'originalNormalMapSpecifiedUV':specified,'originalEffectiveTangentUV':used,'activeUV':active,'renderUV':render,'uvCharts':{n:{'sha256':beforeUV[n],'nonzeroLoopCount':int(np.count_nonzero(np.any(v!=0,axis=1)))} for n,v in allUV.items()},'mismatchObserved':used!=target,'sourceSha256':digest}
 save('actual-head-tangent-chart-before.json',uvReport);assert nm.space=='TANGENT' and used!=target,'No changed-premise chart mismatch: do not author a cosmetic variant'
 # Establish texture UV path from the actual normal colour texture.
 assert nm.inputs['Color'].is_linked;tex=nm.inputs['Color'].links[0].from_node;assert tex.type=='TEX_IMAGE' and tex.inputs['Vector'].is_linked and tex.inputs['Vector'].links[0].from_node==uvnode
 save('direct-head-tangent-chart-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T02:52:50+00:00','action':'Bind actual artist-head tangent-space Normal Map to the same existing explicit head UV chart as its unchanged source normal texture; retain all mesh/UV/shape/control/image/colour data.'})
 nm.uv_map=target;skin.data.update();bpy.context.view_layer.update();assert nm.uv_map==target and before=={n:a.rawsig(bpy.data.objects[n]) for n in before};assert beforeUV=={u.name:a.a.hasharray(h.values(u.data,'uv',N,2)) for u in skin.data.uv_layers};assert a.a.protected()==protected
 rig['AFN147_scope']='Unaccepted original head tangent-chart binding correction only. All original textures/geometry/native controls unchanged from146; not new anatomy/contact/runtime acceptance. R139 remains working until scoped decision.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 save('a-build-summary.json',{'source':str(SRC),'comparisonBaseline':str(S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend'),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':h.PROPS,'originalGazeAction':'AFN138_NATIVE_CURRENT_GAZE_DEMO','newBlinkDemoAction':'AFN144_ACTUAL_CURRENT_SKIN_BLINK_DEMO','oneCompleteCandidate':True,'completeAppearanceOperationContactRuntimeUnaccepted':True,'changedPremiseActualNormalAndTextureUVDisagreement':uvReport,'onlyOneNormalMapUVBindingChanged':True,'geometryUVImagesColourExposureUnchanged':True,'secondsBeforePreview':time.time()-tick})
 views=[]
 for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-head-tangent-chart',v));save('a-view-controls.json',views)
 motion=[]
 for f in [5,9,13,17]:
  scene.frame_set(f);bpy.context.view_layer.update()
  for v in ['face','body-face']:
   row=a.b.u.v.image('blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in h.PROPS.items()};motion.append(row);save('actual-blink-motion-controls.json',motion)
 scene.frame_set(9);bpy.context.view_layer.update();save('actual-closed-profile-control.json',a.b.u.v.image('closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected and a.a.sha(SRC)==digest;print('R147_ACTUAL_HEAD_TANGENT_CHART_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
