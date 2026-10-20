"""Load source material DATA only; inspect prerequisites without image pixels."""
from pathlib import Path
import bpy,json,hashlib
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0073-complete-skin';E.mkdir(exist_ok=True);S=R/'engine/assets/characters/female-next/source';D=R/'Reference/character/charmorph-vitruvian-cc0'
def main():
    bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0069-a-complete-controls-study.blend'));body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];row={'currentBodyUV':[u.name for u in body.data.uv_layers],'currentBodyAttributes':[(a.name,a.data_type,a.domain) for a in body.data.attributes],'sourceMaterial':None,'groups':[],'images':[]};oldimages={i.as_pointer() for i in bpy.data.images}
    assert hashlib.sha256((D/'char.blend').read_bytes()).hexdigest()=='7e9581c30b48f1409dfeec4a5ec0736014318fc8825ca6d4728f2b543bb02126'
    with bpy.data.libraries.load(str(D/'char.blend'),link=False) as (src,dst):dst.materials=['UDIM.Skin']
    mat=dst.materials[0];seen=set()
    def walk(t):
        if t.as_pointer() in seen:return
        seen.add(t.as_pointer());nodes=[]
        for n in t.nodes:
            a={'name':n.name,'type':n.bl_idname}
            if n.type=='GROUP':a['group']=n.node_tree.name;walk(n.node_tree)
            if n.type=='TEX_IMAGE':a.update(image=n.image.name if n.image else None,vectorLinked=n.inputs['Vector'].is_linked)
            if n.type=='UVMAP':a['uv']=n.uv_map
            if n.type=='ATTRIBUTE':a['attribute']=n.attribute_name
            if n.type=='VERTEX_COLOR':a['layer']=n.layer_name
            nodes.append(a)
        drivers=[]
        if t.animation_data:
            for f in t.animation_data.drivers:drivers.append({'path':f.data_path,'expression':f.driver.expression})
        row['groups'].append({'name':t.name,'nodes':nodes,'drivers':drivers})
    walk(mat.node_tree);row['sourceMaterial']={'name':mat.name,'displacementMethod':mat.displacement_method,'nodes':[(n.name,n.bl_idname,n.node_tree.name if n.type=='GROUP' else None) for n in mat.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links]}
    for im in bpy.data.images:
        if im.as_pointer() not in oldimages:row['images'].append({'name':im.name,'path':im.filepath,'source':im.source,'packed':bool(im.packed_file),'tiles':[x.number for x in im.tiles] if im.source=='TILED' else [],'colorspace':im.colorspace_settings.name})
    (E/'source-material-prerequisites.json').write_text(json.dumps(row,indent=2),encoding='utf8');print('R73_SOURCE_MATERIAL',json.dumps(row['sourceMaterial']),flush=True);print('R73_ATTRIBUTES',row['currentBodyAttributes'],flush=True)
    for g in row['groups']:
        selected=[x for x in g['nodes'] if any(k in x for k in ('image','attribute','layer','uv'))]
        if selected or g['drivers']:print('R73_DEPENDENCY',g['name'],selected,'DRIVERS',g['drivers'],flush=True)
    print('R73_IMPORTED_IMAGES',row['images'],flush=True)
if __name__=='__main__':main()
