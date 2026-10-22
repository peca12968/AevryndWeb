from pathlib import Path
import bpy,json
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0158-shared-native-skin';b=json.loads((E/'a-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];source=bpy.data.objects[b['actualPoseSource']]
def slots(o):return [{'index':i,'link':x.link,'effective':x.material.name if x.material else None,'nodes':x.material.use_nodes if x.material else None,'dataMaterial':o.data.materials[i].name if o.data.materials[i] else None} for i,x in enumerate(o.material_slots)]
def attrs(d):return [{'name':x.name,'domain':x.domain,'type':x.data_type} for x in d.attributes]
seen=set();used=[]
def tree(t):
 if not t or t.name in seen:return
 seen.add(t.name)
 for n in t.nodes:
  if n.bl_idname in ['ShaderNodeUVMap','ShaderNodeAttribute','ShaderNodeVertexColor']:used.append({'tree':t.name,'node':n.bl_idname,'name':getattr(n,'attribute_name',getattr(n,'uv_map',getattr(n,'layer_name',None)))})
  if n.bl_idname=='ShaderNodeGroup':tree(n.node_tree)
for x in source.material_slots:
 if x.material and x.material.use_nodes:tree(x.material.node_tree)
ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh();out={'sourceSlots':slots(source),'nativeSlots':slots(skin),'sourceEvaluatedAttributes':attrs(d),'newNativeAttributes':attrs(skin.data),'shaderNamedData':used,'sourceUnchanged':True};ev.to_mesh_clear();(E/'actual-effective-material-and-attribute-state.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R158_ACTUAL_MATERIAL_AND_ATTRIBUTE_STATE_DONE',json.dumps(out),flush=True)
