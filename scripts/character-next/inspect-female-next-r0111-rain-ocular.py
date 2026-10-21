"""Inspect actual existing Rain ocular topology/controls, no source scripts."""
from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';SRC=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend'
with bpy.data.libraries.load(str(SRC),link=False) as (a,b):
 names=[n for n in a.objects if n.startswith(('GEO-','RIG-')) and any(x in n.lower() for x in ['body','head','face','eye','rig-rain','rig-rain'])];b.objects=names
for ob in list(bpy.data.objects):
 if ob.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();report={'source':str(SRC),'loaded':[o.name for o in b.objects if o],'meshes':{},'rigs':{}}
for ob in b.objects:
 if ob.type=='MESH':report['meshes'][ob.name]={'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'keys':[(k.name,k.value) for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'modifiers':[(m.name,m.type,getattr(getattr(m,'object',None),'name',None)) for m in ob.modifiers],'eyeGroups':[g.name for g in ob.vertex_groups if any(x in g.name.lower() for x in ['eye','lid'])]}
 if ob.type=='ARMATURE':
  report['rigs'][ob.name]={'bones':{p.name:{'props':{k:repr(v) for k,v in p.items()},'loc':list(p.location),'constraints':[{'name':c.name,'type':c.type,'minY':getattr(c,'min_y',None),'maxY':getattr(c,'max_y',None),'space':c.owner_space} for c in p.constraints]} for p in ob.pose.bones if any(x in p.name.lower() for x in ['eyelid','blink','eye_settings']) and not p.name.startswith(('ORG-','DEF-','STR-'))},'drivers':[{'path':f.data_path,'expression':f.driver.expression,'variables':[{'name':v.name,'targets':[{'id':t.id.name if t.id else None,'bone':t.bone_target,'path':t.data_path,'transform':t.transform_type} for t in v.targets]} for v in f.driver.variables]} for f in ob.animation_data.drivers if 'Eyelid' in f.data_path and ('action_props' in f.data_path or 'blink' in f.data_path.lower())] if ob.animation_data else []}
(E/'actual-rain-ocular-source.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report),flush=True)
