"""Independent neutral closed-body ray test for all negative nearest-normal eye points."""
import bpy,json,math
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0008-evaluated-sockets'
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0008-b-balanced-study.blend'))
dg=bpy.context.evaluated_depsgraph_get();body=bpy.data.objects['AFN_R0008_Body'];ev=body.evaluated_get(dg);mesh=ev.to_mesh();P=[ev.matrix_world@v.co for v in mesh.vertices];mesh.calc_loop_triangles();T=[tuple(t.vertices) for t in mesh.loop_triangles];tree=BVHTree.FromPolygons(P,T,all_triangles=True)
edges=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in mesh.polygons for i in range(len(p.vertices)))
directions=[Vector(v).normalized() for v in ((1.,.371,.193),(-.317,1.,.233),(.217,-.181,1.),(-1.,-.211,.317),(.193,.271,-1.))]
def count(p,d):
 p=p.copy();n=0
 for step in range(80):
  h=tree.ray_cast(p,d,3.)
  if h[0] is None:return n
  n+=1;p=h[0]+d*.000001
 return None
results=[]
for obj in (o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')):
 pe=obj.evaluated_get(dg);pm=pe.to_mesh();counts=Counter();samples=[];negative=0;minimum=float('inf')
 for i,v in enumerate(pm.vertices):
  p=pe.matrix_world@v.co;h=tree.find_nearest(p);value=(p-h[0]).dot(h[1].normalized());minimum=min(minimum,h[3])
  if value>=0:continue
  negative+=1;rays=[count(p,d) for d in directions];parity=[n%2 if n is not None else None for n in rays];kind='outside' if all(n==0 for n in parity) else ('inside' if all(n==1 for n in parity) else 'ambiguous');counts[kind]+=1
  if len(samples)<5:samples.append({'point':i,'normalSignedM':value,'unsignedDistanceM':h[3],'rayCounts':rays,'classification':kind})
 results.append({'part':obj.name,'rawNegativeVertices':negative,'minimumUnsignedDistanceM':minimum,'rayClassifications':dict(counts),'samples':samples});pe.to_mesh_clear()
ev.to_mesh_clear();result={'revision':'female-next-r0008','variant':'b-balanced','pose':'neutral','boundaryEdges':sum(n==1 for n in edges.values()),'nonManifoldEdges':sum(n>2 for n in edges.values()),'directions':[list(d) for d in directions],'rayStepM':.000001,'results':results,'scope':'Independent neutral diagnostic only; all pose/variant certification is still required.'};(E/'neutral-containment-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='samples'} for r in results],indent=2))
