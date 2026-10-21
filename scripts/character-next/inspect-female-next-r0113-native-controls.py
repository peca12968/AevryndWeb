"""Inspect actual native animation-head controls, no assumed rig from its name."""
from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0113-coherent-head-foundation';SOURCE=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
names=['GEO-head_animation_realistic','GEO-head_sculpting_realistic'];report={}
for name in names:
 ob=bpy.data.objects.get(name)
 if not ob:continue
 report[name]={'type':ob.type,'parent':ob.parent.name if ob.parent else None,'modifiers':[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in ob.modifiers],'shapeKeys':[k.name for k in ob.data.shape_keys.key_blocks] if ob.type=='MESH' and ob.data.shape_keys else [],'vertexGroups':[g.name for g in ob.vertex_groups],'action':ob.animation_data.action.name if ob.animation_data and ob.animation_data.action else None}
report['actualArmatures']=[{'name':o.name,'bones':len(o.data.bones)} for o in bpy.data.objects if o.type=='ARMATURE']
(E/'actual-native-head-controls.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('R113_ACTUAL_NATIVE_HEAD_CONTROLS_INSPECTED',report,flush=True)
