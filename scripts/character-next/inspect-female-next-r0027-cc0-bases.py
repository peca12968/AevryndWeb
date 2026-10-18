"""Inventory the official CC0 base library; no existing model is replaced."""
import bpy,json,hashlib
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0027-hair-redesign';REF=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
def main():
    bpy.ops.wm.open_mainfile(filepath=str(REF));rows=[]
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        asset=o.asset_data;rows.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],'uvLayers':list(o.data.uv_layers.keys()),'modifiers':[{'name':m.name,'type':m.type,'levels':getattr(m,'levels',None),'sculptLevels':getattr(m,'sculpt_levels',None)} for m in o.modifiers],'author':getattr(asset,'author',None),'license':getattr(asset,'license',None),'copyright':getattr(asset,'copyright',None),'description':getattr(asset,'description',None),'materials':[m.name if m else None for m in o.data.materials]})
    collections=[{'name':c.name,'author':getattr(c.asset_data,'author',None),'license':getattr(c.asset_data,'license',None),'copyright':getattr(c.asset_data,'copyright',None),'description':getattr(c.asset_data,'description',None),'objects':[o.name for o in c.all_objects]} for c in bpy.data.collections if c.asset_data]
    report={'reference':str(REF),'sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'objects':rows,'assetCollections':collections,'textBlocks':[{'name':t.name,'text':t.as_string()} for t in bpy.data.texts if len(t.as_string())<20000],'use':'Reference-only next-foundation inventory; no character/runtime replacement.'};(E/'cc0-human-base-inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'selectedCollections':[c for c in collections if c['name'] in ('Body - Female - Realistic','Body - Female','Head - Realistic - Sculpt','Head - Realistic - Animation') or ('head' in c['name'].lower() and 'real' in c['name'].lower()) or ('female' in c['name'].lower() and 'real' in c['name'].lower())],'headMeshes':[{'name':r['name'],'vertices':r['vertices'],'modifiers':r['modifiers']} for r in rows if 'head' in r['name'].lower() and 'primitive' not in r['name'].lower()]},indent=2),flush=True)
if __name__=='__main__':main()
