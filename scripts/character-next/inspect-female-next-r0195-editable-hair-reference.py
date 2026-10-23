"""Read original editable groom data only; execute no embedded code or asset import."""
from pathlib import Path
import bpy,json,datetime,hashlib
R=Path('D:/Download/Aevrynd');C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0195-local-growth-domains'
p=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend'
assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
bpy.ops.wm.open_mainfile(filepath=str(p))
objects=[]
for o in bpy.data.objects:
 d=o.data
 objects.append({'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world],'vertices':len(d.vertices) if o.type=='MESH' else None,'curves':len(d.curves) if o.type=='CURVES' else None,'points':len(d.points) if o.type=='CURVES' else None,'splines':len(d.splines) if o.type=='CURVE' else None,'modifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in o.modifiers],'particleSystems':[{'name':s.name,'type':s.settings.type,'count':s.settings.count,'hairStep':s.settings.hair_step} for s in o.particle_systems],'hairSurface':d.surface.name if o.type=='CURVES' and d.surface else None,'surfaceUV':d.surface_uv_map if o.type=='CURVES' else None})
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(p),'objects':objects,'textBlocks':[{'name':t.name,'text':t.as_string()[:30000]} for t in bpy.data.texts],'nodeGroups':[{'name':g.name,'nodes':len(g.nodes)} for g in bpy.data.node_groups],'sceneCamera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'noSourceSaveOrEngineAssetImport':True,'licenseVersionNotAssumed':True}
(E/'original-editable-reference-inspection.json').write_text(json.dumps(q,indent=2)+'\n',encoding='utf-8')
print('R195_ONE_EDITABLE_REFERENCE_INSPECTION_DONE',json.dumps({'objects':len(objects),'curves':[x for x in objects if x['type']=='CURVES'],'texts':[t['name'] for t in q['textBlocks']]}),flush=True)
