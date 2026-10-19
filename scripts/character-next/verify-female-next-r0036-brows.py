"""Reopen the actual full-head file, then qualify only the changed static brows."""
import bpy,importlib.util,json,time,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('c36','build-female-next-r0036-brows.py');solver=module('s36','solve-female-next-r0036-brow-contacts.py');b=c.b;v=c.v;E=c.E;S=c.S
PREFIX='b' if '--variant-b' in sys.argv else 'a'
def scalar_summary(gap,limit=1e-6):return {'pairs':len(gap),'notCertifiedSeparated':int((gap<=limit).sum()),'minimumTestedPairCapsuleGapM':float(gap.min()) if len(gap) else None}
def scalp_contact(P,R,H,HR):
    A=H[:,:-1].reshape(-1,3);B=H[:,1:].reshape(-1,3);rad=np.maximum(HR[:,:-1],HR[:,1:]).ravel();r=np.maximum(R[:,:-1],R[:,1:]).ravel();C=P[:,:-1].reshape(-1,3);D=P[:,1:].reshape(-1,3)
    clo=np.minimum(C,D)-r[:,None]-1e-6;chi=np.maximum(C,D)+r[:,None]+1e-6;lo=clo.min(0);hi=chi.max(0);slo=np.minimum(A,B)-rad[:,None]-1e-6;shi=np.maximum(A,B)+rad[:,None]+1e-6
    separation=np.maximum(lo-shi,slo-hi).max(1);ids=np.flatnonzero(separation<=0);minimum=float(separation[separation>0].min()) if np.any(separation>0) else None;tested=0;bad=[]
    for i in ids:
        local_sep=np.maximum(clo-shi[i],slo[i]-chi).max(1);remaining=np.flatnonzero(local_sep<=0)
        if np.any(local_sep>0):
            local_bound=float(local_sep[local_sep>0].min());minimum=min(minimum,local_bound) if minimum is not None else local_bound
        if len(remaining):
            dist,_,_=solver.distances(np.broadcast_to(A[i],(len(remaining),3)),np.broadcast_to(B[i],(len(remaining),3)),C[remaining],D[remaining]);gap=dist-rad[i]-r[remaining];tested+=len(gap);minimum=min(minimum,float(gap.min())) if minimum is not None else float(gap.min())
            for j in np.flatnonzero(gap<=1e-6):bad.append({'scalpSegment':int(i),'browSegment':int(remaining[j]),'gapM':float(gap[j])})
    return {'status':'PASS_NEUTRAL_SCALP_BROW_CAPSULE_SEPARATION' if not bad else 'FAIL_OR_UNRESOLVED','totalScalpSegments':len(A),'totalBrowSegments':len(C),'scalpSegmentsExcludedByCompleteBrowAABB':int((separation>0).sum()),'remainingScalpSegments':len(ids),'directFiniteCapsulePairs':tested,'unqualifiedPairs':len(bad),'minimumCertifiedGapLowerBoundM':minimum,'failureSamples':bad[:50],'scope':'All complete actual POLY segments, max endpoint radii, exact preserved world matrices; broadphase exclusions or finite segment-pair distances. Not scalp self/dynamics.'}
def main():
    start=time.time();build=c.read(PREFIX+'-build.json');path=Path(build['output']);assert b.sha(path)==build['outputSha256'];cache_path=Path(build['cache']);assert b.sha(cache_path)==build['cacheSha256'];cache=np.load(cache_path)
    bpy.ops.wm.open_mainfile(filepath=str(c.SRC));original=c.state();assert json.loads(json.dumps(original))==build['originalState'];parent_brows={}
    if PREFIX=='b':
        parent=Path(build['parentCandidate']);assert b.sha(parent)==build['parentCandidateSha256'];bpy.ops.wm.open_mainfile(filepath=str(parent))
        for name in build['objects']:
            o=bpy.data.objects[name];p,rr=v.hair_arrays(o);parent_brows[name]={'roots':p[:,0].copy(),'radii':rr.copy(),'matrix':np.array(o.matrix_world),'materials':[v.v32.material_signature(m) for m in o.data.materials],'materialIndices':[x.value for x in o.data.attributes['material_index'].data]}
        old_cache=np.load(c.read('a-build.json')['cache']);assert np.array_equal(cache['positions'][:,0],old_cache['positions'][:,0])
        for key in cache.files:
            if key!='positions':assert np.array_equal(cache[key],old_cache[key]),key
    bpy.ops.wm.open_mainfile(filepath=str(path));assert c.state()==original
    s=bpy.context.scene;assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0;P=[];R=[];worldP=[];worldR=[];matrices={}
    for name in build['objects']:
        o=bpy.data.objects[name];assert o.type=='CURVES' and not o.modifiers and o.parent.name==b.BODY
        pp,rr=v.hair_arrays(o);assert pp.shape==(450,24,3);assert all(x.value==1 for x in o.data.attributes['curve_type'].data);P.append(pp);R.append(rr)
        if PREFIX=='b':
            old=parent_brows[name];assert np.array_equal(pp[:,0],old['roots']) and np.array_equal(rr,old['radii']) and np.array_equal(np.array(o.matrix_world),old['matrix']);assert [v.v32.material_signature(m) for m in o.data.materials]==old['materials'] and [x.value for x in o.data.attributes['material_index'].data]==old['materialIndices']
        mx=np.array(o.matrix_world,dtype='f8');matrices[name]=mx.tolist();worldP.append(pp.astype('f8')@mx[:3,:3].T+mx[:3,3]);worldR.append(rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2))
    P=np.concatenate(P);R=np.concatenate(R);assert np.array_equal(P,cache['positions']) and np.array_equal(R,cache['radii']);assert np.isfinite(P).all() and np.isfinite(R).all() and R.min()>0
    P=np.concatenate(worldP);R=np.concatenate(worldR);body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    tid=cache['rootTriangles'];bary=cache['rootBarycentric'];assert np.array_equal(T[tid],cache['rootVertices']);assert np.max(abs(bary.sum(1)-1))<1e-10 and bary.min()>=0
    surf=np.einsum('ni,nij->nj',bary,V[T[tid]]);root_error=np.linalg.norm(surf-cache['rootSurface'],axis=1);target=surf+cache['rootNormals']*cache['rootStandOff'][:,None];root_center_error=np.linalg.norm(P[:,0]-target,axis=1);assert root_error.max()<3e-7 and root_center_error.max()<3e-7
    body_audit=v.g.check(P,R,bt,V[T]);c.save(PREFIX+'-reopened-body-capsules.json',body_audit)
    ids,gap,ss,tt=solver.contacts(P,R,1e-6);self_report=scalar_summary(gap);self_report['failureSamples']=[{'segments':ids[i].tolist(),'gapM':float(gap[i])} for i in np.flatnonzero(gap<=1e-6)[:40]];self_report['method']='All complete finite capsules, spatial-hash expanded AABB and finite pair minimum including interior and four endpoint boundaries. Same-curve directly adjacent segments are one continuous shaft and excluded; nonadjacent segments included.';c.save(PREFIX+'-reopened-brow-self.json',self_report)
    optics={};plo=np.minimum(P[:,:-1],P[:,1:])-np.maximum(R[:,:-1],R[:,1:])[...,None];phi=np.maximum(P[:,:-1],P[:,1:])+np.maximum(R[:,:-1],R[:,1:])[...,None]
    for name in original['meshes']:
        if name==b.BODY:continue
        vv,tt=b.evaluated(bpy.data.objects[name],True);sep=np.maximum(vv.min(0)-phi,plo-vv.max(0)).max(2);assert np.all(sep>1e-6),(name,sep.min());optics[name]={'completeCapsulesSeparated':int(sep.size),'minimumAxisGapM':float(sep.min())}
    scalp=bpy.data.objects[original['hair']['name']];H,HR=v.hair_arrays(scalp);mx=np.array(scalp.matrix_world);H=H.astype('f8')@mx[:3,:3].T+mx[:3,3];HR=HR.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);scalp_audit=scalp_contact(P,R,H,HR);c.save(PREFIX+'-reopened-scalp-brow-contact.json',scalp_audit)
    before=c.read('before-renders.json');after=c.read(PREFIX+'-after-renders.json');assert len(before)==len(after)==3
    for aa,bb in zip(before,after):assert {k:w for k,w in aa.items() if k!='path'}=={k:w for k,w in bb.items() if k!='path'}
    assert not bpy.data.libraries and not bpy.data.texts
    c.render(PREFIX+'-reopened',('face',))
    # Actual matched wider eye+brow closeups, with raw controls recorded.
    rows=[]
    for label,source in [('before',c.SRC),(PREFIX+'-after',path)]:
        bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;cam=s.camera;cam.location=(0,-.50,1.477);cam.rotation_euler=(Vector((0,-.11,1.477))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.filepath=str(E/(label+'-brows-closeup.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);rows.append({'label':label,'camera':b.matrix(cam.matrix_world),'lens':100,'resolution':[1400,650],'stage':v.stage()})
    assert {k:w for k,w in rows[0].items() if k!='label'}=={k:w for k,w in rows[1].items() if k!='label'};c.save(PREFIX+'-closeup-controls.json',rows)
    good=body_audit['status']=='PASS_TESTED_STATIC_CAPSULES' and self_report['notCertifiedSeparated']==0 and scalp_audit['status']=='PASS_NEUTRAL_SCALP_BROW_CAPSULE_SEPARATION' and build['relaxation']['maximumDisplacementM']<=.00065
    if PREFIX=='b':good=good and build['contactCorrection']['maximumWorldDisplacementFromAM']<=.00010
    out={'status':'PASS_REOPENED_NEUTRAL_BROW_SCOPE' if good else 'FAIL_OR_UNRESOLVED_STATIC_BROW_SCOPE','source':str(path),'sourceSha256':b.sha(path),'sourceBaseline':str(c.SRC),'sourceBaselineSha256':b.sha(c.SRC),'originalNineMeshesUVSkinMaterialsScalpArraysMatricesAndStageExact':True,'sourceState':original,'allSavedFibrePositionsRadiiExact':True,'fibres':len(P),'segments':len(P)*(P.shape[1]-1),'physicalPrimitive':'STRIP','hairSubdivision':0,'actualBrowWorldMatrices':matrices,'worldPositionsSha256':hashlib.sha256(P.tobytes()).hexdigest(),'worldRadiusBoundsSha256':hashlib.sha256(R.tobytes()).hexdigest(),'BRootsRadiiSourceLineageMaterialsAndMatricesExactToA':True if PREFIX=='b' else None,'rootSurfaceReconstructionMaxM':float(root_error.max()),'rootCenterBindingMaxM':float(root_center_error.max()),'allFolliclesRetained':True,'body':body_audit,'optics':optics,'browSelf':self_report,'scalpBrow':scalp_audit,'matchedThreeFullHeadViews':True,'matchedCloseup':True,'externalLibraries':0,'seconds':time.time()-start,'limits':['Neutral static 3D eyebrows only; no deforming rig/expressions/blink/gaze/continuous dynamics or runtime','Existing full scalp hair remains visually rejected; no scalp self/dynamic qualification','Image-flow reconstruction is an artistic inference, not captured individual follicles','Sampled CV body gaps and conservative capsule bounds are not exact global signed distances','No whole-character score, clothing, body motions, engine export/LOD/performance or female acceptance']};c.save(PREFIX+'-saved-verification.json',out);print('R36_REOPENED_DONE',out['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
