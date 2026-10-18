"""Read saved hair node graphs/lights/exposure for the paired geometry comparisons."""
import bpy,json,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
S,E=flow.S,flow.E
def graph(tree):
    def value(i):
        v=getattr(i,'default_value',None);return list(v) if v is not None and hasattr(v,'__iter__') and not isinstance(v,str) else v
    return {'nodes':[(n.name,n.bl_idname,getattr(n,'model',None),getattr(n,'parametrization',None),[(i.name,value(i)) for i in n.inputs]) for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]}
def state(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
    return {'hairMaterials':{m.name:graph(m.node_tree) for m in bpy.data.materials if m.name.startswith('AFN13_ChestnutKeratin')},'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy,o.data.size,list(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT'],'world':graph(s.world.node_tree),'view':(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma)}
base=S/'aevrynd-female-next-r0013-b-safe-io-native-envelope-hair-study.blend';pbr=state(base);rows=[]
for name in ('aevrynd-female-next-r0014-a-scalp-flow-study.blend','aevrynd-female-next-r0014-c-clump-volume-study.blend','aevrynd-female-next-r0014-c-review.blend'):
    p=S/name;now=state(p);checks={k:pbr[k]==now[k] for k in pbr};assert all(checks.values()),checks;rows.append({'asset':name,'sha256':flow.route.sha(p),'matchedBaseline':base.name,'checks':checks})
base=S/'aevrynd-female-next-r0013-c-huang-reference-front-view.blend';physical=state(base)
for name in ('aevrynd-female-next-r0014-b-huang-scalp-flow-reference.blend','aevrynd-female-next-r0014-c-huang-clump-reference.blend'):
    p=S/name;now=state(p);checks={k:physical[k]==now[k] for k in physical};assert all(checks.values()),checks;rows.append({'asset':name,'sha256':flow.route.sha(p),'matchedBaseline':base.name,'checks':checks})
(E/'render-controls-verification.json').write_text(json.dumps({'status':'PASS_SAVED_MATERIAL_LIGHT_WORLD_EXPOSURE_EQUALITY','assets':rows,'cameraScope':'Paired images use the exact same shared r0006 stage render helper, which resets camera/lens/resolution for each named view; saved default cameras are not used as the paired-image proof.','limits':'Renderer changes between Eevee and Cycles are separate comparisons and do not prove anatomy improvements.'},indent=2)+'\n');print('AFN14_RENDER_CONTROLS_PASS',flush=True)
