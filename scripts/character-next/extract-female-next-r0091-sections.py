"""Read authored connected clump topology for an explicit section-based rebuild."""
from pathlib import Path
import bpy, numpy as np, json, importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r91src',Path(__file__).with_name('build-female-next-r0090-rain-hair.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0090-b-rain-hair-shape-study.blend'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[];arrays={}
for name in ['AFN90_RAIN_HAIR_MAIN','AFN90_RAIN_HAIR_PONYTAIL','AFN90_RAIN_HAIR_STRAND']:
 o=bpy.data.objects[name];d=o.data;P=m.native_mesh(o);edges=m.q.arr(d.edges,'vertices',len(d.edges),2,'i4');d.calc_loop_triangles();T=m.q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,'i4');adj=[[] for _ in P]
 for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
 cc=np.full(len(P),-1,'i4');parts=[]
 for start in range(len(P)):
  if cc[start]>=0:continue
  ix=len(parts);stack=[start];cc[start]=ix;ids=[]
  while stack:
   a=stack.pop();ids.append(a)
   for b in adj[a]:
    if cc[b]<0:cc[b]=ix;stack.append(b)
  ids=np.array(ids,'i4');parts.append({'component':ix,'vertices':len(ids),'centre':P[ids].mean(0).tolist(),'bounds':[P[ids].min(0).tolist(),P[ids].max(0).tolist()]})
 arrays[name+'_world']=P;arrays[name+'_edges']=edges;arrays[name+'_triangles']=T;arrays[name+'_component']=cc
 rows.append({'name':name,'components':parts})
band=m.q.geom(bpy.data.objects['AFN90_RAIN_HAIRBAND'])[1].mean(0);arrays['bandCentre']=band;np.savez_compressed(E/'authored-clump-topology.npz',**arrays);(E/'authored-clump-topology.json').write_text(json.dumps(rows,indent=2)+'\n');print('R91_SECTION_INPUT',json.dumps(rows),flush=True)
