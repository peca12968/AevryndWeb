"""Simultaneous finite-segment static contact relaxation; no follicle dropping.

All roots fixed. No per-hair greedy accept/lift sequence. This is an offline
groom authoring solver, not a dynamic hair simulation or engine implementation.
"""
import numpy as np
from itertools import combinations,product
def distances(A,B,C,D):
    u=B-A;v=D-C;w=A-C;aa=np.einsum('ij,ij->i',u,u);bb=np.einsum('ij,ij->i',u,v);cc=np.einsum('ij,ij->i',v,v);dd=np.einsum('ij,ij->i',u,w);ee=np.einsum('ij,ij->i',v,w);den=aa*cc-bb*bb
    ss=(bb*ee-cc*dd)/np.where(abs(den)>1e-28,den,1);tt=(aa*ee-bb*dd)/np.where(abs(den)>1e-28,den,1)
    valid=(abs(den)>1e-28)&(ss>=0)&(ss<=1)&(tt>=0)&(tt<=1);best=np.where(valid,np.linalg.norm(w+ss[:,None]*u-tt[:,None]*v,axis=1),np.inf);s=np.where(valid,ss,0.);t=np.where(valid,tt,0.)
    for st in (0.,1.):
        tq=np.clip((ee+st*bb)/np.maximum(cc,1e-30),0,1);d=np.linalg.norm(w+st*u-tq[:,None]*v,axis=1);m=d<best;best[m]=d[m];s[m]=st;t[m]=tq[m]
    for te in (0.,1.):
        sq=np.clip((te*bb-dd)/np.maximum(aa,1e-30),0,1);d=np.linalg.norm(w+sq[:,None]*u-te*v,axis=1);m=d<best;best[m]=d[m];s[m]=sq[m];t[m]=te
    return best,s,t
def controls():
    for a,c,d,expected in [([0,0,0],[.5,-1,0],[.5,1,0],0),([0,0,0],[0,1,0],[1,1,0],1),([0,0,0],[2,0,0],[3,0,0],1),([0,0,0],[.5,-1,2],[.5,1,2],2)]:
        got=distances(np.array([a],dtype='f8'),np.array([[1,0,0]],dtype='f8'),np.array([c],dtype='f8'),np.array([d],dtype='f8'))[0][0];assert abs(got-expected)<1e-12,(got,expected)
def candidates(P,R,margin=5e-6):
    A=P[:,:-1].reshape(-1,3);B=P[:,1:].reshape(-1,3);rad=np.maximum(R[:,:-1],R[:,1:]).ravel();lo=np.minimum(A,B)-rad[:,None]-margin;hi=np.maximum(A,B)+rad[:,None]+margin
    cell=.00065;L=np.floor(lo/cell).astype('i4');H=np.floor(hi/cell).astype('i4');grid={};pairs=set();n=P.shape[1]-1
    for i,(l,h) in enumerate(zip(L,H)):
        for key in product(*(range(l[j],h[j]+1) for j in range(3))):grid.setdefault(key,[]).append(i)
    for ids in grid.values():
        for i,j in combinations(ids,2):
            if i//n==j//n and abs(i-j)<=1:continue
            if np.all(hi[i]>=lo[j]) and np.all(hi[j]>=lo[i]):pairs.add((i,j))
    return np.array(sorted(pairs),dtype='i4').reshape(-1,2)
def contacts(P,R,margin=0.):
    ids=candidates(P,R,margin);A=P[:,:-1].reshape(-1,3);B=P[:,1:].reshape(-1,3);rad=np.maximum(R[:,:-1],R[:,1:]).ravel();i,j=ids.T
    dist,s,t=distances(A[i],B[i],A[j],B[j]);gap=dist-rad[i]-rad[j]
    return ids,gap,s,t
def solve(P,R,N,surface,max_iterations=55):
    controls();rest=P.copy();fixed=P[:,0].copy();history=[];size=P.shape[1];n=size-1;flat=P.reshape(-1,3);normal=N.reshape(-1,3);floor=surface.reshape(-1,3);radius=R.ravel();last=None
    for iteration in range(max_iterations):
        ids,gap,s,t=contacts(P,R,8e-6);bad=gap<4e-6;history.append({'iteration':iteration,'candidatePairs':len(ids),'belowDesignMargin':int(bad.sum()),'minimumCapsuleGapM':float(gap.min()) if len(gap) else None})
        if not np.any(bad):break
        ii,jj=ids[bad].T;s=s[bad];t=t[bad];vi=ii//n*size+ii%n;vj=jj//n*size+jj%n
        pa=(1-s[:,None])*flat[vi]+s[:,None]*flat[vi+1];pb=(1-t[:,None])*flat[vj]+t[:,None]*flat[vj+1];delta=pa-pb;d=np.linalg.norm(delta,axis=1);direction=delta/np.maximum(d[:,None],1e-12)
        tiny=d<1e-10
        if np.any(tiny):direction[tiny]=normal[vi[tiny]]*np.where((ii[tiny]%2)==0,1.,-1.)[:,None]
        ia=(vi%size)!=0;ib=(vj%size)!=0;den=ia*(1-s)**2+s*s+ib*(1-t)**2+t*t;step=(4e-6-gap[bad])/.95/np.maximum(den,1e-12)
        accum=np.zeros_like(flat);counts=np.zeros(len(flat))
        for vertices,weights,sign,movable in [(vi,1-s,1,ia),(vi+1,s,1,np.ones(len(vi),bool)),(vj,1-t,-1,ib),(vj+1,t,-1,np.ones(len(vj),bool))]:
            w=weights*movable;np.add.at(accum,vertices,direction*(sign*step*w)[:,None]);np.add.at(counts,vertices,(w>0).astype('f8'))
        flat+=.85*accum/np.maximum(counts[:,None],1.)
        # Preserve finite local skin clearance; full capsule/body verification
        # follows independently, so these tangent halfspaces are not a proof.
        depth=np.einsum('ij,ij->i',flat-floor,normal);flat+=normal*np.maximum(radius+25e-6-depth,0)[:,None];P[:,0]=fixed
        displacement=np.linalg.norm(P-rest,axis=2)
        if displacement.max()>.00065:break
    ids,gap,s,t=contacts(P,R,1e-6);return P,{'iterations':history,'remainingConservativeCapsuleOverlaps':int((gap<=1e-6).sum()),'minimumPairCapsuleGapM':float(gap.min()) if len(gap) else None,'maximumDisplacementM':float(np.linalg.norm(P-rest,axis=2).max()),'rootPositionsExact':bool(np.array_equal(P[:,0],fixed)),'maximumAllowedDisplacementM':.00065,'allFolliclesRetained':True,'staticAuthoringOnly':True}
