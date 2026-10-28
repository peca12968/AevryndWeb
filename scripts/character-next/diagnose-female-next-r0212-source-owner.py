"""Complete CC0 operative rest through a regularized volumetric grid.
Current guide/birth identity comes from explicit anatomical cap charts.
No old failed free path, analytic spine, TPS or foreign scalp graft.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0212-complete-artist-volume-foundation';F=Path('F:/AevryndEvidence/r0212-complete-artist-volume-foundation');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,d):(E/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
spec=importlib.util.spec_from_file_location('r212base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;source=np.load(E/'source-operative-complete-rest-guide-data.npz');S=source['straight_hair_to_shoulder_operativeP'].astype('f8').reshape(252,16,3);assert np.array_equal(source['straight_hair_to_shoulder_operativeOffsets'],np.arange(252)*16);cap=np.load(E.parent/'r0206-operative-guide-anatomical-map/failed-operative-guide-cap-map-lineage.npz');sv=cap['sourceCapWorld'];st=cap['sourceCapTriangles'];suv=cap['sourceCapUV'];tv=cap['targetCapWorld'];tt=cap['targetCapTriangles'];tuv=cap['targetCapUV'];sb=cap['sourceBoundary'];tb=cap['targetBoundary'];sa=cap['sourceBoundaryAngles'];ta=cap['targetBoundaryAngles'];mapped=cap['volumeAnchorTargets'];assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN211_ACTUAL_REGION_OWNED_WHOLE_REST_GROOM'];oldBirths=bpy.data.objects['AFN211_CURRENT_SKIN_REGION_OWNED_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);lineage=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');sf=lineage['actualCurrentScalpFaces'];assert np.max(abs(W[T[sf]]-tv[tt]))<3e-6
def uvhit(q,uvfaces):
 aa=uvfaces[:,0];v=uvfaces[:,1]-aa;w=uvfaces[:,2]-aa;r=q-aa;det=v[:,0]*w[:,1]-v[:,1]*w[:,0];valid=abs(det)>1e-15;b=np.full(len(det),-np.inf);c=b.copy();b[valid]=(r[valid,0]*w[valid,1]-r[valid,1]*w[valid,0])/det[valid];c[valid]=(v[valid,0]*r[valid,1]-v[valid,1]*r[valid,0])/det[valid];bc=np.column_stack([1-b-c,b,c]);ids=np.flatnonzero((bc.min(1)>=-1e-7)&valid);assert len(ids)>0,('UV outside anatomical cap',q.tolist());i=int(ids[0]);z=np.clip(bc[i],0,1);return i,z/z.sum()
def radial(q,angles,Buv):
 theta=np.arctan2(q[:,1],q[:,0]);theta=np.where(theta<-np.pi/2,theta+2*np.pi,theta);i=np.clip(np.searchsorted(angles,theta,side='right')-1,0,len(angles)-1);v=Buv[i];w=Buv[(i+1)%len(Buv)];d=np.column_stack([np.cos(theta),np.sin(theta)]);cross=lambda x,y:x[:,0]*y[:,1]-x[:,1]*y[:,0];return cross(v,w)/cross(d,w-v)
def target(q):
 q=np.atleast_2d(q);z=q*(radial(q,ta,tuv[tb])/radial(q,sa,suv[sb]))[:,None];fi=[];bc=[]
 for point in z:
  i,w=uvhit(point,tuv[tt]);fi.append(int(sf[i]));bc.append(w)
 fi=np.array(fi,'i4');bc=np.array(bc);return np.einsum('ni,nij->nj',bc,W[T[fi]]),fi,bc
tree=BVHTree.FromPolygons(sv.tolist(),st.tolist(),all_triangles=True);guideParam=[];sourceGaps=[]
for q in S[:,0]:
 hit,no,i,gap=tree.find_nearest(Vector(q));tri=sv[st[i]];uv=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),np.array(hit)-tri[0],rcond=None)[0];bc=np.array([1-uv.sum(),*uv]);guideParam.append(bc@suv[st[i]]);sourceGaps.append(gap)

firstGap=np.array(sourceGaps);bpy.ops.wm.open_mainfile(filepath=str(F/'aevrynd-female-next-r0212-cc0-shoulder-input.blend'));src=bpy.data.objects['straight_hair_to_shoulder'];body=src.data.surface;BV,BT=a.geometry(body);me=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;me.calc_loop_triangles();loops=np.array([x.loops[:] for x in me.loop_triangles]);uvName=src.data.surface_uv_map;uvFaces=h.arr(me.uv_layers[uvName].data,'uv',len(me.uv_layers[uvName].data),2)[loops];sourceUV=source['straight_hair_to_shoulder_operativeUV'];owners=[];bcs=[];logical=[];param=[];lgaps=[]
for q in sourceUV:
 i,bc=uvhit(q,uvFaces);point=bc@BV[BT[i]];hit,no,j,gap=tree.find_nearest(Vector(point));tri=sv[st[j]];v=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),np.array(hit)-tri[0],rcond=None)[0];w=np.array([1-v.sum(),*v]);owners.append(i);bcs.append(bc);logical.append(point);param.append(w@suv[st[j]]);lgaps.append(gap)
logical=np.array(logical);offset=logical-S[:,0];q={'UTC':stamp(),'originalFirstAttemptTerminal':'776b9e actual assertion source firstpoint-to-cap <3um failed; no current groom emitted, original script preserved.','sourceGuideFirstPointToCapQuantilesM':np.quantile(firstGap,[0,.5,.9,1]).tolist(),'actualNativeUVLogicalBirthToQualifiedSourceCapMaximumM':float(max(lgaps)),'actualNativeUVToGuideFirstPointOffsetQuantilesM':np.quantile(np.linalg.norm(offset,axis=1),[0,.5,.9,1]).tolist(),'all252ActualUVSourceOwnersFound':True,'preGenerationFirstPointNotAutomaticallyLogicalBirth':True,'rootOwnershipPremiseNotRelaxed':True};save('source-guide-ownership-single-diagnosis.json',q);np.savez_compressed(E/'actual-native-source-guide-owners.npz',sourceLogicalWorld=logical,sourceSurfaceUV=sourceUV,sourceOwnerFaces=np.array(owners),sourceOwnerBC=np.array(bcs),sourceGuideRootParam=np.array(param),sourceGuideWholePathAttachmentCorrection=offset);print('R212_ACTUAL_SOURCE_GUIDE_OWNERSHIP_DIAGNOSIS',json.dumps(q),flush=True)
