"""Artist-picked native scalp boundary and actual root-source topology."""
from pathlib import Path
import numpy as np,json,importlib.util,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0129-native-authored-bob';PRE=E.parent/'r0127-native-lid-closure'
sp=importlib.util.spec_from_file_location('r129paths',Path(__file__).with_name('inspect-female-next-r0128-lid-domains.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def main():
 data=np.load(PRE/'native-head-topology.npz');P=data['world'];T=data['triangles'];adj=[[] for p in P]
 for i,j in data['edges']:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),w));adj[j].append((int(i),w))
 right=[[0,-.100,1.548],[.038,-.087,1.535],[.068,-.053,1.502],[.078,-.005,1.490],[.072,.028,1.466],[.045,.052,1.440],[0,.055,1.437]];points=right+[[-x,y,z] for x,y,z in right[-2:0:-1]];anchors=[int(np.argmin(np.linalg.norm(P-q,axis=1))) for q in points];ring=[anchors[0]]
 for v in anchors[1:]+anchors[:1]:ring+=a.path(adj,ring[-1],v,set(ring[:-1]))[1:]
 assert ring[0]==ring[-1];ring=ring[:-1];assert len(set(ring))==len(ring);blocked={tuple(sorted([int(x),int(y)])) for x,y in zip(ring,np.roll(ring,-1))};ef={}
 for fi,f in enumerate(T):
  for i,j in zip(f,np.roll(f,-1)):ef.setdefault(tuple(sorted([int(i),int(j)])),[]).append(fi)
 dual=[[] for f in T]
 for edge,faces in ef.items():
  if edge not in blocked and len(faces)==2:i,j=faces;dual[i].append(j);dual[j].append(i)
 centers=P[T].mean(1);seed=int(np.argmax(centers[:,2]));patch={seed};stack=[seed]
 while stack:
  for j in dual[stack.pop()]:
   if j not in patch:patch.add(j);stack.append(j)
 assert 300<len(patch)<20000;faces=np.array(sorted(patch),dtype=np.int32);verts=np.unique(T[faces]);assert P[verts,2].min()>1.4;areas=np.linalg.norm(np.cross(P[T[faces,1]]-P[T[faces,0]],P[T[faces,2]]-P[T[faces,0]]),axis=1)*.5;np.savez_compressed(E/'authored-native-scalp-domain.npz',nativeScalpFaceIds=faces,nativeBoundaryVertexIds=ring,nativeScalpVertexIds=verts)
 save('native-scalp-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pickedHairlineTempleEarBackNapeLandmarks':points,'actualNativeBoundaryAnchorVertexIds':anchors,'orderedActualBoundaryVertexIds':ring,'actualScalpTriangles':len(faces),'actualScalpAreaM2':areas.sum(),'boundsWorld':[P[verts].min(0),P[verts].max(0)],'source':'Exact current artist-head topology from retained r126/r127 native source inspection, not a foreign emitter fit.','scope':'Authored source scalp domain only, not all-root/shaft/finite contact or whole appearance acceptance.'});print('R129_ACTUAL_NATIVE_SCALP_AUTHORED',len(faces),areas.sum(),flush=True)
if __name__=='__main__':main()
