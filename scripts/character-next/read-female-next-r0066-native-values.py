"""Read exact original node operations and source-authored skin transport values."""
from pathlib import Path
import bpy,json
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0066-skin-response'
bpy.ops.wm.open_mainfile(filepath=str(R/'Reference/character/charmorph-vitruvian-cc0/char.blend'))
rows={}
for name in ('VitruvianSkin','RoughnessUnreal'):
    t=bpy.data.node_groups[name];a=[]
    for n in t.nodes:
        row={'name':n.name,'type':n.bl_idname}
        for key in ('operation','blend_type','data_type','space','subsurface_method','distribution'):
            if hasattr(n,key):row[key]=getattr(n,key)
        if n.bl_idname=='ShaderNodeGroup':row['group']=n.node_tree.name
        if n.bl_idname=='ShaderNodeValue':row['output']=n.outputs[0].default_value
        a.append(row)
    rows[name]=a
skin=bpy.data.materials['UDIM.Skin'];rows['sourceDisplacementMethod']=skin.displacement_method
settings=skin.node_tree.nodes['charmorph_settings'].node_tree
rows['sourceSettings']={n.name:n.outputs[0].default_value for n in settings.nodes if n.bl_idname=='ShaderNodeValue'}
rows['meshUnits']={'sceneScale':bpy.context.scene.unit_settings.scale_length,'objects':{o.name:{'scale':list(o.scale),'dimensions':list(o.dimensions)} for o in bpy.data.objects if o.type=='MESH'}}
(E/'native-skin-values.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8');print('R66_NATIVE_VALUES',rows['sourceSettings'],flush=True)
