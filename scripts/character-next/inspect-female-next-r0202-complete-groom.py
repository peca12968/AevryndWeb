from pathlib import Path
import bpy,json,datetime,hashlib
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0202-independent-complete-groom';p=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5'
bpy.ops.wm.open_mainfile(filepath=str(p));rows=[]
for o in bpy.data.objects:
 if o.type in {'CURVES','CURVE'}:rows.append({'name':o.name,'type':o.type,'curves':len(o.data.curves) if o.type=='CURVES' else len(o.data.splines),'points':len(o.data.position_data) if o.type=='CURVES' else None,'surface':o.data.surface.name if o.type=='CURVES' and o.data.surface else None,'hideRender':o.hide_render,'hideViewport':o.hide_get(),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(p),'rows':rows,'texts':[{'name':t.name,'text':t.as_string()[:20000]} for t in bpy.data.texts],'sourceNotSaved':True,'embeddedScriptsNotExecuted':True}
(E/'cc0-original-groom-inventory.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R202_CC0_INVENTORY_DONE',json.dumps(rows),flush=True)
