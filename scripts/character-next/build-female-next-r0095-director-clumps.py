"""Final C construction: independently curved volumetric lock director frames.
24 root-patch locks replace the smooth global sheet interpolation topology.
All1077 editable parent controllers and28002 source roots/fibres remain.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,math
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0095-authored-layered-groom';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0095-b-connected-posterior-guides.blend';OUT=S/'aevrynd-female-next-r0095-c-volumetric-director-locks.blend'
sp=importlib.util.spec_from_file_location('r95clumpbase',Path(__file__).with_name('build-female-next-r0095-layered-guides.py'));base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base);v=base.v;m=base.m;q=base.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();ref=json.loads((E/'b-build-summary.json').read_text('utf8'));assert not OUT.exists() and sha(SRC)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[ref['curveObject']];guide=bpy.data.objects[ref['guideObject']];z=np.load(E/'b-authored-groom-lineage.npz');G=z['guideWorld'].astype('f8');oldG=G.copy();P=z['actualWorld'].astype('f8');root=P[:,0].copy();parts=z['rootGroup'];N=z['rootNormals'];A=np.array(hair.matrix_world);inv=np.linalg.inv(A[:3,:3]);seeds=[];seedPart=[];parentLock=np.full(1077,-1,'i4')
 for part,count in [(0,12),(1,6),(2,6)]:
  ids=np.flatnonzero(parts[:1077]==part);selected=[int(ids[np.argmax(root[ids,2])])];dist=np.sum((root[ids]-root[selected[0]])**2,axis=1)
  for _ in range(count-1):
   j=int(ids[np.argmax(dist)])
   if dist.max()<1e-12:break
   selected.append(j);dist=np.minimum(dist,np.sum((root[ids]-root[j])**2,axis=1))
  selected=np.array(selected);distance=np.linalg.norm(root[ids,None,:]-root[selected][None,:,:],axis=2);start=len(seeds);parentLock[ids]=start+distance.argmin(1);seeds.extend(selected.tolist());seedPart.extend([part]*len(selected))
 seeds=np.array(seeds,'i4');seedPart=np.array(seedPart,'i4');assert (parentLock>=0).all();cores=[];coreFrames=[]
 for lock,seed in enumerate(seeds):
  C=G[seed].copy();F=base.frames(C,N[seed]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C,axis=0),axis=1))];t=arc/arc[-1];w=np.clip((arc-.04)/.09,0,1);w=w*w*(3-2*w);phase=lock*2.399963229728653
  # A separately authored two-axis director curve per lock. Root attachment
  # remains fixed; tangent/root offsets remain finite through the tip.
  C+=F[:,:,1]*(.012*np.sin(phase+t*3*math.pi)*w)[:,None]+F[:,:,2]*(.009*np.sin(phase*.7+t*2*math.pi)*w)[:,None];C[0]=root[seed];cores.append(C);coreFrames.append(base.frames(C,N[seed]))
 cores=np.array(cores);coreFrames=np.array(coreFrames)
 for g in range(1077):
  lock=parentLock[g];seed=seeds[lock];C=cores[lock];F=coreFrames[lock];local=F[0].T@(root[g]-root[seed]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(oldG[g],axis=0),axis=1))];a=np.clip((arc-.04)/.09,0,1);a=a*a*(3-2*a);scale=np.ones((33,3));scale[:,1:]=1-.35*a[:,None];offset=np.einsum('nij,nj->ni',F,scale*local);target=C+offset;G[g]=oldG[g]*(1-a[:,None])+target*a[:,None];G[g,0]=root[g]
 trees={};regionTrees={}
 for part in range(3):
  locks=np.flatnonzero(seedPart==part);tree=KDTree(len(locks))
  for lock in locks:tree.insert(Vector(root[seeds[lock]]),int(lock))
  tree.balance();regionTrees[part]=tree
 for lock in range(len(seeds)):
  ids=np.flatnonzero(parentLock==lock);tree=KDTree(len(ids))
  for g in ids:tree.insert(Vector(root[g]),int(g))
  tree.balance();trees[lock]=(tree,len(ids))
 indices=np.zeros((len(P),4),'i4');weights=np.zeros((len(P),4));Q=np.empty_like(P);offset=np.empty_like(P);allLock=np.empty(len(P),'i4')
 for i,r in enumerate(root):
  lock=int(parentLock[i]) if i<1077 else regionTrees[int(parts[i])].find(Vector(r))[1];allLock[i]=lock
  if i<1077:indices[i]=i;weights[i,0]=1
  else:
   tree,count=trees[lock];near=tree.find_n(Vector(r),min(count,4));k=len(near);indices[i,:k]=[v[1] for v in near];indices[i,k:]=indices[i,k-1];dist=np.array([v[2] for v in near]);w=1/np.maximum(dist,.0001)**2;weights[i,:k]=w/w.sum()
  centre=np.einsum('i,ijk->jk',weights[i],G[indices[i]]);F=base.frames(centre,N[i]);local=F[0].T@(r-centre[0]);off=np.einsum('nij,j->ni',F,local);offset[i]=off;Q[i]=centre+off;Q[i,0]=r
 guide.data.vertices.foreach_set('co',((G.reshape(-1,3)-A[:3,3])@inv.T).astype('f4').ravel());guide.data.update()
 for j in range(4):hair.data.attributes['AFN95_Guide'+str(j)].data.foreach_set('value',indices[:,j]);hair.data.attributes['AFN95_Weight'+str(j)].data.foreach_set('value',weights[:,j].astype('f4'))
 hair.data.attributes['AFN95_TransportedChildOffset'].data.foreach_set('vector',(offset@inv.T).astype('f4').ravel());hair['scope']='24 independently curved root-patch lock director curves, all1077 parent controller paths and28002 source strands/roots retained. Within-lock interpolation, finite transported cross-sections and independent3D S-bends replace a single smooth sheet field. Static unaccepted art candidate, no natural dynamics/body/self/CCD/runtime pass.';bpy.context.view_layer.update();actual=q.hair(hair).reshape(Q.shape);error=float(np.linalg.norm(actual-Q,axis=2).max());assert error<3e-6,error;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/'c-authored-groom-lineage.npz',sourceWorld=z['sourceWorld'],guideWorld=G.astype('f4'),actualWorld=Q.astype('f4'),guideIndices=indices,guideWeights=weights.astype('f4'),transportedChildOffsetWorld=offset.astype('f4'),rootGroup=parts,rootTriangle=z['rootTriangle'],rootBarycentric=z['rootBarycentric'],rootNormals=N,allowedNativeFaces=z['allowedNativeFaces'],objectMatrix=A,radiusNative=z['radiusNative'],lockSeeds=seeds,parentLock=parentLock,strandLock=allLock,lockDirectors=cores.astype('f4'));save('c-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'curveObject':hair.name,'guideObject':guide.name,'authoredGuides':1077,'sourceStrands':28002,'pointsEach':33,'directorLocks':len(seeds),'parentsPerLock':[int((parentLock==i).sum()) for i in range(len(seeds))],'allOriginalRootsStrandsCorrectedWidthsAndMaterialPreserved':True,'sourceRootMaximumWorldErrorM':float(np.linalg.norm(actual[:,0]-root,axis=1).max()),'actualLiveGuideOutputMaximumWorldErrorM':error,'construction':'Independent volumetric lock director frames and within-lock child coupling replace smooth global guide-surface interpolation. Root patch offsets, finite free cross-sections and independently curved lock spines; no endpoint collapse, geometry/radius/density scan or foreign source fitting.','naturalDynamicsContactRuntimeOrCompleteGainAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','back','body-face']:rows.append(v.image('c-director-locks',view));save('c-view-controls.json',rows)
 print('R95_DIRECTOR_LOCKS_COMPLETE_PREVIEW',time.time()-tick,flush=True)
if __name__=='__main__':main()
