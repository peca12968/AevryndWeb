import bpy
from mathutils import Vector
for o in bpy.data.objects:
 role=str(o.get('aevrynd_layer',''))+' '+str(o.get('aevrynd_role',''))
 if o.type=='MESH' and ('hair' in role.lower() or o.name.lower().startswith('hair')):
  pts=[o.matrix_world@Vector(c) for c in o.bound_box]
  lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
  print('HAIR',o.name,'role=',role,'v=',len(o.data.vertices),'f=',len(o.data.polygons),'bounds=',tuple(round(x,4) for x in (*lo,*hi)),'parent=',getattr(o.parent,'name',None),'mods=',[(m.type,getattr(getattr(m,'object',None),'name',None)) for m in o.modifiers])
for o in bpy.data.objects:
 if o.type=='ARMATURE':
  print('RIG',o.name,'bones',len(o.data.bones),'sample',[b.name for b in o.data.bones][:30])
