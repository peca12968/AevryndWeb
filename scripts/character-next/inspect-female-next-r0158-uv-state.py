from pathlib import Path
import bpy,json,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0158-shared-native-skin';b=json.loads((E/'a-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];source=bpy.data.objects[b['actualPoseSource']]
def uvstate(d):return {'activeIndex':d.uv_layers.active_index,'activeName':d.uv_layers.active.name if d.uv_layers.active else None,'layers':[{'name':u.name,'activeRender':u.active_render,'activeClone':u.active_clone,'active':u.active} for u in d.uv_layers]}
ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh();nodes=[]
for mat in skin.data.materials:
 if mat and mat.use_nodes:
  nodes.extend({'material':mat.name,'node':n.bl_idname,'uvMap':getattr(n,'uv_map',None),'attribute':getattr(n,'attribute_name',None)} for n in mat.node_tree.nodes if n.bl_idname in ['ShaderNodeUVMap','ShaderNodeTexCoord','ShaderNodeAttribute'])
out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceRawUV':uvstate(source.data),'sourceEvaluatedUV':uvstate(d),'newNativeUV':uvstate(skin.data),'actualMaterialUVNodes':nodes,'sourceUnmodified':True};ev.to_mesh_clear();(E/'actual-uv-role-readback.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R158_ACTUAL_UV_ROLE_READBACK_DONE',json.dumps(out),flush=True)
