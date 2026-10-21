from pathlib import Path
import bpy,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0113-coherent-head-foundation'
sp=importlib.util.spec_from_file_location('r113back',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
bpy.ops.wm.open_mainfile(filepath=str(b.OUT));b.deliver(0);b.save('b-back-view-controls.json',b.u.v.image('b-coherent-native-character','back'));print('R113_ACTUAL_COMPLETE_BACK_VIEW_DONE',flush=True)
