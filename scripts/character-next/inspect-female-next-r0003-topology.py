"""Record evaluated face geometry and key/edge provenance before local rebuilding."""
import bpy, json, math
from pathlib import Path
from collections import Counter, defaultdict
ROOT=Path(r'D:\Download\Aevrynd')
OUT=ROOT/'Evidence/character-female-next/r0003-topology'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'engine/assets/characters/female-next/source/aevrynd-female-next-r0001-baseline.blend'))
b=bpy.data.objects['AevryndFemaleCC0PalpebralClosure_R1097']
scene=bpy.context.scene; scene.frame_set(1)
keys=b.data.shape_keys.key_blocks
mixed=[v.co.copy() for v in keys[0].data]
for key in keys[1:]:
 if key.mute: continue
 for i,v in enumerate(key.data): mixed[i]+=key.value*(v.co-key.relative_key.data[i].co)
world=[b.matrix_world@v for v in mixed]
counts=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in b.data.polygons for i in range(len(p.vertices)))
boundary=[edge for edge,n in counts.items() if n==1]
adj=defaultdict(list)
for a,c in boundary: adj[a].append(c);adj[c].append(a)
loops=[];pending=set(adj)
while pending:
 seed=min(pending); stack=[seed]; component=set()
 while stack:
  i=stack.pop()
  if i in component: continue
  component.add(i);stack.extend(adj[i])
 pending-=component
 loops.append({'count':len(component),'vertices':sorted(component),'bounds':[[min(world[i][axis] for i in component),max(world[i][axis] for i in component)] for axis in range(3)],'regularDegree2':all(len(adj[i])==2 for i in component)})
face=[i for i,v in enumerate(world) if v.z>1.30 and v.y<-.01]
dump={'matrix': [list(r) for r in b.matrix_world], 'keys':[{'name':k.name,'value':k.value,'mute':k.mute,'relative':k.relative_key.name} for k in keys], 'customProperties':{k:str(v)[:2000] for k,v in b.items()},'groups':[g.name for g in b.vertex_groups], 'boundaries':loops,'modifiers':[{'name':m.name,'type':m.type} for m in b.modifiers],'faceVertices':[{'i':i,'basis':list(keys[0].data[i].co),'mixed':list(world[i]),'normal':list(b.data.vertices[i].normal)} for i in face],'facePolygons':[{'i':p.index,'verts':list(p.vertices),'material':p.material_index} for p in b.data.polygons if any(i in set(face) for i in p.vertices)]}
(OUT/'topology.json').write_text(json.dumps(dump,indent=2),encoding='utf-8')
print(json.dumps({k:dump[k] for k in ('matrix','keys','customProperties','modifiers','groups')},indent=2))
print('BOUNDARIES='+json.dumps([{k:v for k,v in q.items() if k!='vertices'} for q in loops]))
