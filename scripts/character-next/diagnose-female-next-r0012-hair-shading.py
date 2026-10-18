"""Reference render for sparse hair: keep scene and geometry, isolate renderer/specular."""
import bpy,importlib.util,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'));stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage);stage.E=E
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0012-a-layered-hair-study.blend'));s=bpy.context.scene;stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');fits=stage.helper_centres();s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=8
cycles=stage.render('a-cycles-reference','face',fits,'neutral')
s.render.engine='BLENDER_EEVEE'
for m in bpy.data.materials:
    if m.name.startswith('AFN12_ChestnutKeratin'):
        bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Specular IOR Level'].default_value=0
isolation=stage.render('a-no-specular-isolation','face',fits,'neutral')
(E/'shading-isolation.json').write_text(json.dumps({'cycles':cycles,'noSpecular':isolation,'scope':'Diagnostics only; no model saved or acceptance claimed.'},indent=2)+'\n');print('AFN_R0012_SHADING_ISOLATION_DONE')
