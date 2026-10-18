"""Render geometry-only alpha coverage; do not mistake bright scalp for hair shading."""
import bpy,importlib.util,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'));stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage);stage.E=E
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0012-b-volume-hair-study.blend'))
for o in bpy.data.objects:
    if o.type=='MESH':o.hide_render=True
s=bpy.context.scene;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA'
stage.render('b-hair-only-alpha','face',stage.helper_centres(),'neutral')
print('AFN_R0012_COVERAGE_DONE')
