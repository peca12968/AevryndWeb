"""Own finite segment/capsule math and complete swept-AABB broad phase.

For this small method trial, every displayed shaft participates. A broad phase
is never reported as penetration. Connected joints of the SAME polyline are
legal; no distinct fibre pair or scalp/tie region is excluded.
"""
import numpy as np,itertools

def distance(A,B,C,D):
    u=B-A;v=D-C;w=A-C;a=np.einsum('ij,ij->i',u,u);b=np.einsum('ij,ij->i',u,v);c=np.einsum('ij,ij->i',v,v);d=np.einsum('ij,ij->i',u,w);e=np.einsum('ij,ij->i',v,w);den=a*c-b*b;safe=np.where(abs(den)>1e-26,den,1.)
    s=(b*e-c*d)/safe;t=(a*e-b*d)/safe;valid=(abs(den)>1e-26)&(s>=0)&(s<=1)&(t>=0)&(t<=1);best=np.where(valid,np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1),np.inf)
    for P in (A,B):
        tt=np.clip(np.einsum('ij,ij->i',P-C,v)/np.maximum(c,1e-30),0,1);best=np.minimum(best,np.linalg.norm(P-C-tt[:,None]*v,axis=1))
    for P in (C,D):
        ss=np.clip(np.einsum('ij,ij->i',P-A,u)/np.maximum(a,1e-30),0,1);best=np.minimum(best,np.linalg.norm(P-A-ss[:,None]*u,axis=1))
    return best

def closest(A,B,C,D):
    """Exact finite closest-point parameters as well as distances."""
    u=B-A;v=D-C;w=A-C;a=np.einsum('ij,ij->i',u,u);b=np.einsum('ij,ij->i',u,v);c=np.einsum('ij,ij->i',v,v);d=np.einsum('ij,ij->i',u,w);e=np.einsum('ij,ij->i',v,w);den=a*c-b*b;safe=np.where(abs(den)>1e-26,den,1.);s=(b*e-c*d)/safe;t=(a*e-b*d)/safe;valid=(abs(den)>1e-26)&(s>=0)&(s<=1)&(t>=0)&(t<=1);best=np.where(valid,np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1),np.inf)
    s=np.where(valid,s,0.);t=np.where(valid,t,0.)
    for P,ss in ((A,0.),(B,1.)):
        tt=np.clip(np.einsum('ij,ij->i',P-C,v)/np.maximum(c,1e-30),0,1);distance=np.linalg.norm(P-C-tt[:,None]*v,axis=1);mask=distance<best;best=np.minimum(best,distance);s=np.where(mask,ss,s);t=np.where(mask,tt,t)
    for P,tt in ((C,0.),(D,1.)):
        ss=np.clip(np.einsum('ij,ij->i',P-A,u)/np.maximum(a,1e-30),0,1);distance=np.linalg.norm(P-A-ss[:,None]*u,axis=1);mask=distance<best;best=np.minimum(best,distance);s=np.where(mask,ss,s);t=np.where(mask,tt,t)
    return best,s,t

def endpoints(Q):return Q[:,:-1].reshape(-1,3).astype('f8'),Q[:,1:].reshape(-1,3).astype('f8')

def axis_between(A,B,C,D):
    tangent=(B-A)+(D-C);tangent/=np.maximum(np.linalg.norm(tangent,axis=1),1e-30)[:,None];delta=((A+B)-(C+D))*.5;axis=delta-tangent*np.einsum('ij,ij->i',delta,tangent)[:,None];length=np.linalg.norm(axis,axis=1);small=length<1e-16;axis[small]=delta[small];length=np.linalg.norm(axis,axis=1);axis[length<1e-20]=np.array((1.,0,0));return axis/np.maximum(np.linalg.norm(axis,axis=1),1e-30)[:,None]

def plane_gap(A,B,C,D,radius,axis=None):
    """Exact support-plane lower bound for entire finite capsules."""
    if axis is None:axis=axis_between(A,B,C,D)
    middle=np.einsum('ij,ij->i',((A+B)-(C+D))*.5,axis);width=.5*(abs(np.einsum('ij,ij->i',B-A,axis))+abs(np.einsum('ij,ij->i',D-C,axis)));return abs(middle)-width-radius

def grid_candidates(Q,R,nextQ=None,cell=.002):
    A,B=endpoints(Q);radius=np.maximum(R[:,:-1],R[:,1:]).ravel().astype('f8')+.0000005
    lo=np.minimum(A,B);hi=np.maximum(A,B)
    if nextQ is not None:
        C,D=endpoints(nextQ);lo=np.minimum(lo,np.minimum(C,D));hi=np.maximum(hi,np.maximum(C,D))
    lo-=radius[:,None];hi+=radius[:,None];a=np.floor(lo/cell).astype('i8');b=np.floor(hi/cell).astype('i8');grid={};pairs=set();N=Q.shape[1]-1
    for i,(low,high) in enumerate(zip(a,b)):
        assert np.prod(high-low+1)<5000,'Unexpected swept segment box; reject explosive motion.'
        for key in itertools.product(*(range(int(low[j]),int(high[j])+1) for j in range(3))):
            bucket=grid.setdefault(key,[])
            for other in bucket:
                if i//N==other//N and abs(i-other)<=1:continue
                if np.all(lo[i]<=hi[other]) and np.all(lo[other]<=hi[i]):pairs.add((other,i))
            bucket.append(i)
    return np.array(sorted(pairs),dtype='i4').reshape(-1,2),radius-.0000005

def candidates(Q,R,nextQ=None,cell=.002):
    """Exact expanded-AABB sweep/prune, independent of fibre/guide grouping."""
    A,B=endpoints(Q);rr=np.maximum(R[:,:-1],R[:,1:]).ravel().astype('f8');lo=np.minimum(A,B);hi=np.maximum(A,B)
    if nextQ is not None:
        C,D=endpoints(nextQ);lo=np.minimum(lo,np.minimum(C,D));hi=np.maximum(hi,np.maximum(C,D))
    lo-=rr[:,None]+.0000005;hi+=rr[:,None]+.0000005
    score=(hi.max(0)-lo.min(0))/np.maximum(np.mean(hi-lo,axis=0),1e-12);axes=np.argsort(score)[::-1];axis=int(axes[0]);order=np.argsort(lo[:,axis],kind='stable').astype('i4');index=np.arange(len(order),dtype='i4');end=np.searchsorted(lo[order,axis],hi[order,axis],side='right');count=np.maximum(end-index-1,0).astype('i4');total=int(count.sum());assert total<2_000_000_000
    pi=np.repeat(index,count);starts=np.cumsum(count,dtype='i4')-count;pj=np.arange(total,dtype='i4')+np.repeat(index+1-starts,count);i=order[pi];j=order[pj];N=Q.shape[1]-1
    # Filter one scalar axis at a time before allocating further pair fields.
    for axis in axes[1:]:
        mask=(lo[i,axis]<=hi[j,axis])&(lo[j,axis]<=hi[i,axis]);i=i[mask];j=j[mask]
    mask=~((i//N==j//N)&(abs(i-j)<=1));pairs=np.sort(np.column_stack((i[mask],j[mask])),axis=1);pairs=pairs[np.lexsort((pairs[:,1],pairs[:,0]))]
    return pairs.astype('i4'),rr

def continuous_pair_bounds(Q0,Q1,R,maxdepth=8):
    """Certify linear motion with exact static distance and relative-speed bounds.

    All moving segments are affine in time. Any pair of points on them has a
    relative displacement bounded by the maximum of the four endpoint-relative
    displacements (convex weights). Midpoint distance minus half that bound is
    therefore conservative for the WHOLE interval, including arbitrary segment
    parameters. Subdivision refines the same motion, not simulation parameters.
    """
    pairs,rr=candidates(Q0,R,Q1);A0,B0=endpoints(Q0);A1,B1=endpoints(Q1);i,j=pairs.T;stack=[(A0[i],B0[i],A0[j],B0[j],A1[i],B1[i],A1[j],B1[j],rr[i]+rr[j],np.arange(len(pairs)),0)];fail=[];depthUsed=0;tests=0;minimum=np.inf
    while stack:
        a,b,c,d,aa,bb,cc,dd,radius,index,depth=stack.pop();depthUsed=max(depthUsed,depth);am=(a+aa)*.5;bm=(b+bb)*.5;cm=(c+cc)*.5;dm=(d+dd)*.5;gap=distance(am,bm,cm,dm)-radius-1e-6;deltaA=aa-a;deltaB=bb-b;deltaC=cc-c;deltaD=dd-d;speed=np.maximum.reduce([np.linalg.norm(x-y,axis=1) for x in (deltaA,deltaB) for y in (deltaC,deltaD)]);bound=gap-.5*speed;tests+=len(index);ok=bound>0
        if ok.any():minimum=min(minimum,float(bound[ok].min()))
        bad=gap<=0
        for ix in index[bad][:30]:fail.append({'segmentPair':pairs[ix].tolist(),'reason':'Actual midpoint capsule overlap or unresolved within1um'})
        remaining=(~ok)&(~bad)
        if depth==maxdepth:
            for ix in index[remaining][:30]:fail.append({'segmentPair':pairs[ix].tolist(),'reason':'Continuous bound unresolved at bounded subdivision limit'})
        elif remaining.any():
            z=remaining
            stack.append(tuple(x[z] for x in (a,b,c,d,am,bm,cm,dm,radius,index))+(depth+1,));stack.append(tuple(x[z] for x in (am,bm,cm,dm,aa,bb,cc,dd,radius,index))+(depth+1,))
    return {'sweptAABBPairs':len(pairs),'relativeBoundTests':tests,'maximumSubdivisionDepth':depthUsed,'minimumCertifiedPairBoundM':float(minimum) if np.isfinite(minimum) else None,'unqualifiedPairsOrIntervals':len(fail),'examples':fail[:30],'status':'PASS_ALL_ACTUAL_LINEAR_MOVING_CAPSULE_PAIRS' if not fail else 'FAIL_OR_UNRESOLVED'}

def static(Q,R):
    pairs,rr=candidates(Q,R);A,B=endpoints(Q);d=distance(A[pairs[:,0]],B[pairs[:,0]],A[pairs[:,1]],B[pairs[:,1]]) if len(pairs) else np.empty(0);gap=d-rr[pairs[:,0]]-rr[pairs[:,1]]-1e-6;bad=np.flatnonzero(gap<=0)
    return {'completeExpandedAABBPairs':len(pairs),'unqualifiedFinitePairs':len(bad),'minimumRefinedCandidateGapM':float(gap.min()) if len(gap) else None,'exactGlobalSignedMinimumM':None,'examples':[{'segments':pairs[i].tolist(),'centrelineDistanceM':float(d[i]),'sumRadiiM':float(rr[pairs[i]].sum()),'gapAfter1umM':float(gap[i])} for i in bad[:25]],'status':'PASS_ALL_ACTUAL_STATIC_SHAFT_CAPSULE_PAIRS' if not len(bad) else 'FAIL_OR_UNRESOLVED'}
