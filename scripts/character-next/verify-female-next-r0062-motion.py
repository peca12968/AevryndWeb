"""Native-cache readback plus complete finite-shaft linear-motion certificates.

Pair relative-displacement bounds cover arbitrary segment parameters and time.
Body tests use Lipschitz separation or separating planes against every nearby
triangle of the swept four-endpoint convex hull; bounded subdivision refines
only unresolved certificates. No representative guide or point-only acceptance.
"""
from pathlib import Path
import bpy,numpy as np,json,time,math,importlib.util,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('motionVerify62',Path(__file__).with_name('bake-female-next-r0062-bundle-motion.py'));bake=importlib.util.module_from_spec(sp);sp.loader.exec_module(bake)
m=bake.m;E=m.E;EPS=1e-6
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def flat(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;a=np.empty(len(d.position_data)*3,'f4');d.position_data.foreach_get('vector',a);return a.reshape(-1,3)

def self_interval(Q0,Q1,R,maxdepth=8):
    """Relative-speed OR exact relative-support-plane certificate for all time.

    For any fixed unit axis, each simultaneous endpoint difference is affine
    in time. All segment-point differences are convex combinations of the four
    endpoint differences at each time, hence of all eight at both interval
    endpoints. A positive shared projection bound certifies the entire motion.
    The axis from midpoint closest features is merely a choice, not a sampling
    assumption. Remaining intervals use bounded conservative subdivision.
    """
    pairs,rr=m.pair.candidates(Q0,R,Q1);A0,B0=m.pair.endpoints(Q0);A1,B1=m.pair.endpoints(Q1);i,j=pairs.T;stack=[(A0[i],B0[i],A0[j],B0[j],A1[i],B1[i],A1[j],B1[j],rr[i]+rr[j],np.arange(len(pairs)),0)];fail=[];failureCount=0;depthUsed=0;tests=0;minimum=np.inf;planeCount=0
    while stack:
        a,b,c,d,aa,bb,cc,dd,radius,index,depth=stack.pop();depthUsed=max(depthUsed,depth);am=(a+aa)*.5;bm=(b+bb)*.5;cm=(c+cc)*.5;dm=(d+dd)*.5;distance,s,t=m.pair.closest(am,bm,cm,dm);gap=distance-radius-EPS;deltaA=aa-a;deltaB=bb-b;deltaC=cc-c;deltaD=dd-d;speed=np.maximum.reduce([np.linalg.norm(x-y,axis=1) for x in (deltaA,deltaB) for y in (deltaC,deltaD)]);bound=gap-.5*speed;tests+=len(index);ok=bound>0
        if ok.any():minimum=min(minimum,float(bound[ok].min()))
        bad=gap<=0;failureCount+=int(bad.sum())
        for ii in np.flatnonzero(bad)[:max(0,30-len(fail))]:fail.append({'segmentPair':pairs[index[ii]].tolist(),'physicalMidpointGapM':float(distance[ii]-radius[ii]),'reason':'midpoint physical overlap' if distance[ii]<radius[ii] else 'midpoint numerical clearance insufficient'})
        remaining=(~ok)&(~bad)
        if remaining.any():
            q=np.flatnonzero(remaining);axis=(am[q]+s[q,None]*(bm[q]-am[q]))-(cm[q]+t[q,None]*(dm[q]-cm[q]));axis/=np.maximum(distance[q],1e-30)[:,None]
            def support(x,y,z,w):return np.minimum(np.einsum('ij,ij->i',x,axis),np.einsum('ij,ij->i',y,axis))-np.maximum(np.einsum('ij,ij->i',z,axis),np.einsum('ij,ij->i',w,axis))
            plane=np.minimum(support(a[q],b[q],c[q],d[q]),support(aa[q],bb[q],cc[q],dd[q]))-radius[q]-EPS;good=plane>0
            if good.any():minimum=min(minimum,float(plane[good].min()));planeCount+=int(good.sum());remaining[q[good]]=False
        if depth==maxdepth:
            failureCount+=int(remaining.sum())
            for ix in index[remaining][:max(0,30-len(fail))]:fail.append({'segmentPair':pairs[ix].tolist(),'reason':'continuous certificate unresolved at bounded subdivision limit'})
        elif remaining.any():
            z=remaining;stack.append(tuple(x[z] for x in (a,b,c,d,am,bm,cm,dm,radius,index))+(depth+1,));stack.append(tuple(x[z] for x in (am,bm,cm,dm,aa,bb,cc,dd,radius,index))+(depth+1,))
    return {'sweptAABBPairs':len(pairs),'relativeBoundTests':tests,'relativeSupportPlaneCertificates':planeCount,'maximumSubdivisionDepth':depthUsed,'minimumCertifiedPairBoundM':float(minimum) if np.isfinite(minimum) else None,'unqualifiedPairsOrIntervals':failureCount,'examples':fail,'status':'PASS_ALL_ACTUAL_LINEAR_MOVING_CAPSULE_PAIRS' if not failureCount else 'FAIL_OR_UNRESOLVED'}

def hull_plane_bound(A,B,C,D,radius,tree,tri):
    hull=np.array((A,B,C,D),dtype='f8');centre=hull.mean(0);reach=float(np.linalg.norm(hull-centre,axis=1).max());found=tree.find_nearest_range(Vector(centre),reach+radius+EPS+1e-5)
    if not found:return .000005,'swept_range_empty'
    ids=np.array(sorted({x[2] for x in found}),'i4');faces=tri[ids];normal=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);length=np.linalg.norm(normal,axis=1)
    if np.any(length<1e-20):return None,'degenerate_near_triangle'
    normal/=length[:,None];signed=np.einsum('ijk,ik->ij',hull[None]-faces[:,0,None],normal);bound=np.maximum(signed.min(1),-signed.max(1))-radius-EPS
    if np.all(bound>0):return min(float(bound.min()),.000005),'all_near_triangle_separating_planes'
    return None,'needs_refinement'

def body_segment(A0,B0,A1,B1,radius,tree,tri,depth=0):
    bound,method=hull_plane_bound(A0,B0,A1,B1,radius,tree,tri)
    if bound is not None:return True,bound,depth,method
    A=(A0+A1)*.5;B=(B0+B1)*.5;da=tree.find_nearest(Vector(A))[3];db=tree.find_nearest(Vector(B))[3];gap,kind=m.g.k.f.flowcheck.cap.segment_test(A,B,da,db,radius,tree,tri);movement=.5*max(np.linalg.norm(A1-A0),np.linalg.norm(B1-B0))
    if gap-movement>0:return True,float(gap-movement),depth,'subdivided_relative_body_bound'
    if gap<=0 or depth==8:return False,float(gap-movement),depth,'actual_cross_or_unresolved_'+kind
    left=body_segment(A0,B0,A,B,radius,tree,tri,depth+1)
    if not left[0]:return left
    right=body_segment(A,B,A1,B1,radius,tree,tri,depth+1);return right[0],min(left[1],right[1]),max(left[2],right[2]),right[3]

def body_interval(Q0,Q1,R,tree,tri):
    # The first real root segment is constant and tested separately outside its
    # explicit radius-derived anatomical joining collar. Every other segment.
    mid=(Q0[:,1:].astype('f8')+Q1[:,1:].astype('f8'))*.5;dist=np.array([tree.find_nearest(Vector(p))[3] for p in mid.reshape(-1,3)]).reshape(mid.shape[:2]);A0=Q0[:,1:-1].reshape(-1,3).astype('f8');B0=Q0[:,2:].reshape(-1,3).astype('f8');A1=Q1[:,1:-1].reshape(-1,3).astype('f8');B1=Q1[:,2:].reshape(-1,3).astype('f8');r=np.maximum(R[:,1:-1],R[:,2:]).ravel();length=np.linalg.norm((A0+A1-B0-B1)*.5,axis=1);move=.5*np.maximum(np.linalg.norm(A1-A0,axis=1),np.linalg.norm(B1-B0,axis=1));bound=(dist[:,:-1].ravel()+dist[:,1:].ravel()-length)*.5-r-EPS-move;simple=bound>0;minimum=float(bound[simple].min()) if simple.any() else math.inf;methods={'direct_lipschitz':int(simple.sum())};fail=[];depth=0
    for index in np.flatnonzero(~simple):
        ok,gap,d,method=body_segment(A0[index],B0[index],A1[index],B1[index],float(r[index]),tree,tri);methods[method]=methods.get(method,0)+1;depth=max(depth,d)
        if ok:minimum=min(minimum,gap)
        else:fail.append({'curve':int(index//(Q0.shape[1]-2)),'segment':int(index%(Q0.shape[1]-2)+1),'unqualifiedBoundM':gap,'method':method})
    return {'testedSegments':len(A0),'unqualifiedIntervals':len(fail),'maximumSubdivisionDepth':depth,'minimumCertifiedSeparationBoundM':minimum if np.isfinite(minimum) else None,'methods':methods,'examples':fail[:20]}

def main():
    tick=time.time();ref=json.loads((E/'b-build-summary.json').read_text());source=Path(ref['output']);assert m.sha(source)==ref['outputSha256'];raw=np.load(E/ref['motionData']);Q=raw['positions'];R=raw['radii'];assert Q.shape==(481,61,128,3);assert np.isfinite(Q).all();bpy.ops.wm.open_mainfile(filepath=str(source));hair=bpy.data.objects[m.NAME];carrier=bpy.data.objects[ref['carrier']];keys=carrier.data.shape_keys;assert keys.use_relative and len(keys.key_blocks)==len(Q)
    for k,key in enumerate(keys.key_blocks):
        arr=np.empty(Q[k].size,'f4');key.data.foreach_get('co',arr);assert np.array_equal(arr,Q[k].ravel()),('Persisted pose mismatch',k)
        if k:assert key.relative_key==keys.key_blocks[0]
    action=keys.animation_data.action;curves=[]
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:curves.extend(bag.fcurves)
    assert len(curves)==480;peaks={0:np.float32(1.)};times={}
    for fc in curves:
        assert not fc.modifiers and fc.extrapolation=='CONSTANT';k=int(fc.data_path.split('AFN62_STATE_')[1].split('"')[0]);points=list(fc.keyframe_points);assert len(points)==3 and all(p.interpolation=='LINEAR' for p in points);assert [p.co.y for p in points]==[0.,1.,0.];times[k]=[np.float32(p.co.x) for p in points];peaks[k]=times[k][1]
    for k in range(1,481):
        assert times[k][0]==peaks[k-1]
        if k<480:assert times[k][2]==peaks[k+1]
    errors=[]
    for state in (0.,1.,60.,60.5,120.,162.,162.5,264.,264.5,479.,480.):
        timeFrame=1+state/10;frame=int(timeFrame);bpy.context.scene.frame_set(frame,subframe=timeFrame-frame);bpy.context.view_layer.update();a=int(state);expected=Q[a] if a==state else (Q[a].astype('f8')+Q[a+1])*.5;actual=flat(hair).reshape(61,128,3);error=float(np.linalg.norm(actual-expected,axis=2).max());assert error<EPS,(state,error);errors.append({'state':state,'maximumActualNodeErrorM':error})
    d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rr=np.empty(R.size,'f4');d.attributes['radius'].data.foreach_get('value',rr);assert np.array_equal(rr,R.ravel());assert all(c.points_length==128 for c in d.curves);assert all(v.value==1 for v in d.attributes['curve_type'].data);ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];assert ctrl.animation_data.action is None and ctrl['blink_left']==ctrl['blink_right']==0.;assert ctrl['AFN62_PreservedFaceAction'] in bpy.data.actions
    names=list(json.loads((E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values())
    for n in names:
        o=bpy.data.objects[n];assert not o.animation_data or o.animation_data.action is None;assert o.data.shape_keys.animation_data.action is None
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();parts=[m.g.k.mesh(bpy.data.objects[n]) for n in names];V,T,mi,fi=m.g.k.join(parts);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);body=parts[4];cache=np.load(E.parent/'r0061-surface-flow-groom/actual-body-render-surface.npz');assert np.array_equal(body['V'],cache['P']) and np.array_equal(body['T'],cache['T']);bodyTree=BVHTree.FromPolygons(body['V'].tolist(),body['T'].tolist(),all_triangles=True)
    bpy.context.scene.frame_set(49);bpy.context.view_layer.update();assert all(np.array_equal(m.g.k.mesh(bpy.data.objects[n])['V'],row['V']) for n,row in zip(names,parts));assert np.array_equal(Q[:,:,:2],np.broadcast_to(Q[0,:,:2],Q[:,:,:2].shape));author=np.load(E/'a-packed-bundle-authoring.npz');root=[]
    for c,(record,points) in enumerate(zip(author['rootRecords'],Q[0])):
        A=body['V'][body['T'][int(record[0])]];normal=np.cross(A[1]-A[0],A[2]-A[0]);normal/=np.linalg.norm(normal);direction=points[1].astype('f8')-points[0];length=np.linalg.norm(direction);direction/=length;cosine=float(direction@normal);assert cosine>.1;collar=(2*float(R[c,0])+EPS)/cosine;assert collar<length;start=points[0]+direction*collar;state=m.g.k.f.flowcheck.cap.solid.classify(bodyTree,body['V'][body['T']],Vector(start));assert state=='outside';da=tree.find_nearest(Vector(start))[3];db=tree.find_nearest(Vector(points[1]))[3];gap,method=m.g.k.f.flowcheck.cap.segment_test(start,points[1],da,db,float(max(R[c,:2])),tree,tri);assert gap>0;root.append({'curve':c,'nativeFace':int(record[1]),'radiusDerivedJoinArcM':collar,'remainingFirstSegmentBoundM':gap,'outsideClosedBodyAnchor':True})
    m.save('b-native-readback.json',{'source':str(source),'sha256':m.sha(source),'all481NativePoseCoordinateArraysExact':True,'all480LinearTriangleWeightCurvesValidated':True,'nativeSampleChecks':errors,'maximumNativeSampleErrorM':max(x['maximumActualNodeErrorM'] for x in errors),'actualRadiiAndPOLYTypesExact':True,'fixedNeutralBodyExactToQualifiedR60RenderSurface':True,'faceActionRetainedUnboundForThisFixedHeadTest':True,'constantRootJoinSegments':True,'rootJoins':root,'anatomicalRootLumenOrFullHairPhysicsAccepted':False})
    rows=[];minimumBody=math.inf;minimumSelf=math.inf
    for k in range(480):
        selfResult=self_interval(Q[k],Q[k+1],R);bodyResult=body_interval(Q[k],Q[k+1],R,tree,tri);rows.append({'interval':k,'timeSeconds':[k/240,(k+1)/240],'self':selfResult,'body':bodyResult});okay=selfResult['status'].startswith('PASS') and bodyResult['unqualifiedIntervals']==0
        if selfResult['minimumCertifiedPairBoundM'] is not None:minimumSelf=min(minimumSelf,selfResult['minimumCertifiedPairBoundM'])
        if bodyResult['minimumCertifiedSeparationBoundM'] is not None:minimumBody=min(minimumBody,bodyResult['minimumCertifiedSeparationBoundM'])
        if not okay:
            m.save('b-continuous-contact-verification.json',{'status':'FAIL_OR_UNRESOLVED','source':str(source),'sha256':m.sha(source),'testedIntervals':len(rows),'requiredIntervals':480,'intervals':rows,'numericalAllowanceM':EPS,'scope':'Actual61savedshafts, not guides; complete motion not certified.','seconds':time.time()-tick});raise RuntimeError(('Actual continuous shaft gate failed',k,selfResult['status'],bodyResult['unqualifiedIntervals']))
        if k%20==0:
            print('R62_CCD',k,480,'selfPairs',selfResult['sweptAABBPairs'],'bodyBound',bodyResult['minimumCertifiedSeparationBoundM'],flush=True);m.save('continuous-check-progress.json',{'sourceSha256':m.sha(source),'certifiedIntervals':len(rows),'requiredIntervals':480,'status':'RUNNING_NOT_COMPLETE','seconds':time.time()-tick})
    m.save('b-continuous-contact-verification.json',{'status':'PASS_COMPLETE_FIXED_HEAD_61_SHAFT_LINEAR_CACHE_SCOPE','source':str(source),'sha256':m.sha(source),'testedIntervals':480,'intervalDT':1/240,'durationSeconds':2.,'actualFibres':61,'actualPointsPerFibre':128,'numericalAllowanceM':EPS,'rootJoinScope':'Each fixed same-source follicle has a declared2radius+numeric collar; all remaining first-shaft portions tested. Follicle lumen/tissue anatomy remains unaccepted.','bodyMethod':'Actual complete body/optical triangles; endpoint-displacement Lipschitz bound or four-endpoint swept-hull separation against all nearby triangle planes, bounded subdivision when necessary. Closed-body anchors, static neutral source exact.','selfMethod':'All moving shaft capsule pairs via complete swept-AABB broadphase, exact finite-segment distances and endpoint-relative-displacement bounds; bounded time subdivision. Connected same-strand joints only excluded.','minimumCertifiedBodyLowerBoundM':minimumBody,'minimumRefinedSelfCandidateLowerBoundM':minimumSelf,'exactGlobalSignedMinimumM':None,'intervals':rows,'notAccepted':['Full hairstyle','Head/cloth motion or independently moving facial components','Follicle lumen/tissue thickness','Calibrated torsion/friction/aerodynamics','Actual Aevrynd runtime/LOD/performance'],'seconds':time.time()-tick});print('R62_COMPLETE_SHAFT_CCD_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
