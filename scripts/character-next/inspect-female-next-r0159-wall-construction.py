from pathlib import Path
import bpy,numpy as np,json,importlib.util,collections
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0159-native-lid-wall';sp=importlib.util.spec_from_file_location('r159domain',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);h.E=E;a=h.a
b=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['source']);skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update();V,T=a.geometry(skin);faces={f.index:list(f.vertices) for f in skin.data.polygons if f.material_index==0};touch=collections.defaultdict(list)
for fi,f in faces.items():
 for vi in f:touch[vi].append(fi)
domain={187115};queue=list(domain)
while queue:
 fi=queue.pop()
 for vi in faces[fi]:
  for other in touch[vi]:
   if other not in domain:domain.add(other);queue.append(other)
ed=collections.Counter(tuple(sorted((u,v))) for fi in domain for u,v in zip(faces[fi],faces[fi][1:]+faces[fi][:1]));boundary=[edge for edge,n in ed.items() if n==1];graph=collections.defaultdict(list)
for u,v in boundary:graph[u].append(v);graph[v].append(u)
loops=[];remaining=set(graph)
if all(len(v)==2 for v in graph.values()):
 while remaining:
  first=min(remaining);loop=[first];prev=None;cur=first
  while True:
   nxt=next(v for v in graph[cur] if v!=prev)
   if nxt==first:break
   loop.append(nxt);prev,cur=cur,nxt
  loops.append(loop);remaining.difference_update(loop)
ids=sorted(set(v for fi in domain for v in faces[fi]));h.save('actual-cavity-wall-construction.json',{'domainFaces':sorted(domain),'domainVertices':ids,'faces':{str(fi):faces[fi] for fi in sorted(domain)},'boundaryLoops':loops,'boundaryDegreeHistogram':dict(collections.Counter(map(len,graph.values()))),'vertexBounds':[V[ids].min(0),V[ids].max(0)],'loopPositions':[V[loop] for loop in loops]});print('R159_CAVITY_DOMAIN',json.dumps({'faces':len(domain),'vertices':len(ids),'boundaryLoops':[len(x) for x in loops],'degreeHistogram':dict(collections.Counter(map(len,graph.values()))),'bounds':[V[ids].min(0).tolist(),V[ids].max(0).tolist()]}),flush=True)
