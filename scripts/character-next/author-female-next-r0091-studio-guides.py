"""Use verified original studio particle-proxy guide order, not guessed card rails.
Read source script as data to establish mapping only; execute no studio code.
Actual adult body remains unchanged. Child field uses the actual scalp graph.
"""
from pathlib import Path
import numpy as np,json,time
import heapq
def graph_distances(V,edge,w,seeds):
 adj=[[] for _ in V]
 for (a,b),d in zip(edge,w):adj[a].append((int(b),float(d)));adj[b].append((int(a),float(d)))
 D=np.full((len(seeds),len(V)),np.inf)
 for k,seed in enumerate(seeds):
  D[k,seed]=0.;heap=[(0.,int(seed))]
  while heap:
   dist,a=heapq.heappop(heap)
   if dist>D[k,a]:continue
   for b,c in adj[a]:
    nd=dist+c
    if nd<D[k,b]:D[k,b]=nd;heapq.heappush(heap,(nd,b))
 return D
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections';OLD=E.parent/'r0090-native-scalp-groom';COUNT=21908;N=64
def resample(P):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];keep=np.r_[True,np.diff(arc)>1e-9];return np.column_stack([np.interp(np.linspace(0,arc[-1],N),arc[keep],P[keep,i]) for i in range(3)])
def main():
 tick=time.time();data=np.load(E/'ellie-original-groom-data.npz');body=np.load(OLD/'actual-head-surface.npz');scalp=np.load(OLD/'a-guide-lineage.npz');V=scalp['scalpWorld'];T=scalp['scalpTriangles'];targetEyes=np.load(OLD/'b-rain-hair-lineage.npz')['targetEyes'];sourceEyes=[]
 for side in ['L','R']:
  P=data['GEO-ellie_eye.'+side+'_world'];sourceEyes.append((P.min(0)+P.max(0))*.5)
 sourceEyes=np.array(sorted(sourceEyes,key=lambda x:x[0]));se=sourceEyes.mean(0);te=targetEyes.mean(0);head=data['GEO-ellie_head_world'];targetHead=body['world'];scale=np.array([(targetEyes[1,0]-targetEyes[0,0])/(sourceEyes[1,0]-sourceEyes[0,0]),(targetHead[targetHead[:,2]>=te[2],1].max()-te[1])/(head[head[:,2]>=se[2],1].max()-se[1]),(targetHead[:,2].max()-te[2])/(head[:,2].max()-se[2])]);shift=te-se*scale;assert np.all(scale>.2)&np.all(scale<2)
 guides=[];records=[];native=[];group=[]
 for pi,region in enumerate(['front','back','loose']):
  label='GEO-ellie_hair_cut.scalp-'+region;P=data[label+'_world'];edges={tuple(sorted(x)) for x in data[label+'_edges']};counts=data['GEO-ellie_hair_cut.scalp_particle'+str(pi)+'_counts'];start=0
  for index,n in enumerate(counts):
   n=int(n);assert all((j,j+1) in edges for j in range(start,start+n-1));G=P[start:start+n];assert np.isfinite(G).all() and np.linalg.norm(np.diff(G,axis=0),axis=1).sum()>.001;guides.append(resample(G*scale+shift));native.append(G);group.append(pi);records.append({'guide':len(guides)-1,'region':region,'originalGuideIndex':index,'originalProxy':label,'firstVertex':start,'points':n,'allConsecutiveEdgesVerified':True});start+=n
  assert start==int(counts.sum()) and len(P) in (start,2*start)
 G=np.array(guides);delta=G[:,0,None,:]-V[None,:,:];distance2=np.sum(delta*delta,axis=2);vertex=distance2.argmin(1);distance=np.sqrt(distance2[np.arange(len(G)),vertex]);anchors=V[vertex];G+=anchors[:,None,:]-G[:,0,None,:];edge=np.unique(np.sort(np.concatenate((T[:,[0,1]],T[:,[1,2]],T[:,[2,0]])),axis=1),axis=0);w=np.linalg.norm(V[edge[:,0]]-V[edge[:,1]],axis=1);D=graph_distances(V,edge,w,vertex);assert np.isfinite(D).all();rng=np.random.default_rng(910192);area=np.linalg.norm(np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]),axis=1);faces=rng.choice(len(T),COUNT-len(G),p=area/area.sum());uv=rng.random((len(faces),2));flip=uv.sum(1)>1;uv[flip]=1-uv[flip];bc=np.column_stack((1-uv.sum(1),uv));roots=np.einsum('ni,nij->nj',bc,V[T[faces]]);near=T[faces,np.argmax(bc,axis=1)];top=np.argpartition(D[:,near],3,axis=0)[:3].T;dist=D[top,near[:,None]];weights=1/np.maximum(dist,.0015)**2;weights/=weights.sum(1)[:,None];shape=G-G[:,0,None,:];child=roots[:,None,:]+np.sum(shape[top]*weights[:,:,None,None],axis=1);paths=np.concatenate((G,child));owner=np.r_[np.arange(len(G)),top[:,0]];u=np.linspace(0,1,N);phase=rng.uniform(0,2*np.pi,COUNT-len(G));tangent=np.gradient(child,axis=1);normal=np.cross(tangent,np.array([0.,0.,1.]));normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-20);childWave=.0005*np.sin(5*np.pi*u[None,:]+phase[:,None])*np.sin(np.pi*u)[None,:]**2;paths[len(G):]+=normal*childWave[:,:,None];assert np.isfinite(paths).all() and paths.shape==(COUNT,N,3)
 np.savez_compressed(E/'studio-guide-controllers.npz',world=G.astype('f4'),originalNativeWorld=np.concatenate(native),originalCounts=np.array([len(x) for x in native],'i4'),sourceScale=scale,sourceShift=shift,originalRegion=np.array(group,'i4'),rootScalpVertex=vertex,sourceRootBeforeTargetProjection=np.array(guides)[:,0])
 np.savez_compressed(E/'authored-studio-fibres.npz',pathsWorld=paths.astype('f4'),owner=owner.astype('i4'))
 report={'construction':'172 original professionally groomed short-hair proxy chains, verified by source particle counts, sequential mesh edges and the source script direct first-vertex mapping; no rail guessing, source script execution, stylized-mesh section conversion, analytic bob contour or UV advection. Existing adult target scalp geodesic-neighbour interpolation constructs child shapes. All172 author guides retained exactly after resampling/landmark fit/root translation;21908 total fibres.','sourcePage':'https://studio.blender.org/characters/ellie/v1/','sourceLicense':'CC-BY4.0','sourceCharacterBodyFaceRigOrCodeTransferred':False,'scriptReadAsDataOnly':'rigged_particle_hair.py: sequential proxy vertices feed each existing particle key; native particle coordinates are zero without the handler, so original stored proxy guide positions are used.','publisherGuideRegions':[31,82,59],'all172GuidesRetained':True,'allGuideEdgesVerified':True,'sourceProxyExtraVertices':'front and loose contain an additional equal-sized surface strip; original script explicitly consumes only first sum(particle key counts) vertices. These are not failed follicles dropped from this construction. Raw full source preserved.','registration':'One eyeAABB/skull-top/posterior-above-eyes affine design fit and per-guide actual scalp translation; no attachment/clearance proof.','scale':scale.tolist(),'shift':shift.tolist(),'rootTranslationQuantilesM':np.quantile(distance,[0,.5,.95,1]).tolist(),'guides':records,'roots':COUNT,'pointsEach':N,'allRequestedRootsConstructed':True,'allRequestedRootsRetained':True,'actualScalpRootAttachmentPending':True,'finiteContactSelfNaturalDynamicsRuntimeAccepted':False,'seconds':time.time()-tick};(E/'studio-authoring.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('R91_STUDIO_GUIDES_READY',len(G),COUNT,time.time()-tick,flush=True)
if __name__=='__main__':main()
