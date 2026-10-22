"""Intrinsic paths from CURRENT artist mesh topology, not a foreign-head map.
Native per-vertex UVs are exact at all source corners; each cut follows actual
triangle adjacency, retains bends and is resampled by spatial arc length.
"""
from pathlib import Path
import numpy as np,json,datetime,collections,time
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0165-native-hair-construction';tick=time.time();z=np.load(E/'actual-original-hair-geometry.npz');P=z['positions'];T=z['triangles'];U=z['uvPerVertex'];component=z['components'];assert np.max(np.linalg.norm(z['loopUV']-U[z['loopVertex']],axis=1))==0
(E/'direct-intrinsic-native-path-authoring-start.json').write_bytes((json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T20:17:14+00:00','changedFailedPremise':'Source current-head artist mesh geometry itself supplies spatial paths. Triangle-adjacency isolines replace whole-head numerical guide cages and hard neighbour/foreign-head UV rest fits. UV is only an intrinsic coordinate on the SAME actual hair mesh, no surface/head transplant. Native roots will bind separately to actual current scalp.','fixedCutsPerNativeComponent':32,'stations':49,'oneGeometryMethodNoDensityOrShapeSweep':True,'AOpticalCandidateRejectedKept':True},indent=2)+'\n').encode())
paths=[];lineage=[];reports=[]
for ci in range(int(component.max())+1):
 ids=np.flatnonzero(component==ci);tri=T[component[T[:,0]]==ci];assert np.all(component[tri]==ci);uv=U[tri];dUV=uv[:,1:]-uv[:,0,None];dP=P[tri[:,1:]]-P[tri[:,0,None]];det=np.linalg.det(dUV);valid=abs(det)>1e-14
 if not valid.any():reports.append({'component':ci,'failure':'No invertible source UV triangle','paths':0});continue
 jac=np.linalg.solve(dUV[valid],dP[valid]);scale=np.median(np.linalg.norm(jac,axis=2),axis=0);axis=0 if scale[1]>=scale[0] else 1;low=float(U[ids,axis].min());high=float(U[ids,axis].max());count=0;branch=0;closed=0
 for cut in low+(high-low)*(np.arange(32)+.5)/32:
  graph=collections.defaultdict(list);locations={};coordinate={}
  for face in tri:
   scalar=U[face,axis];cross=[]
   for i,j in [(0,1),(1,2),(2,0)]:
    if (scalar[i]<cut)!=(scalar[j]<cut):
     a,b=int(face[i]),int(face[j]);t=(cut-scalar[i])/(scalar[j]-scalar[i]);key=tuple(sorted((a,b)));locations[key]=P[a]*(1-t)+P[b]*t;coordinate[key]=U[a,1-axis]*(1-t)+U[b,1-axis]*t;cross.append(key)
   if len(cross)==2 and cross[0]!=cross[1]:graph[cross[0]].append(cross[1]);graph[cross[1]].append(cross[0])
  remaining=set(graph)
  while remaining:
   seed=next(iter(remaining));domain={seed};queue=[seed]
   while queue:
    node=queue.pop()
    for nb in graph[node]:
     if nb not in domain:domain.add(nb);queue.append(nb)
   remaining.difference_update(domain)
   if any(len(graph[x])>2 for x in domain):branch+=1;continue
   ends=[x for x in domain if len(graph[x])==1];start=ends[0] if ends else seed;chain=[start];prev=None;node=start
   while True:
    options=[x for x in graph[node] if x!=prev]
    if not options:break
    nxt=options[0]
    if nxt==start:break
    chain.append(nxt);prev,node=node,nxt
   chains=[chain]
   if not ends and len(chain)>2:
    closed+=1;param=np.array([coordinate[x] for x in chain]);i=int(np.argmin(param));j=int(np.argmax(param));chain=chain[i:]+chain[:i];j=(j-i)%len(chain);chains=[chain[:j+1],[chain[0]]+list(reversed(chain[j:]))]
   for points in chains:
    Q=np.array([locations[x] for x in points]);arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))]
    if len(Q)<2 or arc[-1]<.008:continue
    at=np.linspace(0,arc[-1],49);resampled=np.stack([np.interp(at,arc,Q[:,k]) for k in range(3)],axis=1);paths.append(resampled);lineage.append([ci,axis,float(cut),float(arc[-1])]);count+=1
 reports.append({'component':ci,'paths':count,'heldNativeCoordinateAxis':axis,'medianWorldDerivativeScales':scale.tolist(),'ambiguousAdjacencyDomainsNotInvented':branch,'closedSurfaceLoopsSplitIntoActualLongitudinalArcs':closed})
paths=np.array(paths,'f4');assert len(paths)>1000 and np.isfinite(paths).all();np.savez_compressed(E/'authored-intrinsic-native-hair-paths.npz',paths=paths,lineage=np.array(lineage));(E/'actual-intrinsic-source-path-construction.json').write_bytes((json.dumps({'sourceComponents':int(component.max())+1,'nativePaths':len(paths),'points':int(paths.shape[0]*paths.shape[1]),'stations':49,'sourceCornerUVExactlySingleValued':True,'actualTriangleAdjacencyUsed':True,'noForeignGroomMapOrWholeHeadGuideField':True,'allSourceComponentReports':reports,'shortSourceFragmentsBelow8mmNotRepresentedAsLongStrands':'Authoring limitation, not a collision-based deletion or passed coverage claim. Complete hairstyle must be judged; all constructed strands remain included in checks.','newScalpRootsNotYetEstablished':True,'seconds':time.time()-tick},indent=2)+'\n').encode());print('R165_ACTUAL_INTRINSIC_CURRENT_HAIR_PATHS_AUTHORED',paths.shape,time.time()-tick,flush=True)
