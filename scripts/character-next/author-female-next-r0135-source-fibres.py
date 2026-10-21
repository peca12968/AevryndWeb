"""Native source-surface fibre reconstruction by texture-U isocontours.
Triangle/edge connectivity separates overlapping atlas copies. Endpoints and
closed surface contours are mesostructure, not biological follicle claims.
"""
from pathlib import Path
import numpy as np,json,time,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0135-source-shape-fibres';OLD=E.parent/'r0130-artist-native-groom';PITCH=.00018
def main():
 tick=time.time();assert not (E/'source-fibre-lineage.npz').exists();(E/'direct-source-fibre-authoring-start.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Replace coarse source sheets with native surface-following finite fibres; actual source shape and topological UV flow, not a foreign groom or material-only change.'},indent=2)+'\n',encoding='utf-8');d=np.load(OLD/'current-hair-native-triangle-charts.npz');V=d['world'].astype('f8');T=d['triangles'];UV=d['triangleUV'].astype('f8');labels=d['componentLabels'];flat=np.c_[T.ravel(),UV.reshape(-1,2)];keys,inverse=np.unique(flat,axis=0,return_inverse=True);VT=inverse.reshape(-1,3);original=keys[:,0].astype('i4');vUV=keys[:,1:];counts=[];points=[];weights=[];pointUV=[];closed=[];curveComponents=[];rows=[];zeroSegments=0;branchNodes=0;allSegments=0;unrepresented=[]
 for ci,c in enumerate(np.unique(labels)):
  fs=np.flatnonzero(labels[T[:,0]]==c);F=VT[fs];u=vUV[F,0];e1=V[T[fs,1]]-V[T[fs,0]];e2=V[T[fs,2]]-V[T[fs,0]];d1=UV[fs,1]-UV[fs,0];d2=UV[fs,2]-UV[fs,0];det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];good=abs(det)>1e-10;span=float(np.ptp(u));assert span>0
  physicalScale=float(np.median(np.linalg.norm((e1[good]*d2[good,1,None]-e2[good]*d1[good,1,None])/det[good,None],axis=1))) if good.any() else float(np.linalg.norm(np.ptp(V[T[fs].ravel()],axis=0))/span);levels=max(1,int(np.ceil(physicalScale*span/PITCH)));minimum=float(u.min());beforeCurves=len(counts);componentSegments=0
  for level in minimum+span*(np.arange(levels)+.5)/levels:
   below=u<level;take=np.flatnonzero((below.any(1))&(~below.all(1)));nodes={};nodePairs=[];nodeT=[];nodeUV=[];segments=[]
   def node(va,vb):
    if va>vb:va,vb=vb,va
    t=float((level-vUV[va,0])/(vUV[vb,0]-vUV[va,0]));assert -1e-10<=t<=1+1e-10
    if t==0:key=('v',int(va));vb=va;t=0.
    elif t==1:key=('v',int(vb));va=vb;t=0.
    else:key=('e',int(va),int(vb))
    if key not in nodes:nodes[key]=len(nodePairs);nodePairs.append([int(original[va]),int(original[vb])]);nodeT.append(t);nodeUV.append((1-t)*vUV[va]+t*vUV[vb])
    return nodes[key]
   for k in take:
    f=F[k];cut=[]
    for j,h in [(0,1),(1,2),(2,0)]:
     if below[k,j]!=below[k,h]:cut.append(node(int(f[j]),int(f[h])))
    assert len(cut)==2
    if cut[0]!=cut[1]:segments.append(cut)
    else:zeroSegments+=1
   if not segments:continue
   adj=[[] for _ in nodePairs]
   for i,(j,k) in enumerate(segments):adj[j].append(i);adj[k].append(i)
   branchNodes+=sum(len(x)>2 for x in adj);visited=np.zeros(len(segments),bool)
   def trace(start,edge):
    path=[start];at=start
    while True:
     assert not visited[edge];visited[edge]=True;j,k=segments[edge];nxt=k if j==at else j;path.append(nxt)
     if nxt==start or len(adj[nxt])!=2:break
     options=[e for e in adj[nxt] if not visited[e]]
     if not options:break
     at=nxt;edge=options[0]
    counts.append(len(path));closed.append(path[-1]==path[0]);curveComponents.append(int(c))
    for p in path:points.append(nodePairs[p]);weights.append(nodeT[p]);pointUV.append(nodeUV[p])
   for j,edges in enumerate(adj):
    if len(edges)!=2:
     for edge in edges:
      if not visited[edge]:trace(j,edge)
   for edge in range(len(segments)):
    if not visited[edge]:trace(segments[edge][0],edge)
   assert visited.all();allSegments+=len(segments);componentSegments+=len(segments)
  if len(counts)==beforeCurves:unrepresented.append(int(c))
  rows.append({'sourceComponent':int(c),'sourceTriangles':len(fs),'isolineLevels':levels,'curves':len(counts)-beforeCurves,'segments':componentSegments,'estimatedTransverseWidthM':physicalScale*span})
  if ci%50==0:print('R135_SOURCE_COMPONENT_FIBRES',ci,len(counts),len(points),flush=True)
 counts=np.array(counts,'i4');points=np.array(points,'i4');weights=np.array(weights,'f4');pointUV=np.array(pointUV,'f4');assert len(points)==counts.sum() and counts.min()>=2 and not unrepresented;assert np.isfinite(weights).all();np.savez_compressed(E/'source-fibre-lineage.npz',counts=counts,sourceEdgeVertices=points,sourceEdgeWeight=weights,sourceUV=pointUV,closedSurfaceContours=np.array(closed,bool),curveSourceComponent=np.array(curveComponents,'i4'))
 summary={'sourceNativeMeshData':str(OLD/'current-hair-native-triangle-charts.npz'),'sourceComponents':len(rows),'sourceTriangles':len(T),'originalNativeVertices':len(V),'seamAwareVirtualVertices':len(keys),'allSourceComponentsRepresented':True,'componentRows':rows,'isolineLevels':sum(r['isolineLevels'] for r in rows),'curves':len(counts),'points':len(points),'sourceNativeContourSegments':allSegments,'surfaceContourLoops':int(sum(closed)),'sourceNonmanifoldBranchNodesSplitNotDiscarded':branchNodes,'zeroLengthTouchIntersectionsNotCurves':zeroSegments,'minimumCurveKnots':int(counts.min()),'maximumCurveKnots':int(counts.max()),'initialPitchEngineeringM':PITCH,'allFiniteSourceMeshEdgeWeightsRange':[float(weights.min()),float(weights.max())],'scope':'All native edge-isocontour segments retained, branch paths split. Every point references exact source Hair edge and interpolated original UV. Not complete source surface-area/render-occupancy equivalence, follicle directions or natural/finite/dynamic/runtime proof.','seconds':time.time()-tick}
 (E/'source-fibre-authoring.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print('R135_ORIGINAL_SHAPE_SOURCE_FIBRES_AUTHORED',len(counts),len(points),time.time()-tick,flush=True)
if __name__=='__main__':main()
