"""Read two already licensed studio hair constructions; no evaluation or source scripts."""
from pathlib import Path
import bpy,json,hashlib,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom'
rows=[]
for rel in ['blender-studio-ellie-v1-cc-by4/ellie.blend','blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend']:
 p=R/'Reference/character'/rel;bpy.ops.wm.open_mainfile(filepath=str(p));obs=[]
 for o in bpy.data.objects:
  if o.type in ['MESH','CURVE','CURVES']:
   obs.append({'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'curves':len(o.data.curves) if o.type=='CURVES' else len(o.data.splines) if o.type=='CURVE' else None,'bounds':[list(x) for x in o.bound_box],'matrix':[list(r) for r in o.matrix_world],'materials':[m.name if m else None for m in o.data.materials],'modifiers':[(m.name,m.type) for m in o.modifiers],'particleSystems':[s.name for s in o.particle_systems]})
 rows.append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'objects':obs,'sourceNotSaved':True,'scriptsDisabled':not bpy.context.preferences.filepaths.use_scripts_auto_execute})
(E/'studio-hair-construction-inspection.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print('R130_STUDIO_NATIVE_CONSTRUCTIONS_READ',[(r['source'],len(r['objects'])) for r in rows],flush=True)
