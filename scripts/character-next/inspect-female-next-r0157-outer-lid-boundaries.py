"""Inspect actual artist outer lid face bands and their true shared boundaries."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,collections,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0157-outer-lid-retopology';E.mkdir(exist_ok=True)
sp=importlib.util.spec_from_file_location('r157boundary',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
b=json.loads((E.parent/'r0155-native-blink/b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];V,T=a.geometry(skin);d=skin.data;faces=[list(p.vertices) for p in d.polygons];matid=next(i for i,m in enumerate(d.materials) if m and m.name=='AFN126_NATIVE_ARTIST_HEAD_MATERIAL');headfaces=[p.index for p in d.polygons if p.material_index==matid];edges=np.unique(np.sort(np.array([e for i in headfaces for e in zip(faces[i],faces[i][1:]+faces[i][:1])],'i4'),axis=1),axis=0);g=h.h.graph(V,edges);construction=json.loads((E.parent/'r0139-native-lid-follow/native-lid-follow-construction.json').read_text());allEdges=collections.defaultdict(list)
for i,f in enumerate(faces):
 for u,v in zip(f,f[1:]+f[:1]):allEdges[tuple(sorted((u,v)))].append(i)
reports=[];savearrays={}
for side in ['L','R']:
 seeds=np.unique(np.concatenate([np.array(construction['actualSourceNativeDomains'][side+'_'+k]['actualSkinSeedIds']) for k in ['UPPER','LOWER']]));dist,owner=h.h.geodesic(g,seeds,.011);chosen=[i for i in headfaces if np.mean(dist[faces[i]])<.007];sel=set(chosen);counts=collections.Counter(tuple(sorted((u,v))) for i in chosen for u,v in zip(faces[i],faces[i][1:]+faces[i][:1]));boundary=[edge for edge,n in counts.items() if n==1];adj=collections.defaultdict(list)
 for u,v in boundary:adj[u].append(v);adj[v].append(u)
 remaining=set(tuple(e) for e in boundary);loops=[];branched={k:len(v) for k,v in adj.items() if len(v)!=2}
 while remaining and not branched:
  edge=next(iter(remaining));loop=[edge[0],edge[1]];remaining.remove(edge)
  while loop[-1]!=loop[0]:
   options=[v for v in adj[loop[-1]] if tuple(sorted((loop[-1],v))) in remaining]
   if not options:break
   nxt=options[0];remaining.remove(tuple(sorted((loop[-1],nxt))));loop.append(nxt)
  loops.append(loop[:-1] if loop[-1]==loop[0] else loop)
 rows=[]
 for k,loop in enumerate(loops):
  other=collections.Counter(d.polygons[j].material_index for u,v in zip(loop,loop[1:]+loop[:1]) for j in allEdges[tuple(sorted((u,v)))] if j not in sel);rows.append({'loop':k,'vertices':len(loop),'originalVertexIds':loop,'meanWorld':V[loop].mean(0).tolist(),'rangeWorld':np.ptp(V[loop],axis=0).tolist(),'adjacentUnselectedMaterials':{d.materials[mi].name:int(n) for mi,n in other.items()}});savearrays[side+'-loop'+str(k)]=np.array(loop,'i4')
 reports.append({'side':side,'seedCount':len(seeds),'chosenOuterPolygons':len(chosen),'boundaryEdges':len(boundary),'branchedBoundaryDegrees':branched,'loops':rows});savearrays[side+'-selectedPolygons']=np.array(chosen,'i4')
np.savez_compressed(E/'actual-outer-lid-boundaries.npz',**savearrays);out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'actualSkin':skin.name,'artistOuterMaterialId':matid,'reports':reports,'scope':'Actual artist outer skin band only, excluding cavity/material0. Boundary source IDs and topology retained; no claim that these engineering band widths are anatomical calibration.','sourceUnmodified':True};(E/'actual-outer-lid-boundaries.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R157_ACTUAL_OUTER_LID_BOUNDARIES_DONE',json.dumps([{k:v for k,v in row.items() if k!='loops'}|{'loops':[{k:v for k,v in x.items() if k!='originalVertexIds'} for x in row['loops']]} for row in reports]),flush=True)
