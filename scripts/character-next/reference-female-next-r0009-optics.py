"""Cycles diagnostic with identical geometry and stage; not an adoption candidate."""
import bpy, json, importlib.util
from pathlib import Path
R = Path(r'D:\Download\Aevrynd')
E = R/'Evidence/character-female-next/r0009-optics'
spec = importlib.util.spec_from_file_location('eye_tools', Path(__file__).with_name('build-female-next-r0006-native-eyes.py'))
stage = importlib.util.module_from_spec(spec); spec.loader.exec_module(stage); stage.E = E
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0008-a-tight-study.blend'))
s = bpy.context.scene; rig = bpy.data.objects['AFN_R0005_Rig']; stage.set_pose(rig, 'neutral')
m = bpy.data.materials['AFN6_Cornea']
meta = {'outputInputs': {i.name: str(getattr(i, 'default_value', None)) for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' for i in n.inputs},
        'materialProperties': {p.identifier: str(getattr(m, p.identifier)) for p in m.bl_rna.properties if any(w in p.identifier for w in ('thickness', 'refraction', 'surface_render'))},
        'raytraceOptions': {p.identifier: str(getattr(s.eevee.ray_tracing_options, p.identifier)) for p in s.eevee.ray_tracing_options.bl_rna.properties}}
(E/'renderer-settings.json').write_text(json.dumps(meta, indent=2)+'\n')
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 48; s.cycles.use_denoising = True; s.render.threads_mode = 'FIXED'; s.render.threads = 8
stage.render('cycles-reference', 'eyes', stage.helper_centres(), 'neutral')
print('AFN_R0009_CYCLES_REFERENCE_DONE')
