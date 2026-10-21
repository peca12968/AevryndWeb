from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0109-complete-native-lid-sheet';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
with bpy.data.libraries.load(str(SRC),link=False) as (a,b):
 names=[n for n in a.objects if any(z in n.lower() for z in ['eyelid','eyelash','eye.','head'])];b.objects=[n for n in names if n.startswith('GEO-')]+['RIG-Ellie']
for ob in list(bpy.data.objects):
 if ob.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();rig=bpy.data.objects['RIG-Ellie'];rows={}
for ob in b.objects:
 if ob.type=='MESH':rows[ob.name]={'vertices':len(ob.data.vertices),'modifiers':[(m.name,m.type,getattr(getattr(m,'object',None),'name',None)) for m in ob.modifiers],'groups':[g.name for g in ob.vertex_groups if any(x in g.name.lower() for x in ['lid','eye'])]}
limits={}
for part in ['Upper','Lower']:
 p=rig.pose.bones['ACT-Eyelid_'+part+'.L'];limits[part]=[{'name':c.name,'type':c.type,'minY':getattr(c,'min_y',None),'maxY':getattr(c,'max_y',None),'owner_space':c.owner_space} for c in p.constraints]
actions=[]
for p in rig.pose.bones:
 for c in p.constraints:
  if c.type=='ACTION' and 'Eyelid_Upper_Close' in c.name:actions.append({'bone':p.name,'action':c.action.name,'frameStart':c.frame_start,'frameEnd':c.frame_end,'eval_time':c.eval_time,'useEvalTime':c.use_eval_time})
report={'names':names,'objects':rows,'controlLimits':limits,'upperActions':actions[:5]};(E/'actual-eye-components.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'names':names,'objects':{k:v['vertices'] for k,v in rows.items()},'limits':limits,'actions':actions[:2]}),flush=True)
