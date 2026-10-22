from pathlib import Path
import bpy,numpy as np,json,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0155-native-blink'
sp=importlib.util.spec_from_file_location('r155rendereval',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;b=json.loads((E/'b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[b['actualSkin']];s.frame_set(1);bpy.context.view_layer.update();P=a.geometry(skin)[0];s.frame_set(11);bpy.context.view_layer.update();Q=a.geometry(skin)[0];params=np.load(E/'current-margin-blink-authoring.npz');construction=json.loads((E.parent/'r0139-native-lid-follow/native-lid-follow-construction.json').read_text());margin=[]
for side in ['L','R']:
 for kind in ['UPPER','LOWER']:
  ids=np.array(construction['actualSourceNativeDomains'][side+'_'+kind]['actualSkinSeedIds']);margin.append({'side':side,'kind':kind,'ids':ids.tolist(),'neutral':P[ids].tolist(),'closedViewport':Q[ids].tolist(),'maximumMovementM':float(np.linalg.norm(Q[ids]-P[ids],axis=1).max()),'authoredAngles':params['angle'][ids].tolist()})
records=[]
def capture(scene,dg):
 if dg.mode!='RENDER' or records:return
 ob=skin.evaluated_get(dg);mesh=ob.to_mesh();v=np.array([ob.matrix_world@x.co for x in mesh.vertices]);ob.to_mesh_clear();records.append({'mode':dg.mode,'frame':scene.frame_current,'blink':[float(rig['blink_L']),float(rig['blink_R'])],'actualSkinVertices':len(v),'actualMaximumSkinMovementFromNeutralM':float(np.linalg.norm(v-P,axis=1).max()),'actualMaximumRenderVersusViewportM':float(np.linalg.norm(v-Q,axis=1).max()),'skinObjectLibrary':str(skin.library),'skinInScene':skin.name in s.objects,'modifiers':[{'name':m.name,'type':m.type,'render':m.show_render,'viewport':m.show_viewport} for m in skin.modifiers]})
a.b.u.v.m.rig.shade.settings();a.b.u.v.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/'b-render-evaluation-probe-closed.png');s.frame_set(11);bpy.context.view_layer.update();bpy.app.handlers.depsgraph_update_post.append(capture)
try:bpy.ops.render.render(write_still=True)
finally:bpy.app.handlers.depsgraph_update_post.remove(capture)
h.save('actual-render-versus-viewport-evaluation.json',{'actualViewportClosedSkinMovementM':float(np.linalg.norm(Q-P,axis=1).max()),'marginEvidence':margin,'renderGraphRecords':records,'sourceFileNotChanged':True,'probeIsDiagnosticNotAnotherSavedCandidate':True});print('R155_ACTUAL_RENDER_VERSUS_VIEWPORT_EVALUATION_DONE',records,flush=True)
