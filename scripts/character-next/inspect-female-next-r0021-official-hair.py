"""Read-only official demo inventory; do not execute embedded scripts or copy code."""
import bpy,json,hashlib
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');REF=R/'Reference/character/blender-hair-styles/hair_nodes-female_hair_styles.blend';E=R/'Evidence/character-female-next/r0021-root-transition'
def main():
    bpy.ops.wm.open_mainfile(filepath=str(REF));objects=[]
    for o in bpy.data.objects:
        row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hiddenRender':o.hide_render,'collections':[c.name for c in o.users_collection],'modifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None,'showRender':m.show_render} for m in o.modifiers]}
        if o.type=='CURVES':row.update({'rawGuideCurves':len(o.data.curves),'rawGuidePoints':len(o.data.points),'surface':o.data.surface.name if o.data.surface else None,'attributes':[x.name for x in o.data.attributes]})
        if o.type=='MESH':
            row.update({'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)})
            if 'growth mesh' in o.name.lower():
                parent=list(range(len(o.data.vertices)))
                def find(i):
                    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
                    return i
                for edge in o.data.edges:
                    i,j=edge.vertices;parent[find(i)]=find(j)
                row['connectedMeshIslands']=len({find(i) for i in range(len(parent))});row['vertexGroups']=[g.name for g in o.vertex_groups]
        objects.append(row)
    # Preserve the original full notes in the unmodified local reference file;
    # inventory only a short credit line and metadata, not the author's prose.
    texts=[{'name':t.name,'length':len(t.as_string()),'credit': 'Daniel Bystedt. CC BY-SA license' if t.name=='Hair demo file info' else None} for t in bpy.data.texts]
    groups=[]
    for g in bpy.data.node_groups:
        counts={}
        for n in g.nodes:counts[n.bl_idname]=counts.get(n.bl_idname,0)+1
        groups.append({'name':g.name,'nodes':len(g.nodes),'nodeTypes':counts,'nestedGroupNames':sorted({n.node_tree.name for n in g.nodes if n.bl_idname=='GeometryNodeGroup' and n.node_tree}),'assetDescription':g.asset_data.description if g.asset_data else None})
    report={'reference':str(REF),'referenceSha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'officialPage':'https://www.blender.org/download/demo-files/','downloadPage':'https://www.blender.org/download/demo/geometry-nodes/hair_nodes-female_hair_styles.blend/','downloadMirror':'https://mirror.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend','author':'Daniel Bystedt','declaredLicense':'CC-BY-SA, exact version not yet resolved from the official listing/embedded text','use':'Read-only learning reference. No reference geometry, textures or node program incorporated into Aevrynd production assets or runtime. Do not describe it as self-authored or CC0.','objects':objects,'nodeGroups':groups,'textBlocks':texts,'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'engine':s.render.engine} for s in bpy.data.scenes]}
    (E/'official-hair-reference-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'objects':len(objects),'curveObjects':[{'name':o['name'],'guides':o['rawGuideCurves'],'surface':o['surface']} for o in objects if o['type']=='CURVES'],'texts':texts},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
