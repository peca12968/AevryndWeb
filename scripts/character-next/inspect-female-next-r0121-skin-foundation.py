from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd'); P=Path('C:/Users/USER/AevryndCharacterEvidence/r0121');P.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend'))
ob=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];out={'uvLayers':[l.name for l in ob.data.uv_layers],'activeUV':ob.data.uv_layers.active.name,'matrix':[list(r) for r in ob.matrix_world],'usedMaterialIndices':sorted(set(p.material_index for p in ob.data.polygons)),'materials':[]}
for mat in ob.data.materials:
 if not mat or not mat.use_nodes:continue
 row={'name':mat.name,'nodes':[],'links':[]}
 for n in mat.node_tree.nodes:
  x={'name':n.name,'type':n.bl_idname}
  if hasattr(n,'uv_map'):x['uv_map']=n.uv_map
  if hasattr(n,'image') and n.image:x['image']={'name':n.image.name,'path':n.image.filepath,'colorspace':n.image.colorspace_settings.name}
  x['inputs']={s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not s.is_linked and s.type in ['VALUE','RGBA','VECTOR','INT','BOOLEAN']}
  row['nodes'].append(x)
 row['links']=[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mat.node_tree.links]
 out['materials'].append(row)
(P/'actual-skin-material-foundation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('R121_SKIN_MATERIAL_FOUNDATION_INSPECTED',out['usedMaterialIndices'],flush=True)
for row in out['materials']:
 if row['name']==ob.data.materials[8].name:print(json.dumps(row,indent=2),flush=True)
