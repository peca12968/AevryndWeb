"""Inspect existing attributed Ellie head/rig controls without running its scripts."""
from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';P=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.objects=['GEO-ellie_head','RIG-Ellie']
for ob in b.objects:
 if ob: bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();report={'source':str(P),'head':{},'rig':{},'helpers':{}}
for ob in bpy.data.objects:
 if ob.type=='ARMATURE':
  for pb in ob.pose.bones:
   if any(x in pb.name.lower() for x in ['eyelid','blink','eye_settings','eye-settings','face_settings','face-settings']):report['rig'][pb.name]={'location':list(pb.location),'rotation':list(pb.rotation_euler),'properties':{str(k):repr(v) for k,v in pb.items()}}
 if ob.type=='MESH' and ob.data.shape_keys:report['helpers'][ob.name]=[(k.name,k.value) for k in ob.data.shape_keys.key_blocks]
 if ob.name=='GEO-ellie_head':report['head']={'vertices':len(ob.data.vertices),'modifiers':[(m.name,m.type,getattr(m,'object',None).name if getattr(m,'object',None) else None) for m in ob.modifiers]}
(E/'existing-artist-blink-controls.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('R107_EXISTING_ARTIST_CONTROL_INSPECTION_DONE',len(report['rig']),flush=True)
