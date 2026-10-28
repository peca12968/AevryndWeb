
from pathlib import Path
import bpy,json,hashlib,datetime
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0208-complete-native-style-construction';ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');assert hashlib.file_digest(ART.open('rb'),'sha256').hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';bpy.ops.wm.open_mainfile(filepath=str(ART));hair=bpy.data.objects['basic_short_hair'];rows=[]
def val(x):
 if hasattr(x,'name'):return {'name':x.name,'type':type(x).__name__}
 try:return list(x)
 except:return x
for md in hair.modifiers:
 row={'name':md.name,'type':md.type,'viewport':md.show_viewport,'render':md.show_render,'props':({k:val(md[k]) for k in md.keys()} if md.type=='NODES' else {})}
 if md.type=='NODES':
  ng=md.node_group;row.update(group=ng.name,sockets=[{'name':x.name,'identifier':x.identifier,'socketType':x.socket_type,'inout':x.in_out,'default':val(x.default_value) if hasattr(x,'default_value') else None} for x in ng.interface.items_tree if x.item_type=='SOCKET'],objectRefs=[{'node':n.name,'input':i.name,'value':val(i.default_value)} for n in ng.nodes for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,bpy.types.ID)],nodes=[{'name':n.name,'type':n.bl_idname,'group':n.node_tree.name if n.bl_idname=='GeometryNodeGroup' else None} for n in ng.nodes])
 rows.append(row)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(ART),'sourceUnmodified':True,'sourceOnlyNotCurrentWomanResult':True,'hair':hair.name,'surface':hair.data.surface.name,'modifiers':rows};(E/'complete-source-style-stage-inspection.json').write_bytes((json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(q),flush=True)
