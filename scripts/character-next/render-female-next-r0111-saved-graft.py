"""Reopen same saved trial with restored required source texture, no model edits."""
from pathlib import Path
import bpy,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r111reopen',Path(__file__).with_name('build-female-next-r0111-mobile-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0111-a-mobile-ocular-graft.blend'))
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and im.filepath:assert Path(bpy.path.abspath(im.filepath)).is_file(),bpy.path.abspath(im.filepath);im.reload()
b.deliver(0);views=[]
for view in ['face','body-face']:views.append(b.u.v.image('a-mobile-ocular-graft-character',view));b.save('a-view-controls.json',views)
for tag,value in [('half',.5),('closed',1.),('restored',0.)]:b.deliver(value);views.append(b.u.v.image('a-mobile-ocular-graft-character-'+tag,'face'));b.save('a-view-controls.json',views)
print('R111_SAME_SAVED_TRIAL_REQUIRED_TEXTURE_REOPEN_PREVIEW_DONE',time.time()-tick,flush=True)
