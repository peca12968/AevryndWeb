"""r40 static complete-path reauthoring with length/bend/contact constraints.
PBD-style geometric authoring, NOT calibrated hair dynamics, Cosserat twist,
or continuous collision. Independent full finite-segment gates follow.
Artist data stays in the private study until reuse terms are documented.
"""
import bpy,importlib.util,json,time,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('inspect40rod',Path(__file__).with_name('inspect-female-next-r0040-guide-source.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
c=i.c;a=i.a;m=i.m;f=i.f;b=i.b;v=i.v;E=i.E;PVT=i.PVT;S=a.S
c1=f.flowcheck.module('c1r40','study-female-next-r0039-surface-transfer.py')
SRC=S/'aevrynd-female-next-r0038-b-live-groom-authoring.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def query(P,tree,tri,radius,margin=.00035):
    shape=P.shape;flat=P.reshape(-1,3);H=[];N=[];D=[]
    for p in flat:
        h,n,ti,d=tree.find_nearest(Vector(p));H.append(h);N.append(n);D.append(d)
    H=np.array(H);N=np.array(N);D=np.array(D);signed=np.einsum('ij,ij->i',flat-H,N)
    near=D<radius+margin;negative=np.flatnonzero((signed<0)&(~near));inside=np.zeros(len(flat),bool);unresolved=0
    for k in negative:
        state=f.flowcheck.cap.solid.classify(tree,tri,Vector(flat[k]))
        if state=='inside':inside[k]=True
        elif state=='unresolved':unresolved+=1
    outsideNear=near&(signed>=0)&(D>1e-10);N[outsideNear]=(flat[outsideNear]-H[outsideNear])/D[outsideNear,None]
    target=H+N*(radius+margin);mask=near|inside
    delta=np.where(mask[:,None],target-flat,0.)
    return delta.reshape(shape),{'active':int(mask.sum()),'inside':int(inside.sum()),'unresolved':unresolved}
def pair_distances(P,L,inv,hop,strength):
    for color in range(2*hop):
        j=np.arange(color,P.shape[1]-hop,2*hop);k=j+hop
        if not len(j):continue
        D=P[:,k]-P[:,j];dist=np.linalg.norm(D,axis=2);u=D/np.maximum(dist[:,:,None],1e-20)
        den=inv[:,j]+inv[:,k];corr=strength*(dist-L[:,j])/np.maximum(den,1e-20)
        delta=u*corr[:,:,None];P[:,j]+=delta*inv[:,j,None];P[:,k]-=delta*inv[:,k,None]
def crossing_constraints(P,inv,radius,tree,tri):
    rr=np.full(P.shape[:2],radius,dtype='f8');audit=f.flowcheck.check(P.astype('f4').astype('f8'),rr,tree,tri)
    for row in audit['failureSamples']:
        ci=row['curve'];j=row['segment'];aa=P[ci,j];bb=P[ci,j+1];D=bb-aa;length=np.linalg.norm(D)
        if length<1e-12:continue
        h,n,ti,dist=tree.ray_cast(Vector(aa),Vector(D/length),float(length))
        if h is None:continue
        t=float(np.clip(dist/length,0,1));wi=inv[ci,j];wj=inv[ci,j+1];den=wi*(1-t)**2+wj*t*t
        if den<1e-12:continue
        corr=np.array(n)*(radius+.00035)/den
        P[ci,j]+=wi*(1-t)*corr;P[ci,j+1]+=wj*t*corr
    return audit
def main():
    start=time.time();assert b.sha(SRC)=='0f8707b92196bc58e158b997a9170f22708d5ddeb2c2e0d95856cbfd00bb4c04'
    save('round-contract.json',{'revision':'female-next-r0040-a-private','source':str(SRC),'sourceSha256':b.sha(SRC),
      'previousGoalTurnClassification':'progress: r39private artist transfer exposed natural flow and contact causes; ownedA/B rejected; no main promotion; pushed29d0539',
      'problem':'Late raw-guide paths and generated children enter the actual head; prior local quadratic fit needed27.94mm and was not applied.',
      'methodDifference':'Reauthor COMPLETE376guide paths with fixed true-body roots/exit directions, approximate inextensibility and two-hop bending-distance constraints. Body contact acts on paths; no density/radius/tolerance change or shared exit/ring/offset field.',
      'notJustLargerRepairBudget':'Different nonlinear constraint problem preserves lengths and permits bend-plane rotation, instead of nearest-target quadratic point fitting. Up to40mm complete-path movement is bounded by measured24-28mm deep interior paths; this is not a relaxed contact gate.',
      'referenceData':'DanielBystedt HairStyles raw main346+secondary30, private only, original data/hash/provenance retained',
      'expectedVisibleChange':'Retain natural varied flow while correcting specific impossible late trajectories; complete-head rendering only after guide feasibility before children.',
      'smallTest':'All376native-resampled128point guide paths, actual closed target body, full segment capsules of46um radius and all root containment. Not a child or self proof.',
      'reject':['Any unresolved guide/body/root capsule after bounded solver','Over40mm displacement or severe rest-length/shape distortion','New cap/rope/collapsed silhouette'],
      'resources':{'startUTC':'2026-10-19 12:51:06 UTC','checkpointUTC':'2026-10-19 13:36:06 UTC','threads':4,'heavyJobsAtOnce':1,'maximumOuterPasses':100},
      'scope':'Static geometric guide reauthoring only; no calibrated dynamics, twist, friction, continuous/self/child or runtime acceptance.'})
    data=np.load(PVT/'raw-artist-guides-reference-only.npz');raw=data['allRawPositions'].astype('f8')
    fit=np.load(c.PRIVATE/'c1-private-surface-transfer.npz');warp,coef=c1.fit(fit['sourceAnchors'],fit['targetAnchors'])
    world=warp(raw*np.array((.094,.085,.081))+np.array((0,.005,.234)))
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    normals=[];rootTri=[];rootBary=[]
    for ci,P in enumerate(world):
        h,n,tid,d=tree.find_nearest(Vector(P[0]));face=tri[tid];h,bc=c1.exact_triangle_foot(P[0],face);normal=a.norm(np.cross(face[1]-face[0],face[2]-face[0]))
        root=h+normal*.00018;delta=root-P[0];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
        P+=delta*(1-np.clip(arc/.03,0,1))[:,None]**2;P[0]=root
        L=np.linalg.norm(P[1]-P[0]);tangent=a.norm(P[1]-P[0]);tangent=a.norm(tangent+normal*max(.25-tangent@normal,0))
        P[1]=root+tangent*L;normals.append(normal);rootTri.append(tid);rootBary.append(bc)
    rest=world.copy();fixed=world[:,:2].copy();L=np.linalg.norm(np.diff(rest,axis=1),axis=2);L2=np.linalg.norm(rest[:,2:]-rest[:,:-2],axis=2)
    inv=np.ones(rest.shape[:2]);inv[:,:2]=0.;history=[];radius=.000046;best=None;bestCount=10**9
    f.flowcheck.cap.math_controls()
    for outer in range(101):
        # No gravity/time calibration: this solves static geometric feasibility.
        for k in range(8):pair_distances(world,L,inv,1,1.)
        pair_distances(world,L2,inv,2,.10)
        delta,stats=query(world,tree,tri,radius);world+=delta*inv[:,:,None];world[:,:2]=fixed
        if outer%4==0:
            for color in (0,1):
                j=np.arange(color,127,2);mid=(world[:,j]+world[:,j+1])*.5
                dm,_=query(mid,tree,tri,radius)
                den=inv[:,j]+inv[:,j+1];world[:,j]+=dm*(2*inv[:,j]/np.maximum(den,1e-20))[:,:,None];world[:,j+1]+=dm*(2*inv[:,j+1]/np.maximum(den,1e-20))[:,:,None]
            world[:,:2]=fixed
        maximum=float(np.linalg.norm(world-rest,axis=2).max())
        if maximum>.040:
            history.append({'pass':outer,'maximumDisplacementM':maximum,'status':'STOP_OVER40MM_COMPLETE_PATH_BUDGET'});break
        if outer%10==0:
            audit=crossing_constraints(world,inv,radius,tree,tri);world[:,:2]=fixed
            stretch=np.linalg.norm(np.diff(world,axis=1),axis=2)/np.maximum(L,1e-20)-1.
            row={'pass':outer,**stats,'unqualifiedGuideSegments':audit['unqualifiedSegments'],'rootFailures':len(audit['rootFailures']),'maximumDisplacementM':maximum,'maximumRelativeEdgeLengthError':float(np.abs(stretch).max())}
            history.append(row);save('guide-authoring-progress.json',{'history':history,'scope':'All376guides, not children/self/dynamics.'});print('R40_GUIDE_PASS',row,flush=True)
            if audit['unqualifiedSegments']<bestCount:bestCount=audit['unqualifiedSegments'];best=world.copy()
            if audit['status']=='PASS_TESTED_STATIC_CAPSULES' and np.abs(stretch).max()<.03:break
    if best is not None:world=best
    # Saved-precision proof, every guide/segment, fixed roots and source radius.
    saved=world.astype('f4').astype('f8');r=np.full(saved.shape[:2],radius);proof=f.flowcheck.check(saved,r,tree,tri)
    save('a-all-guide-body-contact.json',proof);stretch=np.linalg.norm(np.diff(saved,axis=1),axis=2)/np.maximum(L,1e-20)-1.
    np.savez_compressed(PVT/'a-rebuilt-guide-paths.npz',positionsWorld=saved.astype('f4'),restPositionsWorld=rest.astype('f4'),rootTriangles=np.array(rootTri,dtype='i4'),rootBarycentric=np.array(rootBary),rootNormals=np.array(normals),guideUV=data['guideUV'])
    save('a-guide-build-summary.json',{'status':'PASS_STATIC_GUIDE_BODY_ONLY' if proof['status']=='PASS_TESTED_STATIC_CAPSULES' and np.abs(stretch).max()<.03 else 'NOT_QUALIFIED_GUIDE_STRUCTURE_OR_BODY',
      'sourceArtist':'Daniel Bystedt raw guides; private geometric reauthoring by Aevrynd','guides':376,'mainGuides':346,'pointsPerGuide':128,'radiusM':radius,
      'body':proof,'maximumRelativeEdgeLengthError':float(np.abs(stretch).max()),'maximumDisplacementM':float(np.linalg.norm(saved-rest,axis=2).max()),
      'rootMaximumFloat32ReconstructionErrorM':float(np.linalg.norm(saved[:,0]-fixed[:,0],axis=1).max()),'history':history,'allChildrenSelfDynamicsRuntime':'NOT_TESTED','sourceSceneStateUnmodified':f.state()==before,'seconds':time.time()-start})
    print('R40_GUIDE_DONE',proof['status'],proof['unqualifiedSegments'],'stretch',float(np.abs(stretch).max()),time.time()-start,flush=True)
if __name__=='__main__':main()
