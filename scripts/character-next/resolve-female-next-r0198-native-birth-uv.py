"""Resolve recorded native guide UVs on the recorded actual source surface.
All overlapping candidates are checked; no nearest first-point ownership.
"""
from pathlib import Path
import numpy as np,json,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0198-native-birth-owned-scalp';d=np.load(E/'native-birth-fields.npz');U=d['bodyUV__UVMap'].astype('f8');V=d['sourceBodyWorld'].astype('f8');T=d['sourceBodyTriangles'];uv=d['raw__surface_uv_coordinate'].astype('f8');childUV=d['evaluated__surface_uv_coordinate'];gi=d['evaluated__guide_curve_index'];A=U[:,0];B=U[:,1]-A;D=U[:,2]-A;den=B[:,0]*D[:,1]-B[:,1]*D[:,0];safe=np.abs(den)>1e-14;owners=[];weights=[];positions=[];issues=[];overlap=[]
for i,p in enumerate(uv):
 X=p-A;b=np.zeros((len(U),3));b[:,1]=np.divide(X[:,0]*D[:,1]-X[:,1]*D[:,0],den,out=np.zeros(len(U)),where=safe);b[:,2]=np.divide(B[:,0]*X[:,1]-B[:,1]*X[:,0],den,out=np.zeros(len(U)),where=safe);b[:,0]=1-b[:,1]-b[:,2];hits=np.flatnonzero(safe&(b.min(1)>-1e-6)&(b.max(1)<1+1e-6))
 if not len(hits):issues.append({'guide':i,'issue':'No actual source-surface UV triangle','uv':p.tolist()});owners.append(-1);weights.append([0,0,0]);positions.append([0,0,0]);continue
 Q=np.einsum('ni,nij->nj',b[hits],V[T[hits]]);spread=float(np.linalg.norm(Q-Q[0],axis=1).max())
 if spread>3e-6:issues.append({'guide':i,'issue':'UV candidates disagree in actual3D','triangles':hits.tolist(),'spreadM':spread})
 if len(hits)>1:overlap.append({'guide':i,'matchingFaces':len(hits),'actual3DSpreadM':spread})
 fi=int(hits[0]);owners.append(fi);weights.append(b[fi]);positions.append(Q[0])
owners=np.array(owners,'i4');weights=np.array(weights);positions=np.array(positions);np.savez_compressed(E/'resolved-guide-births.npz',sourceGuideUV=uv,sourceGuideBirthFaces=owners,sourceGuideBirthBC=weights,sourceGuideBirthWorld=positions,childOriginalGuideIDs=gi)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualSourceRawGuideUVCount':len(uv),'actualFullCurves':len(childUV),'actualFullUniqueUVs':len(np.unique(childUV,axis=0)),'fullUVExactlyIndexedRawGuideUV':bool(np.array_equal(childUV,uv.astype('f4')[gi])),'actualChildUVIsUniqueBirthEvidence':False,'actualRawGuideUVResolutionIssues':issues,'sharedUVBoundaryCandidates':overlap,'resolvedSourceBirthWorldBounds':np.stack([positions.min(0),positions.max(0)]).tolist(),'sourceUVResolutionPassed':not issues,'interpretation':'Complete generation copies252 guide UV values to10191 curves with guide_curve_index. This proves inherited guide affiliation, not10191 independent surface births. Resolve source guide fields on actual source mesh before authoring a new surface-born child construction.','notCurrentAnatomyOrContactAcceptance':True};(E/'native-birth-resolution.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R198_NATIVE_GUIDE_BIRTH_UV_RESOLUTION_DONE',json.dumps(q),flush=True)
