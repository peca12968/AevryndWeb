"""Author finite original quad-strip paths; no tangent integration, shared XYZ or tuck field."""
from pathlib import Path
import numpy as np,json,collections,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0118-native-bob-construction';z=np.load(E/'native-bob-source-lineage.npz');W=z['actualNativeWorld'];UV=z['sourceUV'];F=z['sourceFaces'];FU=z['sourceFaceUV'];edgeFaces=collections.defaultdict(list)
for fi,f in enumerate(FU):
 for k in range(4):edgeFaces[tuple(sorted((int(f[k]),int(f[(k+1)%4]))))].append((fi,k))
assert max(map(len,edgeFaces.values()))<=2
paths=[];seen=set()
for edge,neighbors in edgeFaces.items():
 if len(neighbors)!=1:continue
 fi,k=neighbors[0];faces=[];pairs=[];used=set();enter=(int(FU[fi,k]),int(FU[fi,(k+1)%4]));worldpair=(int(F[fi,k]),int(F[fi,(k+1)%4]));pairs.append(worldpair);uvpairs=[enter]
 while fi not in used:
  used.add(fi);faces.append(fi);f=FU[fi];same=(int(f[k]),int(f[(k+1)%4]))==enter;out=(int(f[(k+3)%4]),int(f[(k+2)%4]));wp=(int(F[fi,(k+3)%4]),int(F[fi,(k+2)%4]))
  if not same:out=out[::-1];wp=wp[::-1]
  pairs.append(wp);uvpairs.append(out);nxt=[x for x in edgeFaces[tuple(sorted(out))] if x[0]!=fi]
  if not nxt:break
  fi,k=nxt[0];enter=out
 key=tuple(sorted(faces))
 if key in seen:continue
 seen.add(key);p=W[np.array(pairs)].mean(1);uv=UV[np.array(uvpairs)].mean(1);length=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum());duv=np.abs(np.diff(uv,axis=0)).sum(0);width=float(np.linalg.norm(W[np.array(pairs)[:,1]]-W[np.array(pairs)[:,0]],axis=1).mean())
 paths.append({'faces':faces,'pairs':pairs,'uvPairs':uvpairs,'length':length,'width':width,'UVArc':duv.tolist(),'dominantV':bool(duv[1]>=duv[0])})
# Every original source face must contribute to an authored longitudinal path.
# Select the existing topological V family, then include the longer original
# boundary-to-boundary strip for any uncovered source face. No generated paths.
chosen={i for i,p in enumerate(paths) if p['dominantV']};covered={f for i in chosen for f in paths[i]['faces']};missing=sorted(set(range(len(F)))-covered);added=[]
for fi in missing:
 if fi in covered:continue
 candidates=[i for i,p in enumerate(paths) if fi in p['faces']];i=max(candidates,key=lambda i:paths[i]['length']);chosen.add(i);covered.update(paths[i]['faces']);added.append(i)
assert len(covered)==len(F)
flat=[];counts=[];uvflat=[];records=[]
for i in sorted(chosen):
 p=paths[i];a=np.array(p['pairs']);u=np.array(p['uvPairs']);mid=W[a].mean(1)
 if mid[0,2]<mid[-1,2]:a=a[::-1];u=u[::-1]
 flat.extend(a);uvflat.extend(u);counts.append(len(a));records.append({'sourceStripID':i,**p,'rootAtHigherOriginalEndpoint':True})
np.savez_compressed(E/'native-bob-authored-strip-paths.npz',edgeVertexPairs=np.array(flat,dtype='i4'),edgeUVPairs=np.array(uvflat,dtype='i4'),pathEdgeCounts=np.array(counts,dtype='i4'),actualSourceWorld=W)
(E/'native-bob-authored-strip-paths.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'allOriginal4237FacesCovered':len(covered),'allBoundaryToBoundaryQuadStrips':len(paths),'chosenOriginalLongitudinalStrips':len(chosen),'coverageCompletionStrips':added,'construction':'Exact original opposite-edge quad-strip topology in29 native UV charts, original dominant-V hair-flow family. Not scalp U/V advection or integration, not r97 shared XYZ ear tuck. Geometric source roots are reference endpoints, not proven biological follicles.','paths':records},indent=2)+'\n',encoding='utf-8')
print('R118_ORIGINAL_QUAD_STRIP_PATHS_AUTHORED',len(paths),len(chosen),'coverage',len(covered),'completion',len(added),'lengths',np.quantile([paths[i]['length'] for i in chosen],[0,.5,1]).tolist(),flush=True)
