"""Inspect original MakeHuman UV compatibility and current skin shader inputs."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows'
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0010-c-spaced-lashes-study.blend'))
o=bpy.data.objects['AFN_R0008_Body'];m=o.data
material=m.materials[0]
m.calc_loop_triangles();tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
samples=[]
for x,z in [(-.028,1.435),(.028,1.435),(-.042,1.435),(.042,1.435),(-.025,1.505),(.025,1.505)]:
    hit,n,ti,d=tree.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.4);t=m.loop_triangles[ti];a,b,c=[o.matrix_world@m.vertices[i].co for i in t.vertices]
    u=b-a;v=c-a;w=hit-a;den=u.dot(u)*v.dot(v)-u.dot(v)**2;p=(v.dot(v)*w.dot(u)-u.dot(v)*w.dot(v))/den;q=(u.dot(u)*w.dot(v)-u.dot(v)*w.dot(u))/den;bc=(1-p-q,p,q)
    uv=sum((m.uv_layers.active.data[li].uv*weight for li,weight in zip(t.loops,bc)),Vector((0,0)))
    samples.append({'world':list(hit),'uv':list(uv)})
result={'uvLayers':[{'name':u.name,'loops':len(u.data),'min':[min(v.uv[i] for v in u.data) for i in range(2)],'max':[max(v.uv[i] for v in u.data) for i in range(2)]} for u in m.uv_layers],
        'activeUV':m.uv_layers.active.name,'referenceSkinSamples':samples,'materials':[x.name for x in m.materials],
        'shaders':[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:list(i.default_value) if hasattr(getattr(i,'default_value',None),'__iter__') and not isinstance(i.default_value,str) else getattr(i,'default_value',None) for i in n.inputs}} for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'],
        'lights':[{'name':x.name,'energy':x.data.energy,'size':x.data.size,'position':list(x.location)} for x in bpy.data.objects if x.type=='LIGHT'],
        'view':{'transform':bpy.context.scene.view_settings.view_transform,'exposure':bpy.context.scene.view_settings.exposure}}
(E/'uv-and-skin-inspection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
