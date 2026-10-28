
from pathlib import Path
import bpy,json
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0208-complete-native-style-construction';bpy.ops.wm.open_mainfile(filepath='C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');rows=[]
for md in bpy.data.objects['basic_short_hair'].modifiers:
 ins=[]
 for i in md.properties.inputs:
  props={}
  for prop in i.bl_rna.properties:
   if prop.identifier=='rna_type':continue
   try:
    v=getattr(i,prop.identifier)
    if hasattr(v,'name'):v={'name':v.name,'type':type(v).__name__}
    elif prop.is_array:v=list(v)
    elif prop.type in ['COLLECTION','POINTER']:v=str(v)
    props[prop.identifier]=v
   except Exception as er:props[prop.identifier]=str(er)
  ins.append({'type':type(i).__name__,'props':props})
 rows.append({'name':md.name,'inputs':ins})
(E/'qualified-original-modifier-input-sockets.json').write_bytes((json.dumps(rows,indent=2)+'\n').encode());print(json.dumps(rows),flush=True)
