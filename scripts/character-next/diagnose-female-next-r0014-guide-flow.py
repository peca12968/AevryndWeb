"""Actual 3D scalp/guide visualization, enlarged only for diagnostic visibility."""
import bpy,json,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
bpy.ops.wm.open_mainfile(filepath=str(flow.S/'aevrynd-female-next-r0014-a-scalp-guides.blend'))
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.8;return m
scalp=bpy.data.objects['AFN14_SCALP_EMITTER'];scalp.hide_render=False;scalp.data.materials.append(material('AFN14_DIAGNOSTIC_CYAN',(.025,.28,.32)))
guides=bpy.data.objects['AFN14_GUIDES'];guides.hide_render=False;guides.data.bevel_depth=.00018;guides.data.materials.append(material('AFN14_DIAGNOSTIC_AMBER',(.25,.07,.01)))
fits=flow.solid.stage.eyes.helper_centres();paths=[flow.solid.stage.eyes.render('a-scalp-guide-diagnostic',v,fits,'neutral') for v in ('face','profile')]
(flow.E/'guide-visualization.json').write_text(json.dumps({'renders':paths,'scope':'Diagnostic visualization only: scalp emitter shown cyan and guides enlarged from 60 to 180 um radius. Authoritative guide source is not modified or resaved; these colors and thickness are not final hair.'},indent=2)+'\n');print('AFN14_GUIDE_VIZ_DONE')
