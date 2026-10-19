"""Private C2: quadratic displacement fairing with body contact targets.
Not hair dynamics. All fibres participate; only measured contacts activate
constraints. Actual full finite-capsule verification is independent.
"""
import bpy,importlib.util,json,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('c1contact39',Path(__file__).with_name('study-female-next-r0039-surface-transfer.py'));c1=importlib.util.module_from_spec(sp);sp.loader.exec_module(c1)
c=c1.c;a=c.a;m=c.m;f=c.f;b=c.b;v=c.v;S=c.a.S;PVT=c.PRIVATE
SRC=c1.OUT;OUT=PVT/'aevrynd-female-next-r0039-c2-contact-fit-study.blend'
def query(P,tree,tri,radii):
    flat=P.reshape(-1,3);h=np.empty_like(flat);normal=np.empty_like(flat);dist=np.empty(len(flat))
    for lo in range(0,len(flat),8192):
        q=[tree.find_nearest(Vector(p)) for p in flat[lo:lo+8192]]
        h[lo:lo+len(q)]=[row[0] for row in q];normal[lo:lo+len(q)]=[row[1] for row in q];dist[lo:lo+len(q)]=[row[3] for row in q]
    signed=np.einsum('ij,ij->i',flat-h,normal);near=dist<radii.ravel()+.00035;possible=(signed<0)&(~near)
    inside=np.zeros(len(flat),bool);unresolved=0;outsideNegative=0
    for i in np.flatnonzero(possible):
        result=f.flowcheck.cap.solid.classify(tree,tri,Vector(flat[i]))
        if result=='inside':inside[i]=True
        elif result=='unresolved':unresolved+=1
        else:outsideNegative+=1
    mask=(near|inside).reshape(P.shape[:2]);mask[:,0]=False
    # For already-outside near points, use the actual closest-point direction
    # instead of a halfspace that could push a separated strand the wrong way.
    direction=normal.copy();outside_near=near&(signed>=0)&(dist>1e-10)
    direction[outside_near]=(flat[outside_near]-h[outside_near])/dist[outside_near,None]
    target=(h+direction*(radii.ravel()+.00035)[:,None]).reshape(P.shape)
    return mask,target,{'pointTargets':int(mask.sum()),'insidePoints':int(inside.sum()),'unresolvedInsideTests':unresolved,'negativeHalfspaceButOutsideNotPushed':outsideNegative}
def quadratic(rest,targets,mask,lam=1.0,weight=1e5):
    n=rest.shape[1];D=np.zeros((n-2,n))
    for j in range(n-2):D[j,j:j+3]=(1,-2,1)
    Q=np.eye(n)+lam*D.T@D;Q=Q[1:,1:]
    active=np.flatnonzero(mask[:,1:].any(1));out=rest.copy()
    for lo in range(0,len(active),128):
        ids=active[lo:lo+128];W=mask[ids,1:].astype('f8')*weight
        A=np.broadcast_to(Q,(len(ids),n-1,n-1)).copy();di=np.arange(n-1);A[:,di,di]+=W
        rhs=(targets[ids,1:]-rest[ids,1:])*W[:,:,None]
        out[ids,1:]=rest[ids,1:]+np.linalg.solve(A,rhs)
    out[:,0]=rest[:,0];return out
def main():
    start=time.time();source=json.loads((PVT/'c1-private-build.json').read_text());assert b.sha(SRC)==source['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    obj=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];p,rr=v.hair_arrays(obj);mx=np.array(obj.matrix_world);inv=np.linalg.inv(mx)
    rest=p.astype('f8')@mx[:3,:3].T+mx[:3,3];r=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);V,T=b.evaluated(bpy.data.objects[b.BODY],True)
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T];current=rest.copy();targets=rest.copy();mask=np.zeros(rest.shape[:2],bool);history=[]
    ids=np.linspace(0,len(rest)-1,256,dtype='i4')
    for iteration in range(5):
        flagged,newTargets,stats=query(current,tree,tri,r);mask|=flagged;targets[flagged]=newTargets[flagged]
        current=quadratic(rest,targets,mask);maximum=float(np.linalg.norm(current-rest,axis=2).max())
        if '--proposal-only' in sys.argv:
            curve,cv=np.unravel_index(np.linalg.norm(current-rest,axis=2).argmax(),rest.shape[:2]);q=rest[curve,cv]
            hh,nn,ti,dist=tree.find_nearest(Vector(q));cl=f.flowcheck.cap.solid.classify(tree,tri,Vector(q));arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(rest[curve],axis=0),axis=1))]
            diagnostic={'source':str(SRC),'sourceSha256':b.sha(SRC),'maximumDisplacementM':maximum,'curve':int(curve),'cv':int(cv),'restPointWorld':q.tolist(),'proposedPointWorld':current[curve,cv].tolist(),'actualRootWorld':rest[curve,0].tolist(),'nearestBodyPointWorld':list(hh),'nearestBodyDistanceM':dist,'restPointClassification':cl,'arcFromRootM':float(arc[cv]),'strandLengthM':float(arc[-1]),'stats':stats,'scope':'Proposal only, no geometry saved or adopted; diagnosis of the12mm guard before considering any budget change.'}
            c.write('c2-max-contact-proposal.json',diagnostic);print('C2_PROPOSAL_ONLY',diagnostic,flush=True);return
        print('C2_CONTACT_FIT',iteration,stats,'maxM',maximum,flush=True)
        if maximum>.012:
            history.append({'iteration':iteration,**stats,'maximumDisplacementM':maximum,'status':'STOP_OVER12MM_REPAIR_BUDGET'});break
        local=((current-mx[:3,3])@inv[:3,:3].T).astype('f4');local[:,0]=p[:,0]
        obj.data.position_data.foreach_set('vector',local.ravel());bpy.context.view_layer.update();actual,ar=v.hair_arrays(obj)
        world=actual.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=ar.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
        pilot=f.flowcheck.check(world[ids],rad[ids],tree,tri)
        row={'iteration':iteration,**stats,'maximumDisplacementM':maximum,'pilotUnqualifiedSegments':pilot['unqualifiedSegments']}
        history.append(row);c.write('c2-contact-fit-progress.json',{'history':history,'limits':'Actual11223fibres were fitted. Representative checks are not all-child qualification.'})
        if pilot['status']=='PASS_TESTED_STATIC_CAPSULES':
            current=world;break
    else:current=world
    # Always read saved float32 geometry, not double precision solver buffers.
    actual,ar=v.hair_arrays(obj);world=actual.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=ar.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    assert np.array_equal(actual[:,0],p[:,0]) and np.array_equal(ar,rr)
    # f.state includes this private visible curve, so only original scene layers
    # are compared while temporarily hiding this study object.
    obj.hide_render=True;expected=before.copy();expected['curves']=dict(before['curves']);expected['curves'].pop(obj.name,None)
    assert f.state()==expected;obj.hide_render=False
    final_pilot=f.flowcheck.check(world[ids],rad[ids],tree,tri);c.write('c2-representative-body-contact.json',final_pilot)
    full=None
    if final_pilot['status']=='PASS_TESTED_STATIC_CAPSULES':
        full=f.flowcheck.check(world,rad,tree,tri);c.write('c2-all-fibre-body-contact.json',full)
    f.E=PVT;f.render('c2-private')
    b.camera('face');s.camera.data.lens=85;s['AFN39_status']='PRIVATE_CONTACT_FIT_RESEARCH_NOT_ADOPTED'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    c.write('c2-private-build.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
      'author':'Original groom Daniel Bystedt; own retarget and quadratic contact-fit by Aevrynd',
      'license':'Upstream CC BY-SA exact version unresolved. PRIVATE_RESEARCH_ONLY_NOT_ADOPTED',
      'method':'Minimize displacement/data and second-difference displacement energy with high-weight measured contact targets; per-curve global quadratic solves; all roots fixed. Static authoring, not Cosserat dynamics.',
      'designClearanceM':.00035,'contactProofAllowanceM':1e-6,'curveCount':len(world),'pointsPerCurve':128,'allFolliclesRootsRadiiRetained':True,
      'history':history,'representative':final_pilot,'allFibreBody':full,'selfContinuousMotionRuntime':'NOT_TESTED','noPublicPromotion':True,'seconds':time.time()-start})
    print('R39_C2_DONE',final_pilot['unqualifiedSegments'],None if full is None else full['unqualifiedSegments'],time.time()-start,flush=True)
if __name__=='__main__':main()
