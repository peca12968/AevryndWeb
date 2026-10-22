"""Inspect newly acquired source as data; do not install an add-on or transplant it."""
from pathlib import Path
import bpy,json,datetime,numpy as np
P=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference')
E=Path('D:/Download/Aevrynd/Evidence/character-female-next/support-r0152-render-representation')
bpy.ops.wm.open_mainfile(filepath=str(P/'hair.blend'))
rows=[]
for o in bpy.data.objects:
 d=o.data
 row={'name':o.name,'type':o.type,'location':list(o.location),'dimensions':list(o.dimensions),'hidden':o.hide_render,'modifiers':[{'type':m.type,'name':m.name,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in o.modifiers],'properties':{k:str(o[k])[:500] for k in o.keys()}}
 if o.type=='CURVES':row.update(curves=len(d.curves),points=len(d.points),surface=d.surface.name if d.surface else None,uv=d.surface_uv_map)
 if o.type=='CURVE':row.update(splines=len(d.splines),points=sum(len(s.points)+len(s.bezier_points) for s in d.splines))
 if o.type=='MESH':row.update(vertices=len(d.vertices),polygons=len(d.polygons))
 rows.append(row)
data={'inspectedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(P/'hair.blend'),'objects':rows,'textBlocks':[{'name':t.name,'body':t.as_string()[:12000]} for t in bpy.data.texts],'nodeGroups':[{'name':n.name,'nodes':len(n.nodes),'interface':[(i.name,i.in_out,i.socket_type) for i in n.interface.items_tree if i.item_type=='SOCKET']} for n in bpy.data.node_groups],'adopted':False,'noInstallOrWomanEdit':True}
(E/'new-cc0-mpfb-hair-source-inspection.json').write_bytes((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode());print('NEW_CC0_HAIR_SOURCE_NATIVE_INSPECTION_DONE',len(rows),len(bpy.data.node_groups),flush=True)
