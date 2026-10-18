"""Find actual skin/socket front-depth transitions before authoring eye-rim geometry."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0010-eye-rim'; E.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0009-a-slab-thickness-study.blend'))
b=bpy.data.objects['AFN_R0008_Body']; m=b.data; m.calc_loop_triangles(); tree=BVHTree.FromPolygons([b.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
raw=bpy.data.objects['AFN_R0005_EditableNativeCC0']
groups=[g.name for g in raw.vertex_groups if any(s in g.name.lower() for s in ('eye','lid','face','brow'))]
rows=[]
for x in [.009,.012,.015,.018,.021,.024,.027,.03,.033,.036,.039,.042,.045]:
    values=[]
    for iz in range(-90,91):
        z=1.46+iz*.00015; p,n,fi,d=tree.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.4)
        if p: values.append([z,p.y,fi,list(n)])
    jumps=[{'before':values[i-1],'after':values[i]} for i in range(1,len(values)) if abs(values[i][1]-values[i-1][1])>.002]
    rows.append({'x':x,'jumps':jumps,'nearestAtEyeZ':min(values,key=lambda v:abs(v[0]-1.46)) if values else None})
K=raw.data.shape_keys.key_blocks; P=[v.co.copy() for v in K[0].data]
for k in K[1:]:
    if not k.mute:
        for i,v in enumerate(k.data): P[i]+=k.value*(v.co-k.relative_key.data[i].co)
helpers={}
for name in groups:
    if 'eyelashes' not in name: continue
    g=raw.vertex_groups[name]; pts=[{'vertex':v.index,'co':list(raw.matrix_world@P[v.index])} for v in raw.data.vertices if any(x.group==g.index for x in v.groups)]
    helpers[name]={'points':pts,'bounds':[[min(p['co'][i] for p in pts),max(p['co'][i] for p in pts)] for i in range(3)]}
result={'groups':groups,'rows':rows,'helpers':helpers,'nativeShapeKeys':[k.name for k in raw.data.shape_keys.key_blocks]}
(E/'rim-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
