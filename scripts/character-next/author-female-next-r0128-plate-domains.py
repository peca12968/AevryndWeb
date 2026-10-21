"""Direct native outer tarsal footprint from explicit source crease/rim paths."""
from pathlib import Path
import numpy as np,json,importlib.util,datetime
sp=importlib.util.spec_from_file_location('r128domain',Path(__file__).with_name('inspect-female-next-r0128-lid-domains.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);E=a.E;PRE=a.PRE
def main():
 data=np.load(PRE/'native-head-topology.npz');P=data['world'];T=data['triangles'];adj=[[] for p in P]
 for i,j in data['edges']:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),w));adj[j].append((int(i),w))
 upper=[4760,5920,6065,6002,5993,5933,5982,5971,5960,6495];crease=[5327,2218,6653,8246,2934,6915];ring=[upper[0]]
 for v in upper[1:]+crease+[upper[0]]:ring+=a.path(adj,ring[-1],v,set(ring[:-1]))[1:]
 assert ring[-1]==ring[0];ring=ring[:-1];assert len(set(ring))==len(ring);edgeFaces={}
 for fi,f in enumerate(T):
  for x,y in zip(f,np.roll(f,-1)):edgeFaces.setdefault(tuple(sorted([int(x),int(y)])),[]).append(fi)
 socket=np.load(E/'actual-native-lid-domains.npz');centers=P[T].mean(1);arrays={};rows={}
 for side,sign in [('R',1),('L',-1)]:
  ids=np.array(ring) if sign==1 else np.array([int(np.argmin(np.linalg.norm(P-np.array([-P[i,0],P[i,1],P[i,2]]),axis=1))) for i in ring]);blocked={tuple(sorted([int(x),int(y)])) for x,y in zip(ids,np.roll(ids,-1))};assert all(edge in edgeFaces for edge in blocked);dual=[[] for f in T]
  for edge,faces in edgeFaces.items():
   if edge not in blocked and len(faces)==2:i,j=faces;dual[i].append(j);dual[j].append(i)
  target=np.array([sign*.029,-.123,1.469]);seed=int(np.argmin(np.linalg.norm(centers-target,axis=1)));patch={seed};stack=[seed]
  while stack:
   for j in dual[stack.pop()]:
    if j not in patch:patch.add(j);stack.append(j)
  assert 10<len(patch)<6000;assert not patch.intersection(socket[side+'_socketFaces']);faces=np.array(sorted(patch),dtype=np.int32);arrays[side+'_plateFaces']=faces;arrays[side+'_plateBoundary']=ids;rows[side]={'nativeOuterPlateFaces':len(faces),'nativeBoundaryVertices':len(ids),'sourceOuterCreaseLandmarks':crease,'sourceLowerEdgeLandmarks':upper,'nativePlateFaces':faces,'outerPlateAndClosedSocketDomainsDisjoint':True}
 np.savez_compressed(E/'authored-native-plate-domains.npz',**arrays);a.save('authored-native-plate-domains.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct source-native outer tarsal footprint, separate from closed socket and upper mobile skin. Next author finite solid plate and skin seam articulation, not a scalar old rim-weight change.','sides':rows,'approximateSolidPlateThicknessM':.0005,'notMeasuredSubjectSpecificBiologicalThickness':True});print('R128_NATIVE_PLATE_DOMAINS_AUTHORED',[(k,v['nativeOuterPlateFaces']) for k,v in rows.items()],flush=True)
if __name__=='__main__':main()
