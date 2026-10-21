"""One unsaved causal Base Color test on the actual retained complete woman."""
from pathlib import Path
import bpy,json,importlib.util,time
R=Path('D:/Download/Aevrynd'); E=R/'Evidence/character-female-next/r0105-native-head-skin-chart'
sp=importlib.util.spec_from_file_location('r105shared',Path(__file__).with_name('build-female-next-r0104-native-head-union.py')); u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
tick=time.time(); P=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0104-b2-native-head-material-repair.blend';bpy.ops.wm.open_mainfile(filepath=str(P));skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];original=skin.data.materials[4]; mat=original.copy();mat.name='AFN105_DIAGNOSTIC_ONLY_BASECOLOR_EMISSION';skin.data.materials[4]=mat
graph=[]
for node in original.node_tree.nodes:
 row={'name':node.name,'type':node.bl_idname,'inputs':{}}
 if node.type=='TEX_IMAGE':row.update(image=node.image.name if node.image else None,filepath=node.image.filepath if node.image else None)
 if node.type=='UVMAP':row['uvMap']=node.uv_map
 for inp in node.inputs:
  if inp.is_linked:row['inputs'][inp.name]=[{'node':l.from_node.name,'socket':l.from_socket.name} for l in inp.links]
  elif hasattr(inp,'default_value'):
   val=inp.default_value
   try:val=list(val)
   except TypeError:pass
   row['inputs'][inp.name]=val
 graph.append(row)
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);em=mat.node_tree.nodes.new('ShaderNodeEmission')
if bs.inputs['Base Color'].is_linked:mat.node_tree.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
mat.node_tree.links.new(em.outputs[0],out.inputs['Surface']);u.v.E=E;view=u.v.image('diagnostic-basecolor-emission','face')
(E/'basecolor-causal-diagnostic.json').write_text(json.dumps({'source':str(P),'sourceNotSaved':True,'graph':graph,'diagnosticView':view,'scope':'Actual original Base Color routed unchanged into emission; all other skin shading responses bypassed only for diagnosis. Not appearance adoption.','seconds':time.time()-tick},indent=2)+'\n',encoding='utf8',newline='\n');print('R105_BASECOLOR_DIAGNOSTIC_DONE',time.time()-tick,flush=True)
