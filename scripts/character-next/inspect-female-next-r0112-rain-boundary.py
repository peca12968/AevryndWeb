from pathlib import Path
from collections import defaultdict,Counter
import json,numpy as np
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0112-topological-ocular-graft';E.mkdir(exist_ok=True);d=np.load(E.parent/'r0111-native-mobile-lid-mesh/actual-rain-ocular-geometry.npz');V=d['head_neutralWorld'];ids=d['head_neutralLoopVertexIndices'];counts=d['head_neutralPolygonCounts'];starts=np.r_[0,np.cumsum(counts)[:-1]];polys=[ids[s:s+n].tolist() for s,n in zip(starts,counts)];ef=defaultdict(list)
for f,p in enumerate(polys):
 for a,b in zip(p,p[1:]+p[:1]):ef[tuple(sorted((a,b)))].append(f)
adj=defaultdict(list)
for (a,b),fs in ef.items():
 if len(fs)==1:adj[a].append(b);adj[b].append(a)
seen=set();loops=[]
for v in adj:
 if v in seen:continue
 loop=[v];prev=-1
 while True:
  seen.add(loop[-1]);ns=[i for i in adj[loop[-1]] if i!=prev];assert len(ns)>=1
  n=ns[0]
  if n==v:break
  prev=loop[-1];loop.append(n);assert len(loop)<len(adj)+1
 loops.append(loop)
rows=[{'loop':x,'vertices':len(x),'centre':V[x].mean(0).tolist(),'min':V[x].min(0).tolist(),'max':V[x].max(0).tolist()} for x in loops];report={'source':'Actual Rain evaluated external head topology, current source neutral/half/closed graph','boundaries':rows,'allBoundaryVertexDegreeTwo':all(len(x)==2 for x in adj.values()),'vertices':len(V),'faces':len(polys)};(E/'actual-rain-eye-boundaries.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='boundaries'}));print(json.dumps([{k:v for k,v in x.items() if k!='loop'} for x in rows]))
