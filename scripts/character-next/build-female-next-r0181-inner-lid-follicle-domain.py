"""Reconstruct inner upper follicle band on traceable original anterior Skin faces.
Geodesic surface distance replaces world-Z/front-face closest projection collapse.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,heapq,time,datetime
from mathutils import Vector
from mathutils.kdtree import KDTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0181-inner-lid-follicle-domain';OUT=C/'assets-source/aevrynd-character/female-next/r0181-source/aevrynd-female-next-r0181-a-inner-lid-follicle-domain.blend'
sp=importlib.util.spec_from_file_location('r181base',C/'scripts/character-next/build-female-next-r0180-anatomical-lash-rows.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def unit(v):return v/max(np.linalg.norm(v),1e-15)
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(t['source']))==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];lash=bpy.data.objects['AFN180_ACTUAL_ANATOMICAL_ROW_ROOTED_LASHES'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);P0,offset=m.m.curveworld(lash);P=P0.reshape(436,17,3).copy();line=np.load(E.parent/'r0180-anatomical-lash-rows/anatomical-lash-row-lineage.npz');rootT=line['rootTriangles'].copy();bc=line['rootBC'].copy();construction=json.loads((E.parent/'r0180-anatomical-lash-rows/direct-anatomical-lash-authoring.json').read_text());records=construction['actualRootAndGrowthRecords'];domains=json.loads((R/'Evidence/character-female-next/r0139-native-lid-follow/native-lid-follow-construction.json').read_text('utf-8-sig'))['actualSourceNativeDomains'];eye=np.array(json.loads((R/'Evidence/character-female-next/r0138-native-current-gaze/native-current-gaze-construction.json').read_text('utf-8-sig'))['centersWorld']['L'])
 # Original face lineage is independent from normal direction or face numbering.
 sourceOld=R/'engine/assets/characters/female-next/source/r0138-source/aevrynd-female-next-r0138-a-native-current-gaze.blend'
 with bpy.data.libraries.load(str(sourceOld),link=False) as (fr,to):to.objects=[a.FIXED[0]]
 old=to.objects[0];ow=h.arr(old.data.vertices,'co',len(old.data.vertices),3);ow=ow@np.array(old.matrix_world)[:3,:3].T+np.array(old.matrix_world.translation);old.data.calc_loop_triangles();ot=np.array([x.vertices[:] for x in old.data.loop_triangles]);oldFaces={tuple(sorted(x)) for x in ot};kd=KDTree(len(ow))
 for i,p in enumerate(ow):kd.insert(Vector(p),i)
 kd.balance();oldMesh=old.data;bpy.data.objects.remove(old,do_unlink=True)
 if oldMesh.users==0:bpy.data.meshes.remove(oldMesh)
 centroid=W[T].mean(1);normal=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-15);region=np.flatnonzero((centroid[:,0]>.017)&(centroid[:,0]<.046)&(centroid[:,1]<-.09)&(centroid[:,2]>1.459)&(centroid[:,2]<1.48)&(normal[:,1]<-.10));vertexMap={}
 def originalVertex(i):
  i=int(i)
  if i not in vertexMap:
   q,j,d=kd.find(Vector(W[i]));vertexMap[i]=(j,d)
  return vertexMap[i]
 good=[]
 for fi in region:
  mapped=[originalVertex(i) for i in T[fi]]
  if max(x[1] for x in mapped)<1e-6 and tuple(sorted(x[0] for x in mapped)) in oldFaces:good.append(int(fi))
 good=np.array(good,'i4');assert len(good)>20
 # Actual upper margin and contiguous exterior mesh define a metric root band.
 Q=W[domains['L_UPPER']['actualSkinSeedIds']];order=np.argsort(Q[:,0]);Q=Q[order];umin,umax=Q[0,0],Q[-1,0];u=(Q[:,0]-umin)/(umax-umin);coeff=np.polynomial.polynomial.polyfit(u,Q,5);uvU=(W[:,0]-umin)/(umax-umin);marginZ=np.polynomial.polynomial.polyval(np.clip(uvU,0,1),coeff)[2];upper=good[np.mean(W[T[good],2]-marginZ[T[good]],axis=1)>-.0001];ids=np.unique(T[upper]);meshKD=KDTree(len(ids))
 for j,i in enumerate(ids):meshKD.insert(Vector(W[i]),int(i))
 meshKD.balance();seeds=[];seedGaps=[]
 for q in Q:
  pp,i,d=meshKD.find(Vector(q));seeds.append(i);seedGaps.append(float(d))
 graph={int(i):{} for i in ids}
 for fi in upper:
  tri=T[fi]
  for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
   dist=float(np.linalg.norm(W[i]-W[j]));graph[int(i)][int(j)]=dist;graph[int(j)][int(i)]=dist
 distance={i:0. for i in set(seeds)};heap=[(0.,i) for i in distance];heapq.heapify(heap)
 while heap:
  d,i=heapq.heappop(heap)
  if d!=distance[i]:continue
  for j,w in graph[i].items():
   dd=d+w
   if dd<distance.get(j,1e6):distance[j]=dd;heapq.heappush(heap,(dd,j))
 chart=np.column_stack((uvU,np.array([distance.get(i,1e6) for i in range(len(W))])));triUV=chart[T[upper]];A=np.stack((triUV[:,1]-triUV[:,0],triUV[:,2]-triUV[:,0]),axis=2);det=np.linalg.det(A);valid=abs(det)>1e-12;chartFaces=upper[valid];A=A[valid];triUV=triUV[valid];inverse=np.linalg.inv(A);changes=[];changed=[]
 for rec in records:
  cid=rec['id']
  if not (rec['side']=='L' and rec['lid']=='UPPER' and rec['u']<=.35):continue
  at=rec['u'];metric=.00050+.00025*rec['row'];targetUV=np.array([at,metric]);ab=np.einsum('bij,bj->bi',inverse,targetUV-triUV[:,0]);BC=np.column_stack((1-ab.sum(1),ab));candidates=np.flatnonzero((BC>=-1e-6).all(1));assert len(candidates),('No actual exterior metric-band triangle',cid,targetUV.tolist())
  candidatePoints=np.einsum('bi,bij->bj',BC[candidates],W[T[chartFaces[candidates]]]);targetWorld=np.polynomial.polynomial.polyval(at,coeff)+np.array([0,0,metric]);pick=int(candidates[np.argmin(np.linalg.norm(candidatePoints-targetWorld,axis=1))]);fi=int(chartFaces[pick]);newBC=np.clip(BC[pick],0,1);newBC/=newBC.sum();root=newBC@W[T[fi]];n=unit(normal[fi]);tangent=unit(np.polynomial.polynomial.polyval(at,np.polynomial.polynomial.polyder(coeff)));initial=unit(.75*n+.25*unit(root-eye)+(.12+.22*at)*tangent);curl=unit(np.array([0,0,1])-initial*initial[2]);length=rec['arcLengthM'];angle=rec['totalCurlAngleRadians'];k=angle/length;samp=np.linspace(0,length,17);new=root+n*.000032+np.sin(k*samp)[:,None]/k*initial+(1-np.cos(k*samp))[:,None]/k*curl;oldMapped=[originalVertex(i) for i in rootT[cid]];oldOriginal=max(x[1] for x in oldMapped)<1e-6 and tuple(sorted(x[0] for x in oldMapped)) in oldFaces;changes.append({'id':cid,'side':'L','lid':'UPPER','row':rec['row'],'u':at,'geodesicBandDistanceM':metric,'oldOwnerWasUnchangedOriginalFace':oldOriginal,'oldRoot':line['rootWorld'][cid].tolist(),'newRoot':root.tolist(),'newSkinTriangle':fi,'newBC':newBC.tolist(),'inverseChartCandidateCount':len(candidates),'actualRootMovementM':float(np.linalg.norm(root-line['rootWorld'][cid])),'completePathReauthored':True});P[cid]=new;rootT[cid]=T[fi];bc[cid]=newBC;changed.append(cid)
 assert len(changed)>0;unchanged=np.setdiff1d(np.arange(436),changed);assert np.array_equal(P[unchanged],P0.reshape(436,17,3)[unchanged]);B=W[rootT];root=(B*bc[:,:,None]).sum(1);ax=B[:,1]-B[:,0];ax/=np.linalg.norm(ax,axis=1,keepdims=True);az=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);az/=np.linalg.norm(az,axis=1,keepdims=True);basis=np.stack((ax,np.cross(az,ax),az),axis=2);local=np.einsum('bni,bij->bnj',P-root[:,None],basis);lash.data=lash.data.copy();lash.data.name='AFN181_ORIGINAL_SURFACE_METRIC_FOLLICLE_BAND_DATA';lash.name='AFN181_ACTUAL_INNER_UPPER_METRIC_BAND_LASHES';d=lash.data;d.position_data.foreach_set('vector',P.ravel());d.attributes['AFN180_FOLLICLE_ID'].name='AFN181_FOLLICLE_ID'
 for j in range(3):d.attributes['AFN149_SkinVertex'+str(j)].data.foreach_set('value',np.repeat(rootT[:,j],17))
 for name,x in [('AFN149_RootBarycentric',np.repeat(bc,17,axis=0)),('AFN149_RootLocal',local.reshape(-1,3)),('AFN149_RestWorld',P.reshape(-1,3))]:d.attributes[name].data.foreach_set('vector',x.astype('f4').ravel())
 d.update_tag();lash.update_tag();bpy.context.view_layer.update();actual,off=m.m.curveworld(lash);error=float(np.linalg.norm(actual-P.reshape(-1,3),axis=1).max());assert error<3e-6;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};s.camera.data.type='PERSP';a.b.u.v.E=E;views=[a.b.u.v.image('a-inner-lid-metric-band','face')]
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':t['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0181-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':lash.name,'originalLashesRetainedHiddenRollback':a.FIXED[2],'retainedSourceHair':a.FIXED[1],'nativeStrands':436,'points':len(actual),'completeWomanCandidates':1,'changedCompleteFibrePaths':len(changed),'savedCameraType':'PERSP','unaccepted':True,'secondsBeforeOtherViews':time.time()-tick})
 np.savez_compressed(E/'inner-lid-follicle-band-lineage.npz',rootTriangles=rootT,rootBC=bc,rootWorld=root,rootCentre=P[:,0],curveWorld=P,rootLocal=local.astype('f4'),changedCurveIDs=np.array(changed,'i4'));save('direct-inner-lid-band-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':t['startedUTC'],'changedFailedPremise':'Actual source-lineage exterior triangle domain plus native surface geodesic-distance band replaces front-face nearest/world-Z projection which collapsed separate roots onto one Boolean crease vertex. Reauthor complete paths in inner L_UPPER third, not selective failed-fibre deletion, fixed bad tips or blanket outward move. Same436 IDs/count/radius/material, unchanged other complete paths bit exact.','sourceLineageFaceCount':len(good),'upperExteriorBandTriangles':len(upper),'actualMarginVertexProjectionGapsM':seedGaps,'actualChanges':changes,'unmodifiedOtherCompletePaths':len(unchanged),'nativeDisplayMaximumErrorM':error,'geodesicBandEngineeringNotClinicalCalibration':True,'multipleInverseChartCandidatesPreservedNotUniqueAnatomyProof':True,'allOriginalSevenRawMeshUVSignaturesRetained':True,'appearanceOperationFiniteContactsRuntimeUnaccepted':True})
 for v in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('a-inner-lid-metric-band',v));save('inner-lid-band-preview-controls.json',views)
 m.E=E;save('inner-lid-band-eye-capture-controls.json',m.eye_image('a-inner-lid-metric-band-eyes',str(OUT)));print('R181_INNER_LID_SOURCE_SURFACE_METRIC_BAND_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
