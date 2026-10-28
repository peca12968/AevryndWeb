from pathlib import Path
import bpy,json,hashlib,numpy as np,datetime
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);R=Path(p['directProjectAccess']);E=A/'evidence/character-female-next/r0211-complete-regional-lock-foundation';f=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend';assert hashlib.file_digest(f.open('rb'),'sha256').hexdigest()=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48';bpy.ops.wm.open_mainfile(filepath=str(f));rows=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES':
  d=ob.data;raw=np.array([list(x.vector) for x in d.position_data]);roots=np.array([list(c.points[0].position) for c in d.curves]);mods=[]
  for md in ob.modifiers:
   ng=md.node_group;inputs=[]
   for so in ng.interface.items_tree:
    if so.item_type=='SOCKET' and so.in_out=='INPUT':
     v=getattr(md.properties.inputs,so.identifier,None);val=getattr(v,'value',None)
     if hasattr(val,'name'):val=val.name
     elif not isinstance(val,(str,int,float,bool,type(None))):
      try:val=list(val)
      except:val=str(val)
     inputs.append({'name':so.name,'id':so.identifier,'value':val,'type':getattr(v,'type',None),'attribute':getattr(v,'attribute_name',None)})
   mods.append({'name':md.name,'group':ng.name,'inputs':inputs})
  rows.append({'name':ob.name,'rawCurves':len(d.curves),'rawPoints':len(raw),'rootLocalBounds':[roots.min(0).tolist(),roots.max(0).tolist()],'rawLocalBounds':[raw.min(0).tolist(),raw.max(0).tolist()],'surface':d.surface.name if d.surface else None,'mods':mods})
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(f),'embeddedTexts':{x.name:x.as_string()[:25000] for x in bpy.data.texts},'rows':rows};(E/'source-operative-and-license-inspection.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R211_REFERENCE_OPERATIVE_AND_LICENSE_READ',json.dumps({'texts':q['embeddedTexts'],'long':next(x for x in rows if x['name']=='long hair main')}),flush=True)
