"""Independent saved-source/data/live-authoring check and cheap body falsification.
No sparse sample is presented as global/self/continuous contact acceptance.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0081-editable-curly-groom'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module('read81native','verify-female-next-r0076-crowns.py');q=v.q;m=module('read81render','build-female-next-r0081-editable-curly.py');rig=m.rig
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
STABLE='--stable-frame' in sys.argv
TAG='b' if STABLE else 'a'
def save(n,v):(E/((TAG+n[1:]) if n.startswith('a-') else n)).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def parity(tree,p,d):
 direction=Vector(d).normalized();origin=Vector(p);hits=0
 for _ in range(128):
  co,_,_,_=tree.ray_cast(origin,direction,4.)
  if co is None:return bool(hits%2)
  hits+=1;origin=co+direction*1e-7
 return None
def main():
 tick=time.time();ref=q.read(E/(TAG+'-build-summary.json'));baselineSource=ref.get('completeBaselineSource',ref['source']);baselineSHA=ref.get('completeBaselineSha256',ref['sourceSha256']);assert sha(Path(baselineSource))==baselineSHA;bpy.ops.wm.open_mainfile(filepath=baselineSource);bpy.context.scene.frame_set(1);names=rig.native_names();native={n:v.signature(bpy.data.objects[n]) for n in names};mats={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights();dental={n:q.arr(bpy.data.objects[n].data.vertices,'co',len(bpy.data.objects[n].data.vertices),3).copy() for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};baseline=q.read(E/'baseline-pilot-controls.json') if STABLE else [m.render('baseline-r76','face'),m.render('baseline-r76','body-face')];save('baseline-pilot-controls.json',baseline)
 assert sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==native;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert lights==m.m.q.lights()
 for n,p in dental.items():assert np.array_equal(q.arr(bpy.data.objects[n].data.vertices,'co',len(p),3),p)
 o=bpy.data.objects[ref['editableGuideObject']];z=np.load(E/'a-guide-and-render-lineage.npz');assert len(o.data.curves)==303 and len(o.data.position_data)==3636;assert np.array_equal(q.arr(o.data.position_data,'vector',3636,3),z['registeredNativeGuideLocal']);actual=q.hair(o);A=np.array(o.matrix_world);expected=z['renderNeutralLocal'].astype('f8')@A[:3,:3].T+A[:3,3];assert actual.shape==expected.shape;neutralError=float(np.linalg.norm(actual-expected,axis=1).max());assert neutralError<2e-6;d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in d.curves]);assert np.array_equal(counts,z['renderCounts']);radii=q.arr(d.attributes['radius'].data,'value',len(actual));assert np.array_equal(radii,z['renderRadii']);starts=np.r_[0,np.cumsum(counts)[:-1]]
 table=bpy.data.objects[ref['liveRootBindingTable']].data;ids=np.column_stack([q.arr(table.attributes['AFN69_BodyVertex'+str(i)].data,'value',len(counts),dtype='i4') for i in range(3)]);bc=q.arr(table.attributes['AFN69_Barycentric'].data,'vector',len(counts),3);body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];restBody=m.rig.k.mesh(body)['V'];frameIDs=np.column_stack([q.arr(table.attributes['AFN81_FrameVertex'+str(i)].data,'value',len(counts),dtype='i4') for i in range(3)]) if STABLE else ids;tri=restBody[ids];rt,rb,rn=rig.frames(restBody[frameIDs]);anchor=np.einsum('ij,ijk->ik',bc,tri);pointCurve=np.repeat(np.arange(len(counts)),counts);local=actual-anchor[pointCurve];coeff=np.column_stack([np.einsum('ij,ij->i',local,basis[pointCurve]) for basis in (rt,rb,rn)]);poses=[]
 for deg in (-20,20,0):
  rig.axis_pose(bpy.data.objects['AFN69_BODY_CONTROLS'],'Head',(0,0,1),deg);bpy.context.view_layer.update();current=m.rig.k.mesh(body)['V'];ct,cb,cn=rig.frames(current[frameIDs]);ca=np.einsum('ij,ijk->ik',bc,current[ids]);target=ca[pointCurve]+sum(coeff[:,i,None]*basis[pointCurve] for i,basis in enumerate((ct,cb,cn)));P=q.hair(o);err=float(np.linalg.norm(P-target,axis=1).max());poses.append({'headYawDegrees':deg,'maximumWorldPointErrorAgainstIndependentActualBodyFrameM':err,'toleranceM':2e-6,'passed':err<2e-6});save('a-body-frame-pose-progress.json',{'poses':poses});print('R81_ACTUAL_BODY_FRAME',deg,err,flush=True)
  if err>=2e-6:
   save('a-function-failure.json',{'status':'FAIL_INDEPENDENT_ACTUAL_BODY_FRAME','poses':poses.copy(),'noMotionAcceptance':True})
   if '--record-failures' not in sys.argv:raise AssertionError(('Actual render frame does not follow body',deg,err))
 # An actual authoring operation, restored in memory without modifying the file.
 before=q.hair(o).copy();nativeP=q.arr(o.data.position_data,'vector',3636,3);guideCounts=np.array([c.points_length for c in o.data.curves]);guideStarts=np.r_[0,np.cumsum(guideCounts)[:-1]];guideIndex=151;pi=int(guideStarts[guideIndex]+guideCounts[guideIndex]-3);changed=nativeP.copy();changed[pi,0]+=.002/np.linalg.norm(A[:3,0]);o.data.position_data.foreach_set('vector',changed.ravel());o.data.update_tag();bpy.context.view_layer.update();edited=q.hair(o);assert edited.shape==before.shape;delta=np.linalg.norm(edited-before,axis=1);assert float(delta.max())>1e-5;o.data.position_data.foreach_set('vector',nativeP.ravel());o.data.update_tag();bpy.context.view_layer.update();restoreError=float(np.linalg.norm(q.hair(o)-before,axis=1).max());assert restoreError<2e-6;edit={'guideIndex':guideIndex,'nativePointIndex':pi,'freeControlPointMoveWorldM':.002,'renderCurvesStable':len(counts),'renderPointsChangedOver1Micrometre':int((delta>1e-6).sum()),'maximumActualRenderPointChangeM':float(delta.max()),'maximumRestoreErrorM':restoreError,'sourceBlendNotModified':True};save('a-guide-edit-operation.json',edit)
 # Cheap finite-body falsification on free-length native knots. A strong
 # closed-body containment witness rejects qualification; no witness is a pass.
 P=q.hair(o);row=rig.k.mesh(body);edges=np.concatenate([row['T'][:,[0,1]],row['T'][:,[1,2]],row['T'][:,[2,0]]]);edges.sort(axis=1);packed=edges[:,0].astype('u8')*len(row['V'])+edges[:,1];_,incidence=np.unique(packed,return_counts=True);closed=bool(np.all(incidence==2));skin=rig.k.mesh(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);skinTree=BVHTree.FromPolygons(skin['V'].tolist(),skin['T'].tolist(),all_triangles=True);tree=BVHTree.FromPolygons(row['V'].tolist(),row['T'].tolist(),all_triangles=True);arc=np.empty(len(P));
 for st,n in zip(starts,counts):arc[st:st+n]=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P[st:st+n],axis=0),axis=1))]
 free=np.flatnonzero(arc>.008);sample=free[np.linspace(0,len(free)-1,min(8192,len(free)),dtype=int)];witness=[];nearMin=float('inf');maxRadius=float(radii.max()*np.linalg.svd(A[:3,:3],compute_uv=False).max())
 for idx in sample:
  point=P[idx];co,normal,face,distance=tree.find_nearest(Vector(point));nearMin=min(nearMin,distance)
  if distance<maxRadius+1e-6 or abs(float((point-np.array(co))@np.array(normal)))<1e-7:continue
  # Three independent parity rays confirm interior; nearest normal is not used as a sign test.
  inside=[parity(tree,point,direction) for direction in ((1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.))]
  if closed and all(value is True for value in inside):
   sco,_,sface,skinDistance=skinTree.find_nearest(Vector(point));surfaceAgreement=float(np.linalg.norm(np.array(sco)-np.array(co)))
   if surfaceAgreement>1e-6:continue
   ci=int(np.searchsorted(starts,idx,side='right')-1);witness.append({'curve':ci,'nativePointIndex':int(idx),'worldPointM':point.tolist(),'freePolygonalArcFromRootM':float(arc[idx]),'unsignedDistanceToActualBodyM':float(distance),'renderRadiusWorldUpperBoundM':maxRadius,'threeRayParityInside':inside,'nearestBodyTriangle':int(face),'nearestActualVisibleSkinTriangle':int(sface),'unsignedDistanceToActualVisibleSkinM':float(skinDistance),'closedVsActualVisibleSkinNearestPointAgreementM':surfaceAgreement})
   if len(witness)>=8:break
 contact={'status':'FAIL_FREE_SHAFT_BODY_INTERIOR_SAMPLE_WITNESSES' if witness else 'NO_STRONG_SAMPLE_WITNESS_NOT_CONTACT_PASS','actualBodyObject':body.name,'actualVisibleSkinObject':'AFN74_SKIN_AND_EXISTING_OCULAR_LINING','closedBodyEveryTriangleEdgeHasTwoIncidentFaces':closed,'nonTwoIncidentEdges':int((incidence!=2).sum()),'sampledFreeNativeKnotsPlanned':len(sample),'witnesses':witness,'witnessCountIsNotGlobalTotal':True,'minimumInspectedUnsignedDistanceM':nearMin,'globalSignedMinimumM':None,'freeThresholdPolygonalArcM':.008,'renderRadiusWorldUpperBoundM':maxRadius,'scope':'Native knots are on the declared Catmull-Rom centreline; only strong interior samples at least radius+1micrometre away from actual closed body. Parity is not nearest-normal sign. This falsifies body exclusion in the stated neutral sampled scope; it is not self, root, continuous or engine qualification.','noFullContactPass':True};save('a-neutral-body-falsification.json',contact)
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();textures.append({'relative':im.filepath,'sha256':sha(p)})
 assert len(textures)==15 and not bpy.data.libraries;result={'status':('PASS_SAVED_DATA_GUIDE_EDIT_ONLY_HEAD_FRAME_TARGET_FAILED' if not all(p['passed'] for p in poses) else 'PASS_SAVED_DATA_LIVE_GUIDE_EDIT_AND_INDEPENDENT_BODY_FRAME_SCOPE_ONLY'),'bodyFrameTargetPassed':all(p['passed'] for p in poses),'source':ref['output'],'sha256':ref['outputSha256'],'allFiveNativeCagesKeysUVWeightsDriversExact':True,'allOriginalMaterialsLightsDentalDataExact':True,'actualRenderCurves':len(counts),'actualRenderPoints':len(P),'neutralSavedReadbackMaximumErrorM':neutralError,'independentBodyFramePoses':poses,'guideEditOperation':edit,'contactStatus':contact['status'],'externalTextures':textures,'naturalDynamicsSelfContinuousBodyAndEngineAccepted':False,'seconds':time.time()-tick};save('a-independent-readback.json',result);print('R81_READBACK_AND_BODY_FALSIFICATION',contact['status'],len(witness),time.time()-tick,flush=True)
if __name__=='__main__':main()
