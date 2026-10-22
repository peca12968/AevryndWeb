"""Actual physical-seam lock topology and scalp-owned root-to-tip volume field.
No source-V-as-follicle assumption, new free cage, remote root connector or geometry move.
"""
from pathlib import Path
import bpy,numpy as np,json,heapq,datetime,importlib.util,time
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0174-artist-volume-flow'
sp=importlib.util.spec_from_file_location('r174base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def prepare():
 tick=time.time();timing=json.loads((E/'before.json').read_text());assert a.a.sha(Path(timing['source']))==timing['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=timing['source']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin);source=E.parent/'r0173-artist-fibre-surface/actual-artist-mesh-uv-construction.npz';z=np.load(source);V=z['worldVertices'];F=z['triangles'];rounded,first,inv=np.unique(np.round(V,6),axis=0,return_index=True,return_inverse=True);Q=V[first];WF=inv[F];parent=np.arange(len(Q))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for tr in WF:
  p,q,r=map(find,tr)
  if p!=q:parent[q]=p
  if p!=r:parent[r]=p
 labels=np.array([find(i) for i in range(len(Q))]);_,group=np.unique(labels,return_inverse=True);ng=int(group.max()+1);faceGroup=group[WF[:,0]];assert (group[WF]==faceGroup[:,None]).all();line=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz');scalp=line['actualScalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),T[scalp].tolist(),all_triangles=True);gap=np.array([tree.find_nearest(Vector(p))[3] for p in Q]);edges=np.unique(np.sort(np.vstack((WF[:,[0,1]],WF[:,[1,2]],WF[:,[2,0]])),axis=1),axis=0);adj=[[] for _ in Q]
 for p,q in edges:
  length=float(np.linalg.norm(Q[p]-Q[q]));adj[p].append((int(q),length));adj[q].append((int(p),length))
 potential=np.full(len(Q),np.inf);rootOwner=np.full(len(Q),-1,'i4');rows=[];seedIDs=[];seedsByGroup=[]
 for gi in range(ng):
  ids=np.flatnonzero(group==gi);minimum=float(gap[ids].min());near=ids[gap[ids]<=minimum+.001];# Spatial root band only; actual emitted roots are always on true current Skin.
  top=float(Q[near,2].max());seeds=near[Q[near,2]>=top-.005];seedIDs.extend(seeds.tolist());seedsByGroup.append(seeds);queue=[]
  for vi in seeds:potential[vi]=0;rootOwner[vi]=vi;heapq.heappush(queue,(0.,int(vi)))
  while queue:
   d,p=heapq.heappop(queue)
   if d>potential[p]+1e-12:continue
   for q,w in adj[p]:
    nd=d+w
    if nd<potential[q]:potential[q]=nd;rootOwner[q]=rootOwner[p];heapq.heappush(queue,(nd,q))
  tip=int(ids[np.argmax(potential[ids])]);rows.append({'group':gi,'vertices':len(ids),'triangles':int((faceGroup==gi).sum()),'nearestActualScalpGapM':minimum,'rootBandVertices':len(seeds),'rootBandWorldBounds':[Q[seeds].min(0).tolist(),Q[seeds].max(0).tolist()],'sourceMaximumRootToTipGeodesicM':float(potential[tip]),'farthestSourceTipWorld':Q[tip].tolist(),'farthestSourceTipScalpGapM':float(gap[tip])})
 B=Q[WF];e1=B[:,1]-B[:,0];e2=B[:,2]-B[:,0];aa=np.einsum('ij,ij->i',e1,e1);bb=np.einsum('ij,ij->i',e1,e2);cc=np.einsum('ij,ij->i',e2,e2);det=aa*cc-bb*bb;d1=potential[WF[:,1]]-potential[WF[:,0]];d2=potential[WF[:,2]]-potential[WF[:,0]];safe=np.maximum(det,1e-30);grad=((cc*d1-bb*d2)/safe)[:,None]*e1+((aa*d2-bb*d1)/safe)[:,None]*e2;norm=np.linalg.norm(grad,axis=1);grad/=np.maximum(norm[:,None],1e-30);vertexFlow=np.zeros((len(Q),3));area=np.linalg.norm(np.cross(e1,e2),axis=1);valid=(det>1e-22)&(norm>1e-8)
 for j in range(3):np.add.at(vertexFlow,WF[valid,j],grad[valid]*area[valid,None])
 vertexFlow/=np.maximum(np.linalg.norm(vertexFlow,axis=1,keepdims=True),1e-30);roots=line['fixedRootWorld'];kd=KDTree(len(seedIDs))
 for i,vi in enumerate(seedIDs):kd.insert(Vector(Q[vi]),int(vi))
 kd.balance();owners=[];seedDist=[]
 for root in roots:
  p,vi,d=kd.find(Vector(root));owners.append(int(group[vi]));seedDist.append(float(d))
 owners=np.array(owners,'i4');seedDist=np.array(seedDist);maximum=np.array([r['sourceMaximumRootToTipGeodesicM'] for r in rows]);minGap=np.array([r['nearestActualScalpGapM'] for r in rows]);untrusted=(seedDist>.020)|(minGap[owners]>.005)|(maximum[owners]<.03)
 proof={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceEvidence':str(source),'originalPhysicalVertices':len(V),'coincidentSeamWeldedVertices':len(Q),'weldToleranceM':1e-6,'actualGeometryNotMoved':True,'sourcePhysicalLockComponents':ng,'priorRawSplitComponents':470,'rootToTipDirection':'Multi-source geodesic potential from spatial proximal root band on each physically seam-welded artist component, not UV-V or a shared artist target. Reference direction only, not proof of original follicles.','groups':rows,'fixedActualScalpBirthRoots':len(roots),'sourceRootBandDistanceQuantilesM':np.quantile(seedDist,[0,.5,.9,.99,1]).tolist(),'birthRootsOutsideDeclared20mmSourceBandOr5mmSourceScalpOr30mmLengthDomain':int(untrusted.sum()),'untrustedBirthIDs':np.flatnonzero(untrusted).tolist(),'rootDomainQualificationThresholdsFixedBeforeCompletePreview':{'sourceBandMaximumM':.020,'componentScalpGapMaximumM':.005,'componentGeodesicMinimumM':.030},'noRootExclusionOrRemoteConnector':True,'seconds':time.time()-tick};save('actual-welded-artist-flow-domain.json',proof)
 np.savez_compressed(E/'actual-artist-flow-domain.npz',worldVertices=Q.astype('f4'),triangles=WF.astype('i4'),sourceTriangleGroup=faceGroup.astype('i4'),vertexGroup=group.astype('i4'),vertexFlow=vertexFlow.astype('f4'),geodesicPotential=potential.astype('f4'),vertexScalpGap=gap.astype('f4'),rootBandVertices=np.array(seedIDs,'i4'),fixedBirthSourceGroup=owners,fixedBirthSourceBandDistance=seedDist.astype('f4'),actualScalpFaces=scalp,fixedRootTriangles=line['fixedRootTriangles'],fixedRootBarycentric=line['fixedRootBarycentric'],fixedRootWorld=roots)
 print('R174_ACTUAL_PHYSICAL_LOCK_FLOW_DOMAIN_DONE',ng,int(untrusted.sum()),np.quantile(seedDist,[0,.5,.9,1]).tolist(),time.time()-tick,flush=True)
if __name__=='__main__':prepare()
