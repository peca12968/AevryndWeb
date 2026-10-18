"""Separate screen-space trace error from authored cornea response."""
import bpy, importlib.util, json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0009-optics'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'))
stage=importlib.util.module_from_spec(spec); spec.loader.exec_module(stage); stage.E=E
rows=[]
for label in ('trace-scale','reflection-isolation'):
    bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0008-a-tight-study.blend'))
    s=bpy.context.scene; stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral')
    opt=s.eevee.ray_tracing_options
    if label=='trace-scale':
        opt.screen_trace_thickness=.0002; opt.screen_trace_quality=1.; opt.resolution_scale='1'
    else:
        for n in bpy.data.materials['AFN6_Cornea'].node_tree.nodes:
            if n.bl_idname=='ShaderNodeBsdfPrincipled': n.inputs['Specular IOR Level'].default_value=0.
    path=stage.render(label,'eyes',stage.helper_centres(),'neutral')
    rows.append({'label':label,'image':path,'traceThicknessM':opt.screen_trace_thickness,'scope':'renderer diagnostic only' if label=='trace-scale' else 'nonphysical isolation only'})
(E/'trace-isolation.json').write_text(json.dumps(rows,indent=2)+'\n')
print('AFN_R0009_TRACE_DONE')
