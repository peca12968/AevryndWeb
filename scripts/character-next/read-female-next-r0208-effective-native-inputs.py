
from pathlib import Path
import bpy,json
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0208-complete-native-style-construction';bpy.ops.wm.open_mainfile(filepath='C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');rows=[]
def val(x):
 if isinstance(x,(str,bool,int,float)) or x is None:return x
 try:return list(x)
 except:return str(x)
for md in bpy.data.objects['basic_short_hair'].modifiers:
 i=md.properties.inputs;values={}
 for sock in md.node_group.interface.items_tree:
  if sock.item_type=='SOCKET' and sock.in_out=='INPUT':
   try:values[sock.identifier]={'name':sock.name,'value':val(getattr(i,sock.identifier))}
   except Exception as er:values[sock.identifier]={'name':sock.name,'error':str(er)}
 rows.append({'name':md.name,'rna':[x.identifier for x in i.bl_rna.properties],'attributes':[x for x in dir(i) if not x.startswith('_')],'values':values})
(E/'qualified-original-modifier-input-sockets.json').write_bytes((json.dumps(rows,indent=2)+'\n').encode());print(json.dumps(rows),flush=True)
