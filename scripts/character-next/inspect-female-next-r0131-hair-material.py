"""Read the actual current material graph and original hair-card UV roles."""
from pathlib import Path
import bpy,numpy as np,json,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0131-native-hair-material';E.mkdir(parents=True,exist_ok=True);SRC=R/'engine/assets/characters/female-next/source/r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';bpy.ops.wm.open_mainfile(filepath=str(SRC));o=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];rows=[]
for mat in o.data.materials:
 nodes=[]
 for n in mat.node_tree.nodes:
  inputs={}
  for p in n.inputs:
   if hasattr(p,'default_value'):
    v=p.default_value;inputs[p.name]={'default':list(v) if hasattr(v,'__len__') and not isinstance(v,str) else v,'linked':p.is_linked}
  nodes.append({'name':n.name,'type':n.bl_idname,'inputs':inputs,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'uvMap':n.uv_map if n.type=='NORMAL_MAP' else None})
 rows.append({'name':mat.name,'surfaceRenderMethod':mat.surface_render_method,'nodes':nodes,'links':[(x.from_node.name,x.from_socket.name,x.to_node.name,x.to_socket.name) for x in mat.node_tree.links]})
data={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'object':o.name,'uvLayers':[u.name for u in o.data.uv_layers],'rawVertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':rows,'sourceNotSaved':True};(E/'actual-hair-material-inspection.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print('R131_ACTUAL_CURRENT_HAIR_MATERIAL_READ',flush=True)
