"""Direct native-edge scalp boundaries, paired semantic arcs, intrinsic charts.
No target nearest-root fitting, height-cut cap or global pole registration.
"""
from pathlib import Path
import numpy as np,json,datetime,time,heapq
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0133-anatomical-scalp-chart';OLD=E.parent/'r0092-native-compatible-groom'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
def path(adj,start,end,forbidden):
 heap=[(0.,start)];ds={start:0.};prev={}
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
def chart(P,T,picks,label):
 edges=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0);adj=[[] for _ in P]
 for i,j in edges:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),w));adj[j].append((int(i),w))
 anchors=[int(np.linalg.norm(P-np.array(p),axis=1).argmin()) for p in picks];assert len(set(anchors))==len(anchors);ring=[anchors[0]];sectors=[]
 for v in anchors[1:]+anchors[:1]:
  part=path(adj,ring[-1],v,set(ring[:-1]));sectors.append(part);ring+=part[1:]
 assert ring[-1]==ring[0];ring=ring[:-1];assert len(set(ring))==len(ring)
 blocked={tuple(sorted([int(x),int(y)])) for x,y in zip(ring,np.roll(ring,-1))};ef={}
 for fi,f in enumerate(T):
  for i,j in zip(f,np.roll(f,-1)):ef.setdefault(tuple(sorted([int(i),int(j)])),[]).append(fi)
 dual=[[] for _ in T]
 for ed,fs in ef.items():
  if ed not in blocked and len(fs)==2:i,j=fs;dual[i].append(j);dual[j].append(i)
 seed=int(P[T].mean(1)[:,2].argmax());patch={seed};stack=[seed]
 while stack:
  for j in dual[stack.pop()]:
   if j not in patch:patch.add(j);stack.append(j)
 faces=np.array(sorted(patch),'i4');assert 300<len(faces)<12000,(label,len(faces));used,inv=np.unique(T[faces],return_inverse=True);F=inv.reshape(-1,3);V=P[used];index={int(v):i for i,v in enumerate(used)};ringLocal=np.array([index[int(v)] for v in ring]);allEdges=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1);ed,ec=np.unique(allEdges,axis=0,return_counts=True);assert len(V)-len(ed)+len(F)==1,(label,'not disk');assert set(map(tuple,ed[ec==1]))=={tuple(sorted([index[int(x)],index[int(y)]])) for x,y in zip(ring,np.roll(ring,-1))},(label,'extra boundary');assert ec.max()==2
 uv=np.zeros((len(V),2));sectorRows=[]
 for k,part in enumerate(sectors):
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P[part],axis=0),axis=1))];angle=2*np.pi*(k+arc/arc[-1])/len(sectors);ids=np.array([index[int(x)] for x in part]);uv[ids]=np.c_[np.sin(angle),-np.cos(angle)];sectorRows.append({'semanticSector':k,'nativeVertices':part,'arcLength':float(arc[-1])})
 boundary=np.zeros(len(V),bool);boundary[ringLocal]=True;interior=np.flatnonzero(~boundary);ii=np.full(len(V),-1,'i4');ii[interior]=np.arange(len(interior));e=np.concatenate([ed,ed[:,::-1]]);deg=np.bincount(e[:,0],minlength=len(V));take=~boundary[e[:,0]];ei=e[take];known=boundary[ei[:,1]];rhs=np.column_stack([np.bincount(ii[ei[known,0]],weights=uv[ei[known,1],j],minlength=len(interior)) for j in [0,1]]);inside=ei[~known];row=ii[inside[:,0]];col=ii[inside[:,1]];diag=deg[interior]
 def apply(x):return diag*x-np.bincount(row,weights=x[col],minlength=len(interior))
 iterations=[]
 for j in [0,1]:
  x=np.zeros(len(interior));r=rhs[:,j].copy();z=r/diag;p=z.copy();rz=r@z
  for it in range(5000):
   Ap=apply(p);alpha=rz/(p@Ap);x+=alpha*p;r-=alpha*Ap
   if np.linalg.norm(r)<1e-10:break
   z=r/diag;new=r@z;p=z+(new/rz)*p;rz=new
  assert np.linalg.norm(r)<1e-8,(label,'chart solve',np.linalg.norm(r));uv[interior,j]=x;iterations.append(it+1)
 a=uv[F[:,1]]-uv[F[:,0]];b=uv[F[:,2]]-uv[F[:,0]];signed=a[:,0]*b[:,1]-a[:,1]*b[:,0];assert signed.min()>1e-12 or signed.max()<-1e-12,(label,'folded/degenerate chart',float(signed.min()),float(signed.max()))
 result={'nativeVertexIds':used,'nativeFaceIds':faces,'triangles':F,'world':V,'uv':uv,'nativeBoundaryVertexIds':np.array(ring),'nativeAnchorVertexIds':np.array(anchors)};np.savez_compressed(E/(label+'-scalp-chart.npz'),**result);save(label+'-scalp-chart.json',{'pickedNativeAnatomicalBoundaryLandmarks':picks,'nativeAnchorVertexIds':anchors,'orderedNativeBoundaryVertexIds':ring,'semanticBoundaryArcs':sectorRows,'vertices':len(V),'triangles':len(F),'eulerCharacteristic':1,'boundaryCycles':1,'harmonicSolveIterations':iterations,'uvSignedDoubleAreaRange':[float(signed.min()),float(signed.max())],'allChartFacesSameOrientationNondegenerate':True,'scope':'Actual source-native surface disk with paired semantic boundary arcs, not generic spatial target projection or contact/appearance proof.'});print('R133_AUTHORED_NATIVE_SCALP_CHART',label,len(V),len(F),iterations,flush=True)
def main():
 tick=time.time();save('direct-scalp-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Author actual native source/current-head scalp boundary cycles and continuous semantic harmonic chart correspondence. Original start/deadlines retained.','previousGoalTurnClassification':'progress: actual complete r132 source authored/rejected and independently recovered; live free-path edits, but no head coupling/complete gain.'});source=np.load(OLD/'native-Eve-source.npz');canonical=np.load(E.parent/'r0057-coherent-foundation/canonical-mesh-data.npz');T=source['triangles'];mi=np.repeat(canonical['materials'],source['sourceFaceCounts']-2);ids=np.flatnonzero(np.isin(mi,[4,5]));right=[[0,-.061,1.690],[.04,-.052,1.680],[.07,-.015,1.650],[.081,.025,1.630],[.07,.09,1.600],[.04,.12,1.575],[0,.10,1.568]];chart(source['bodyNative'],T[ids],right+[[-x,y,z] for x,y,z in right[-2:0:-1]],'source');src=np.load(E/'source-scalp-chart.npz');np.savez_compressed(E/'source-original-face-map.npz',originalTriangles=ids[src['nativeFaceIds']]);target=np.load(E.parent/'r0127-native-lid-closure/native-head-topology.npz');right=[[0,-.112,1.525],[.038,-.100,1.520],[.068,-.053,1.502],[.078,-.005,1.490],[.072,.028,1.466],[.045,.052,1.440],[0,.055,1.437]];chart(target['world'],target['triangles'],right+[[-x,y,z] for x,y,z in right[-2:0:-1]],'target');print('R133_PAIRED_NATIVE_SCALP_CHARTS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
