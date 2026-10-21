"""Read exact embedded asset licence metadata and native scene instances."""
from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';SRC=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));assets=[]
for collection in [bpy.data.objects,bpy.data.meshes,bpy.data.hair_curves,bpy.data.node_groups,bpy.data.materials,bpy.data.collections]:
 for x in collection:
  if x.asset_data:assets.append({'name':x.name,'type':x.bl_rna.identifier,'author':x.asset_data.author,'license':x.asset_data.license,'copyright':x.asset_data.copyright,'description':x.asset_data.description})
objects=[{'name':o.name,'parent':o.parent.name if o.parent else None,'instanceCollection':o.instance_collection.name if o.instance_collection else None,'instanceType':o.instance_type,'boundsLocal':[list(v) for v in o.bound_box] if o.type=='MESH' else None,'properties':{k:str(o[k]) for k in o.keys()}} for o in bpy.data.objects]
(E/'original-asset-rights-and-instances.json').write_text(json.dumps({'assetMetadata':assets,'objects':objects},indent=2)+'\n',encoding='utf-8');print('R130_EMBEDDED_ASSET_RIGHTS_READ',len(assets),flush=True)
