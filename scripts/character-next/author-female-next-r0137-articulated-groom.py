"""Author native source pony rest pose coherently across main mesh and all fibres."""
from pathlib import Path
import numpy as np,json,datetime,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0137-complete-studio-groom'
def main():
 tick=time.time();assert not (E/'articulated-complete-groom.npz').exists();(E/'direct-articulated-authoring-start.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Coherent joint rest-pose authoring of complete original pony core and all source pony fibre paths; original front/back/loose and complete head/body gains protected.','originalStartedUTC':'2026-10-21T20:43:00+00:00','allOriginalTimingAndSupportFailuresPreserved':True},indent=2)+'\n');d=np.load(E/'original-long-source.npz');V=d['coreWorld'];F=d['coreTriangles'];par=np.arange(len(V));size=np.ones(len(V),'i4')
 def root(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for f in F:
  a=root(f[0])
  for b in f[1:]:
   b=root(b)
   if a!=b:
    if size[a]<size[b]:a,b=b,a
    par[b]=a;size[a]+=size[b]
 labels=np.array([root(i) for i in range(len(V))]);ids=np.unique(labels);rows=[{'component':int(i),'vertices':int((labels==i).sum()),'bounds':[V[labels==i].min(0).tolist(),V[labels==i].max(0).tolist()]} for i in ids];qualification=json.loads((E/'original-long-source-qualification.json').read_text('utf-8'));region=np.concatenate([np.full(s['parents']+s['children'],j,'i4') for j,s in enumerate(qualification['systems'])]);counts=d['fibreCounts'];assert len(region)==len(counts);P=d['fibreLocal'];starts=np.r_[0,np.cumsum(counts)[:-1]];ponyCurves=region==2;roots=P[starts[ponyCurves]];joint=np.median(roots,axis=0);ponyEnd=P[(starts+counts-1)[ponyCurves]];direction=np.median(ponyEnd,axis=0)-joint;direction/=np.linalg.norm(direction);wanted=np.array([-.12,.42,-.90]);wanted/=np.linalg.norm(wanted);axis=np.cross(direction,wanted);axis/=np.linalg.norm(axis);angle=np.arccos(np.clip(direction@wanted,-1,1));K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);Q=np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K)
 # Components are the artist's actual disconnected clump volumes. A component
 # with a real tip extending beyond the native pony tie is selected whole; no
 # strand/face is removed, no deformation is chosen by contact-test outcome.
 along=(V-joint)@direction;ponyComponents=[int(i) for i in ids if np.max(along[labels==i])>.13];selected=np.isin(labels,ponyComponents)
 if selected.sum()==len(V):
  raise RuntimeError('Core is one connected whole; cannot claim a separately articulated pony without source skin weights')
 assert selected.any();edited=V.copy();edited[selected]=(V[selected]-joint)@Q.T+joint;pp=P.copy();pointMask=np.repeat(ponyCurves,counts);pp[pointMask]=(P[pointMask]-joint)@Q.T+joint
 np.savez_compressed(E/'articulated-complete-groom.npz',coreSource=V,corePosed=edited,coreTriangles=F,corePonyMask=selected,originalFibreLocal=P,posedFibreLocal=pp,fibreCounts=counts,fibreRegions=region,ponyJoint=joint,ponyRotation=Q,sourceHeadWorld=d['headWorld'],sourceHeadTriangles=d['headTriangles'])
 (E/'articulated-source-authoring.json').write_text(json.dumps({'source':'original-long-source.npz','sourceOriginalCompleteNativeComponents':rows,'selectedWholePonyComponentIds':ponyComponents,'selectedCoreVertices':int(selected.sum()),'allCoreVertices':len(V),'ponyCurves':int(ponyCurves.sum()),'allCurves':len(counts),'ponyJointSource':joint.tolist(),'originalPonyDirection':direction.tolist(),'authoredGravityRestDirection':wanted.tolist(),'rotationRadians':float(angle),'rotationMatrix':Q.tolist(),'allOriginalCoreTrianglesAndAllNativeFibresPreserved':True,'nonPonyCoreExact':bool(np.array_equal(edited[~selected],V[~selected])),'nonPonyFibresExact':bool(np.array_equal(pp[~pointMask],P[~pointMask])),'finitePhysicalMotionNotClaimed':'One static authored rigid joint rest pose, not a gravity solver or native original rigidity/finite contacts proof.','seconds':time.time()-tick},indent=2)+'\n');print('R137_ACTUAL_NATIVE_VOLUME_PONY_REST_AUTHORING_DONE',int(selected.sum()),len(V),time.time()-tick,flush=True)
if __name__=='__main__':main()
