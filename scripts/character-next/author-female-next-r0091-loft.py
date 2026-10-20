"""Explicit distributed end patches and section-loft coordinates for Rain clumps.
No UV is read and no tangent-field advection or point sink is used. This is an
artist-shape reconstruction hypothesis, not a follicle or contact certificate.
Run in the bundled numerical Python, not a new installed modelling application.
"""
from pathlib import Path
import numpy as np, heapq, json, time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections'
N=64;COUNT=21908
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-20)
def distances(P,edges,seeds):
 adj=[[] for _ in P]
 for a,b in edges:
  w=float(np.linalg.norm(P[a]-P[b]));adj[a].append((int(b),w));adj[b].append((int(a),w))
 D=np.full(len(P),np.inf);heap=[]
 for i in seeds:D[i]=0.;heapq.heappush(heap,(0.,int(i)))
 while heap:
  d,a=heapq.heappop(heap)
  if d>D[a]:continue
  for b,w in adj[a]:
   z=d+w
   if z<D[b]:D[b]=z;heapq.heappush(heap,(z,b))
 return D
def profile(P,T,edges,rootHint,tipHint,label):
 tipSeed=int(np.linalg.norm(P-tipHint,axis=1).argmin());dt=distances(P,edges,[tipSeed])
 rootSeed=int(np.argmax(dt)) if rootHint is None else int(np.linalg.norm(P-rootHint,axis=1).argmin())
 dr=distances(P,edges,[rootSeed]);root=np.flatnonzero(dr<=np.quantile(dr,.06));tip=np.flatnonzero(dt<=np.quantile(dt,.06));assert not np.intersect1d(root,tip).size
 dr=distances(P,edges,root);dt=distances(P,edges,tip);scalar=dr/np.maximum(dr+dt,1e-20)
 stations=np.linspace(.025,.975,48);cuts=[];counts=[]
 # A global section field with two finite patches, rather than integrating a local shading direction.
 for t in stations:
  a=scalar[edges[:,0]];b=scalar[edges[:,1]];mask=(a<t)&(b>=t)|(b<t)&(a>=t);ed=edges[mask];a=a[mask];b=b[mask];assert len(ed)>=3,(label,t,len(ed))
  f=(t-a)/(b-a);C=P[ed[:,0]]*(1-f[:,None])+P[ed[:,1]]*f[:,None];cuts.append(C);counts.append(len(C))
 centres=np.array([x.mean(0) for x in cuts])
 for _ in range(2):centres[1:-1]=.25*centres[:-2]+.5*centres[1:-1]+.25*centres[2:]
 tangent=unit(np.gradient(centres,axis=0));basis=[];prev=None;rings=[];areas=[]
 for i,(C,c,tan) in enumerate(zip(cuts,centres,tangent)):
  if prev is None:
   trial=np.array([1.,0,0]) if abs(tan[0])<.85 else np.array([0.,1.,0]);u=unit(trial-tan*np.dot(trial,tan))
  else:u=unit(prev-tan*np.dot(prev,tan))
  v=unit(np.cross(tan,u));prev=u;Q=C-c;X=Q@u;Y=Q@v;ang=np.arctan2(Y,X);idx=np.argsort(ang);ang=ang[idx];Q=Q[idx];theta=np.linspace(-np.pi,np.pi,64,endpoint=False)
  # Preserve the observed transverse section shape, including its width; no common point exit.
  ring=np.column_stack([np.interp(theta,np.r_[ang[-1]-2*np.pi,ang,ang[0]+2*np.pi],np.r_[Q[-1,j],Q[:,j],Q[0,j]]) for j in range(3)])
  rings.append(ring);basis.append([u,v]);areas.append(.5*abs(float(np.sum(X[idx]*np.roll(Y[idx],-1)-Y[idx]*np.roll(X[idx],-1)))))
 rings=np.array(rings)
 for _ in range(2):rings[1:-1]=.2*rings[:-2]+.6*rings[1:-1]+.2*rings[2:]
 return {'label':label,'centres':centres,'rings':rings,'basis':np.array(basis),'rootIDs':root,'tipIDs':tip,'scalar':scalar,'station':stations,'cutCounts':counts,'areas':areas,'rootSeed':rootSeed,'tipSeed':tipSeed}
def sample(p,theta,radial,u):
 # Constant transverse coordinates through every longitudinal station; no ODE integration.
 theta=np.mod(theta+np.pi,2*np.pi)/(2*np.pi)*64;lo=np.floor(theta).astype(int)%64;hi=(lo+1)%64;blend=theta-np.floor(theta);Q=p['centres'][None,:,:]+radial[:,None,None]*(p['rings'][:,lo,:].transpose(1,0,2)*(1-blend[:,None,None])+p['rings'][:,hi,:].transpose(1,0,2)*blend[:,None,None]);out=np.empty((len(theta),len(u),3))
 for c in range(len(theta)):
  for j in range(3):out[c,:,j]=np.interp(u,np.linspace(0,1,len(p['centres'])),Q[c,:,j])
 return out
def main():
 tick=time.time();data=np.load(E/'authored-clump-topology.npz');band=data['bandCentre'];profiles=[];orphan=[];arrays={};records=[]
 for name in ['AFN90_RAIN_HAIR_MAIN','AFN90_RAIN_HAIR_PONYTAIL','AFN90_RAIN_HAIR_STRAND']:
  P=data[name+'_world'];T=data[name+'_triangles'];edge=data[name+'_edges'];cc=data[name+'_component']
  for ix in np.unique(cc):
   ids=np.flatnonzero(cc==ix);mapping=np.full(len(P),-1);mapping[ids]=np.arange(len(ids));edges=mapping[edge[np.all(cc[edge]==ix,axis=1)]];tris=mapping[T[np.all(cc[T]==ix,axis=1)]];Q=P[ids];label=name+'_'+str(ix)
   if not len(tris):orphan.append({'object':name,'component':int(ix),'originalVertexIDs':ids.tolist(),'reason':'Original isolated vertex without any surface/edge, retained in unchanged hidden source. Not a discarded attempted follicle.'});continue
   sideburn=name.endswith('MAIN') and ix in (1,2,12);tail=name.endswith('PONYTAIL');loose=name.endswith('STRAND')
   rootHint=Q[Q[:,2].argmax()] if sideburn or tail or loose else None;tipHint=Q[Q[:,2].argmin()] if sideburn or tail or loose else band
   p=profile(Q,tris,edges,rootHint,tipHint,label);p['role']='tail' if tail else 'free' if sideburn or loose else 'gather';p['object']=name;p['component']=int(ix);profiles.append(p)
   arrays[label+'_centres']=p['centres'];arrays[label+'_rings']=p['rings'];arrays[label+'_basis']=p['basis'];arrays[label+'_rootNativeIDs']=ids[p['rootIDs']];arrays[label+'_tipNativeIDs']=ids[p['tipIDs']];arrays[label+'_scalar']=p['scalar'];arrays[label+'_sourceIDs']=ids
   records.append({'label':label,'role':p['role'],'sourceVertices':len(ids),'sourceTriangles':len(tris),'rootNativeVertexIDs':ids[p['rootIDs']].tolist(),'tipNativeVertexIDs':ids[p['tipIDs']].tolist(),'sectionEdgeIntersectionCounts':p['cutCounts'],'sectionAreaRangeM2':[min(p['areas']),max(p['areas'])],'rootPatchCentre':Q[p['rootIDs']].mean(0).tolist(),'tipPatchCentre':Q[p['tipIDs']].mean(0).tolist(),'minimumTransverseExtentM':float(np.min(np.linalg.norm(p['rings'],axis=2).max(1))),'allSectionsConstructed':True})
 tail=next(p for p in profiles if p['role']=='tail');roots=[p for p in profiles if p['role']!='tail'];weights=np.array([max(np.linalg.norm(p['rings'][0],axis=1).max(),.002) for p in roots]);counts=np.floor(COUNT*weights/weights.sum()).astype(int);counts[np.argmax(counts)]+=COUNT-int(counts.sum());rng=np.random.default_rng(910091);paths=[];owner=[];rad=[];angle=[]
 for ci,(p,num) in enumerate(zip(roots,counts)):
  theta=rng.uniform(-np.pi,np.pi,num);rho=np.sqrt(rng.uniform(.18,1.,num));u=np.linspace(0,1,40 if p['role']=='gather' else N);P=sample(p,theta,rho,u)
  if p['role']=='gather':
   # Match across a finite tail-root section. Each strand keeps a distinct transverse coordinate.
   tailtheta=np.arctan2((P[:,-1]-tail['centres'][0])@tail['basis'][0,1],(P[:,-1]-tail['centres'][0])@tail['basis'][0,0]);tailP=sample(tail,tailtheta,rho,np.linspace(0,1,38));bridge=P[:,-1,None,:]*(1-np.linspace(0,1,7)[None,:,None])+tailP[:,0,None,:]*np.linspace(0,1,7)[None,:,None];P=np.concatenate((P,bridge[:,1:-1],tailP),axis=1)
  output=np.empty((num,N,3))
  for j,path in enumerate(P):
   length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];end=length[-1]*(.83+.17*rng.random()) if p['role']=='gather' else length[-1]*(.9+.1*rng.random());output[j]=np.column_stack([np.interp(np.linspace(0,end,N),length,path[:,k]) for k in range(3)])
  # Modest strand-scale variation; roots and authored large forms remain controlled.
  t=np.linspace(0,1,N);tan=unit(np.gradient(output,axis=1));normal=unit(np.cross(tan,np.array([0.,0.,1.])));phase=rng.uniform(0,2*np.pi,num);wave=.00035*np.sin(7*np.pi*t[None,:]+phase[:,None])*np.sin(np.pi*t)[None,:]**2;output+=normal*wave[:,:,None]
  assert np.isfinite(output).all();paths.append(output);owner.extend([ci]*num);rad.extend(rho);angle.extend(theta);print('R91_AUTHORED_SECTION_LOFT',p['label'],num,flush=True)
 paths=np.concatenate(paths);assert paths.shape==(COUNT,N,3) and len(owner)==COUNT;np.savez_compressed(E/'section-profiles.npz',**arrays);np.savez_compressed(E/'authored-fibre-lofts.npz',pathsWorld=paths.astype('f4'),owner=np.array(owner,'i4'),transverseRadius=np.array(rad,'f4'),transverseAngle=np.array(angle,'f4'),rootCounts=counts)
 report={'construction':'Global two-distributed-patch graph coordinate, explicit48 cross-sections per connected surface,64 polar samples preserving transverse shape, volume loft and finite-width tail gather. No UV read, tangent advection, sparse-volume claim or shared XYZ free-knot template.','profiles':records,'surfaceComponents':len(profiles),'unchangedSourceOrphanVertices':orphan,'roots':COUNT,'pointsEach':N,'allRequestedRootsConstructed':True,'allRequestedRootsRetained':True,'actualScalpRootAttachmentPending':True,'finiteContactSelfNaturalDynamicsRuntimeAccepted':False,'seconds':time.time()-tick};(E/'section-authoring.json').write_text(json.dumps(report,indent=2)+'\n');print('R91_LOFT_READY',paths.shape,time.time()-tick,flush=True)
if __name__=='__main__':main()
