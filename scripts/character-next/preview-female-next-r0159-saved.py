"""Observe original saved candidate after save-cost assert; no new build/save."""
from pathlib import Path
import bpy,importlib.util,json,time
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0159-native-lid-wall';sp=importlib.util.spec_from_file_location('r159preview',C/'scripts/character-next/build-female-next-r0159-native-lid-wall.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;tick=time.time();b=json.loads((E/'a-build-summary.json').read_text());assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];a.b.u.v.E=E;views=[]
for frame,view,tag in [(11,'face','a-wall-closed'),(11,'body-face','a-wall-closed'),(1,'face','a-wall-neutral'),(9,'face','a-wall-half')]:
 s.frame_set(frame);bpy.context.view_layer.update();_=a.geometry(bpy.data.objects[b['actualSkin']])
 for name in a.FIXED[2:4]:_=a.geometry(bpy.data.objects[name])
 control=a.b.u.v.image(tag,view);control.update(frame=frame,blink=[float(rig[k]) for k in ['blink_L','blink_R']]);views.append(control);h.save('actual-wall-preview-controls.json',views)
s.frame_set(1);bpy.context.view_layer.update();assert a.a.sha(Path(b['output']))==b['sha256'];print('R159_ORIGINAL_SAVED_CANDIDATE_COMPLETE_HEAD_BODY_NEUTRAL_HALF_PREVIEW_DONE',time.time()-tick,flush=True)
