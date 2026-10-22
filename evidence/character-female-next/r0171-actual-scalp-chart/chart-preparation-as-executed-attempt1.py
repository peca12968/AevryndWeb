"""Actual source/target scalp domains and orientation-preserving harmonic charts."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0171-actual-scalp-chart';sp=importlib.util.spec_from_file_location('r171charts',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;before=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin);previous=np.load(E.parent/'r0170-root-constrained-carrier/root-constrained-carrier-lineage.npz');carrier=bpy.data.objects['AFN170_ROOT_CONSTRAINED_ANATOMICAL_CARRIER'];raw=carrier.data;V=h.arr(raw.vertices,'co',len(raw.vertices),3);raw.calc_loop_triangles();F=np.array([t.vertices[:] for t in raw.loop_triangles]);index=carrier.vertex_groups['scalp'].index;weights=np.array([next((g.weight for g in v.groups if g.group==index),0.) for v in raw.vertices]);sourceFaces=np.flatnonzero(weights[F].min(1)>.5);targetFaces=previous['actualCurrentScalpFaces'];sourceRootIDs=previous['explicitRootVertexIDs'];allSourceFaces=np.flatnonzero(np.isin(F,sourceRootIDs).any(1));sourceFaces=np.unique(np.r_[sourceFaces,allSourceFaces]);records={};arrays={}
def chart(label,P,tri,faceIDs):
 # Weld identical physical seam points for chart topology; original actual
 # surface coordinates and triangle orientation are retained for binding.
 old=np.unique(tri[faceIDs]);Q=P[old];_,first,inverse=np.unique(np.round(Q,7),axis=0,return_index=True,return_inverse=True);Q=Q[first];lookup=np.full(len(P),-1,'i4');lookup[old]=inverse;G=lookup[tri[faceIDs]];valid=np.array([len(set(map(int,f)))==3 for f in G]);G=G[valid];faceIDs=faceIDs[valid];edge=np.sort(np.vstack((G[:,[0,1]],G[:,[1,2]],G[:,[2,0]])),axis=1);edges,count=np.unique(edge,axis=0,return_counts=True);boundary=edges[count==1];adj={}
 for i,j in boundary:adj.setdefault(int(i),[]).append(int(j));adj.setdefault(int(j),[]).append(int(i))
 unused=set(adj);loops=[]
 while unused:
  start=min(unused);path=[start];previousID=-1;cur=start
  while True:
   nxt=[x for x in adj[cur] if x!=previousID];assert len(nxt)>0;choice=nxt[0]
   if choice==start:break
   assert choice not in path,'Non-simple scalp boundary';path.append(choice);previousID,cur=cur,choice
  unused.difference_update(path);loops.append(path)
 rec={'vertices':len(Q),'triangles':len(G),'boundaryLoops':[len(x) for x in loops],'boundaryValences':sorted(set(len(v) for v in adj.values())),'nonmanifoldEdges':int((count>2).sum()),'euler':len(Q)-len(edges)+len(G)};records[label]=rec
 if len(loops)!=1 or rec['boundaryValences']!=[2] or rec['nonmanifoldEdges'] or rec['euler']!=1:return None
 loop=np.array(loops[0]);B=Q[loop];front=int(np.argmin(B[:,1]+.2*abs(B[:,0])));loop=np.roll(loop,-front);B=Q[loop];signed=sum(np.cross(Q[f[1]]-Q[f[0]],Q[f[2]]-Q[f[0]])[2] for f in G)
 if signed<0:loop=np.r_[loop[:1],loop[:0:-1]];B=Q[loop]
 lengths=np.linalg.norm(np.roll(B,-1,axis=0)-B,axis=1);phase=np.r_[0,np.cumsum(lengths[:-1])]/lengths.sum()*2*np.pi;boundaryUV=np.column_stack((np.sin(phase),-np.cos(phase)));UV=np.zeros((len(Q),2));UV[loop]=boundaryUV;isBoundary=np.zeros(len(Q),bool);isBoundary[loop]=True;directed=np.vstack((edges,edges[:,::-1]));degree=np.bincount(directed[:,0],minlength=len(Q));internal=~isBoundary
 for iteration in range(3000):
  summed=np.zeros_like(UV);np.add.at(summed,directed[:,0],UV[directed[:,1]]);new=summed/np.maximum(degree[:,None],1);delta=float(np.max(abs(new[internal]-UV[internal])));UV[internal]=new[internal]
  if delta<1e-9:break
 area=np.cross(UV[G[:,1]]-UV[G[:,0]],UV[G[:,2]]-UV[G[:,0]]);rec.update(iterations=iteration+1,residual=delta,positiveUVTriangles=int((area>1e-12).sum()),negativeUVTriangles=int((area< -1e-12).sum()),nearZeroUVTriangles=int((abs(area)<=1e-12).sum()));arrays.update({label+'World':Q,label+'Triangles':G,label+'UV':UV,label+'OriginalFaceIDs':faceIDs,label+'OriginalVertexIDs':old,label+'OriginalToWeld':inverse,label+'Boundary':loop});return UV
chart('source',V,F,sourceFaces);chart('target',W,T,targetFaces);result={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceScalpVertexGroup':'scalp with original complete-root incident faces','actualTargetScalpFrom':'170 unchanged original albedo connected anatomical scalp','sourceAndTargetDomainRecords':records,'noGeometryMovedOrSourceWomanResaved':True,'chartCapabilityPassed':all(x.get('negativeUVTriangles',1)==0 and x.get('nearZeroUVTriangles',1)==0 for x in records.values())};(E/'actual-scalp-chart-preparation.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());np.savez_compressed(E/'actual-scalp-chart-construction.npz',**arrays);print('R171_ACTUAL_SOURCE_TARGET_SCALP_CHART_PREPARATION',json.dumps(result),flush=True)
