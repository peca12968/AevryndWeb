"""Inspect the actual artist external eye surface and its driver targets, not helper volumes."""
from pathlib import Path
import bpy,json,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0109-complete-native-lid-sheet';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
def target(t):return {'id':t.id.name if t.id else None,'path':t.data_path,'bone':t.bone_target,'transform':t.transform_type,'space':t.transform_space}
with bpy.data.libraries.load(str(SRC),link=False) as (a,b):b.objects=['GEO-ellie_head','RIG-Ellie','GEO-ellie_eye.L','GEO-ellie_eye.R']
for ob in list(bpy.data.objects):
 if ob.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();report={'source':str(SRC),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rigProperties':{},'bones':{},'drivers':{},'head':{}}
rig=bpy.data.objects['RIG-Ellie'];head=bpy.data.objects['GEO-ellie_head'];report['rigProperties']={k:repr(v) for k,v in rig.items()}
for pb in rig.pose.bones:
 if ('eye' in pb.name.lower() or 'lid' in pb.name.lower() or len(pb.keys())) and not pb.name.startswith(('ORG-','DEF-','STR-')):report['bones'][pb.name]={'location':list(pb.location),'rotation':list(pb.rotation_euler),'properties':{k:repr(v) for k,v in pb.items()},'constraints':[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None),'subtarget':getattr(c,'subtarget',None),'action':getattr(getattr(c,'action',None),'name',None)} for c in pb.constraints]}
for ob in list(bpy.data.objects):
 for owner in [ob,getattr(ob.data,'shape_keys',None)]:
  ad=getattr(owner,'animation_data',None)
  if ad:
   rows=[]
   for fc in ad.drivers:
    if any(x in (fc.data_path+' '+fc.driver.expression).lower() for x in ['eye','lid','blink']):rows.append({'path':fc.data_path,'index':fc.array_index,'expression':fc.driver.expression,'valid':fc.driver.is_valid,'variables':[{'name':v.name,'type':v.type,'targets':[target(t) for t in v.targets]} for v in fc.driver.variables]})
   if rows:report['drivers'][owner.name]=rows
report['head']={'rawVertices':len(head.data.vertices),'keys':[(k.name,k.value) for k in head.data.shape_keys.key_blocks] if head.data.shape_keys else [],'modifiers':[(m.name,m.type,getattr(getattr(m,'object',None),'name',None),m.show_viewport,m.show_render) for m in head.modifiers],'allObjectNames':[ob.name for ob in bpy.data.objects]}
(E/'actual-artist-lid-controls.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('R109_ARTIST_ACTUAL_LID_CONTROLS_INSPECTED',len(report['bones']),list(report['drivers']),flush=True)
