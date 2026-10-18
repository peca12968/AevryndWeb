"""Measure native eye helper bounds and corresponding body/socket surfaces."""
import bpy, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0006-native-eyes';E.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0005-native-source.blend'))
raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];body=bpy.data.objects['AFN_R0005_Body'];K=raw.data.shape_keys.key_blocks;coords=[v.co.copy() for v in K[0].data]
for k in K[1:]:
 if k.mute:continue
 for i,v in enumerate(k.data):coords[i]+=k.value*(v.co-k.relative_key.data[i].co)
coords=[raw.matrix_world@v for v in coords];dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);m=ev.to_mesh();P=[ev.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(P,[tuple(p.vertices) for p in m.polygons]);result=[]
for name in ('helper-l-eye','helper-r-eye','joint-l-eye','joint-r-eye','joint-l-upperlid','joint-l-lowerlid','joint-r-upperlid','joint-r-lowerlid'):
 g=raw.vertex_groups.get(name)
 if g is None:continue
 ids=[v.index for v in raw.data.vertices if any(a.group==g.index for a in v.groups)];V=[coords[i] for i in ids];bounds=[[min(v[a] for v in V),max(v[a] for v in V)] for a in range(3)];centre=Vector([(v[0]+v[1])*.5 for v in bounds]);rays=[]
 for dx,dz in ((0.,0.),(-.01,0.),(.01,0.),(0.,.005),(0.,-.005)):
  hit=tree.ray_cast(Vector((centre.x+dx,-.4,centre.z+dz)),Vector((0.,1.,0.)),.45)
  rays.append({'dx':dx,'dz':dz,'point':list(hit[0]) if hit[0] else None,'normal':list(hit[1]) if hit[1] else None,'polygon':hit[2]})
 result.append({'group':name,'vertices':len(V),'bounds':bounds,'centre':list(centre),'rays':rays})
ev.to_mesh_clear();(E/'native-orbit-measurements.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
