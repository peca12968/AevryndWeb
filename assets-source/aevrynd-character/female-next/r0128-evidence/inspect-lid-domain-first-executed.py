"""Trace actual native separating rim cycles and closed-socket face domains."""
from pathlib import Path
import numpy as np,json,heapq,datetime
R=Path('D:/Download/Aevrynd');PRE=R/'Evidence/character-female-next/r0127-native-lid-closure';E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def path(adj,start,end,forbidden=set()):
 heap=[(0.,start)];ds={start:0};prev={}
 while heap:
  d,i=heapq.heappop(heap)
  if d!=ds[i]:continue
  if i==end:break
  for j,w in adj[i]:
   if j in forbidden and j!=end:continue
   nd=d+w
   if nd<ds.get(j,np.inf):ds[j]=nd;prev[j]=i;heapq.heappush(heap,(nd,j))
 assert end in ds;out=[end]
 while out[-1]!=start:out.append(prev[out[-1]])
 return out[::-1]
def main():
 data=np.load(PRE/'native-head-topology.npz');P=data['world'];T=data['triangles'];edges=data['edges'];adj=[[] for p in P]
 for i,j in edges:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),w));adj[j].append((int(i),w))
 upper=[4760,5920,6065,6002,5993,5933,5982,5971,5960,6495];lower=[6106,10251,6182,6312,6319,6330,6338,6349,6361,6497];ring=[]
 for u,v in zip(upper,upper[1:]):ring+=path(adj,u,v)[:-1]
 ring.append(upper[-1]);tail=list(reversed(lower))+[upper[0]]
 for v in tail:
  ring+=path(adj,ring[-1],v,set(ring[:-1])-{upper[0]})[1:]
 assert ring[-1]==ring[0];ring=ring[:-1];assert len(set(ring))==len(ring)
 rows={};arrays={};centers=P[T].mean(1);edgeFaces={}
 for fi,f in enumerate(T):
  for x,y in zip(f,np.roll(f,-1)):edgeFaces.setdefault(tuple(sorted([int(x),int(y)])),[]).append(fi)
 for side,sign in [('R',1),('L',-1)]:
  ids=np.array(ring) if sign==1 else np.array([int(np.argmin(np.linalg.norm(P-np.array([-P[i,0],P[i,1],P[i,2]]),axis=1))) for i in ring]);assert len(set(ids))==len(ids);blocked={tuple(sorted([int(x),int(y)])) for x,y in zip(ids,np.roll(ids,-1))};assert all(edge in edgeFaces for edge in blocked);dual=[[] for f in T]
  for edge,faces in edgeFaces.items():
   if edge not in blocked and len(faces)==2:i,j=faces;dual[i].append(j);dual[j].append(i)
  target=np.array([sign*.029,-.091,1.461]);seed=int(np.argmin(np.linalg.norm(centers-target,axis=1)));patch={seed};stack=[seed]
  while stack:
   for j in dual[stack.pop()]:
    if j not in patch:patch.add(j);stack.append(j)
  assert 10<len(patch)<6000,('rim did not separate bounded socket',side,len(patch));faces=np.array(sorted(patch),dtype=np.int32);vertices=np.unique(T[faces]);assert np.all(P[vertices,0]*sign>0);rows[side]={'orderedSourceRimVertexIds':ids,'rimVertices':len(ids),'socketWallSourceTriangles':faces,'socketWallTriangles':len(faces),'wallBounds':[P[vertices].min(0),P[vertices].max(0)],'sourceSeparatingCycleNoGeneratedAperture':True};arrays[side+'_rim']=ids;arrays[side+'_socketFaces']=faces
 np.savez_compressed(E/'actual-native-lid-domains.npz',**arrays);save('actual-native-lid-domains.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualNativeDomains':rows,'scope':'Exact native edge cycles and face dual flood only. Not anatomical/finite/contact acceptance. Compare r127 gray visible triangle ownership before reconstruction.'});print('R128_ACTUAL_NATIVE_SOCKET_DOMAINS_READY',[(k,v['rimVertices'],v['socketWallTriangles']) for k,v in rows.items()],flush=True)
if __name__=='__main__':main()
