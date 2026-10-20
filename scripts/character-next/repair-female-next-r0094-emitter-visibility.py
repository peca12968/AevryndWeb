"""Same C construction: repair inherited source visibility, preserve failed save."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0094-authored-growth-routing';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0094-c-native-emitter-guides.blend';OUT=S/'aevrynd-female-next-r0094-c-native-emitter-visible.blend'
sp=importlib.util.spec_from_file_location('r94vis',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(o):
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=ev.particle_systems['Eve'];P=np.array([ps.co_hair(ev,particle_no=i,step=j)[:] for i in [0,100,1077,1177] for j in [0,1,3]])
 return {'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get(),'showEmitterRender':o.show_instancer_for_render,'showEmitterViewport':o.show_instancer_for_viewport,'renderType':ps.settings.render_type,'samplePoints':P.tolist(),'modifiers':[{'name':md.name,'type':md.type,'viewport':md.show_viewport,'render':md.show_render} for md in o.modifiers]}
tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);o=bpy.data.objects['AFN94_NATIVE_EVE_EMITTER_AND_EDITABLE_GUIDES'];before=probe(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False);bpy.context.view_layer.update();after=probe(o);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);rows=[]
for view in ['face','back','body-face']:rows.append(v.image('c-native-visible',view));(E/'c-visible-view-controls.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
(E/'c-visibility-repair.json').write_text(json.dumps({'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'before':before,'after':after,'sameConstructionNotNewMethodOrAppearanceGain':True,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8');print('R94_C_VISIBILITY',before['hideRender'],after['hideRender'],time.time()-tick,flush=True)
