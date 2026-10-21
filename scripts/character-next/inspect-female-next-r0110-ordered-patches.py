from pathlib import Path
import numpy as np,json,collections
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0110-ordered-lid-topology';P=np.load(E.parent/'r0107-native-coarse-lid-cage/native-coarse-lid-poses-pinned.npz');V=P['neutralFineWorld'];T=P['fineTriangles'];rings=json.loads((E.parent/'r0108-visible-eyelid-rim/visible-rim-causal-diagnostic.json').read_text('utf8'))['nativeQuadRows']
def polyFromTris(T):
 out=[]
 for a,b in T.reshape(-1,2,3):
  edges=[]
  for tri in [a,b]:edges.extend([(int(tri[i]),int(tri[(i+1)%3])) for i in range(3)])
  counts=collections.Counter(tuple(sorted(e)) for e in edges);edges=[e for e in edges if counts[tuple(sorted(e))]==1];assert len(edges)==4;mapping=dict(edges);row=[edges[0][0]]
  for j in range(3):row.append(mapping[row[-1]])
  out.append(row)
 return out
def edges(polys):
 out=collections.defaultdict(list)
 for f,p in enumerate(polys):
  for a,b in zip(p,p[1:]+p[:1]):out[tuple(sorted((a,b)))].append(f)
 return out
def strips(loop,ef,polys,choose):
 out=[]
 for a,b in zip(loop,np.roll(loop,-1)):
  edge=tuple(sorted((int(a),int(b))));p0=[f for f in ef[edge] if choose(f)];assert len(p0)==1,(edge,p0);prev=-1;fi=p0[0];row=[]
  for j in range(12):
   p=polys[fi]
   if len(p)!=4:break
   row.append({'face':fi,'edge':edge});k=next(k for k in range(4) if tuple(sorted((p[k],p[(k+1)%4])))==edge);other=tuple(sorted((p[(k+2)%4],p[(k+3)%4])));nextf=[f for f in ef[other] if f!=fi]
   if len(nextf)!=1:break
   prev,fi=fi,nextf[0];edge=other
  out.append(row)
 return out
polys=polyFromTris(T);ef=edges(polys);cut=set()
for side in rings:
 loop=rings[side]['nativeRows'][0];cut.update(tuple(sorted((int(a),int(b)))) for a,b in zip(loop,np.roll(loop,-1)))
adj=collections.defaultdict(list)
for e,fs in ef.items():
 if e not in cut and len(fs)==2:adj[fs[0]].append(fs[1]);adj[fs[1]].append(fs[0])
components=np.full(len(polys),-1,int);sizes=[]
for f in range(len(polys)):
 if components[f]>=0:continue
 idx=len(sizes);todo=[f];components[f]=idx;count=0
 while todo:
  p=todo.pop();count+=1
  for n in adj[p]:
   if components[n]<0:components[n]=idx;todo.append(n)
 sizes.append(count)
big=int(np.argmax(sizes));report={'nativeComponentFacesAfterUVSeamCut':sizes,'nativeStrips':{}};arrays={'nativePolygons':np.array(polys)}
for side in rings:
 loop=rings[side]['nativeRows'][0];s=strips(loop,ef,polys,lambda f:components[f]==big);report['nativeStrips'][side]=s
a=np.load(E.parent/'r0109-complete-native-lid-sheet/actual-artist-external-blink.npz');AV=a['neutralWorld'];counts=a['neutralPolygonCounts'];ids=a['neutralLoopVertexIndices'];starts=np.r_[0,np.cumsum(counts)[:-1]];ap=[ids[start:start+n].tolist() for start,n in zip(starts,counts)];ae=edges(ap);boundary=[e for e,fs in ae.items() if len(fs)==1];ba=collections.defaultdict(list)
for i,j in boundary:ba[i].append(j);ba[j].append(i)
seen=set();loops=[]
for v in ba:
 if v in seen:continue
 loop=[v];prev=-1
 while True:
  seen.add(loop[-1]);ns=[x for x in ba[loop[-1]] if x!=prev];n=ns[0]
  if n==v:break
  prev=loop[-1];loop.append(n)
  assert len(loop)<len(ba)+1
 loops.append(loop)
report['artistBoundaryLoops']=[{'vertices':len(loop),'centre':AV[loop].mean(0).tolist(),'min':AV[loop].min(0).tolist(),'max':AV[loop].max(0).tolist()} for loop in loops];report['artistStrips']={}
for side,sign in [('L',1),('R',-1)]:
 loop=min(loops,key=lambda l:np.linalg.norm(AV[l].mean(0)-np.array([sign*.03,-.11,1.463])));report['artistStrips'][side]={'loop':loop,'strips':strips(loop,ae,ap,lambda f:True)}
arrays['artistPolygons']=np.array(ap) if all(n==4 for n in counts) else np.zeros(0);np.savez_compressed(E/'ordered-native-artist-topology.npz',**arrays);(E/'ordered-native-artist-topology.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'components':sizes,'artistLoops':report['artistBoundaryLoops'],'nativeUpperMiddleL':[V[list(s['edge'])].mean(0).tolist() for s in report['nativeStrips']['L'][int(np.argmax(V[rings['L']['nativeRows'][0],2]))]]}))
