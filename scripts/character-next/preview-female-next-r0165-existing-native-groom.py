"""Observe existing saved original B after resource assertion; never reauthor."""
from pathlib import Path
import bpy,json,importlib.util,time
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0165-native-hair-construction';sp=importlib.util.spec_from_file_location('r165preview',C/'scripts/character-next/build-female-next-r0165-intrinsic-native-groom.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;tick=time.time();b=json.loads((E/'b-build-summary.json').read_text());assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['engineAlias']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();a.b.u.v.E=E;views=[]
for view in ['face','body-face','profile','back','oblique']:
 ctl=a.b.u.v.image('b-intrinsic-native-groom',view);ctl.update(frame=1,actualHair=b['actualHair'],nativeStrands=b['nativeStrands'],reopenedExistingSavedBNotReauthored=True);views.append(ctl);m.save('actual-intrinsic-native-groom-preview-controls.json',views)
assert a.a.sha(Path(b['output']))==b['sha256'];print('R165_EXISTING_B_COMPLETE_NATIVE_GROOM_HEAD_BODY_PROFILE_BACK_OBLIQUE_PREVIEW_DONE',time.time()-tick,flush=True)
