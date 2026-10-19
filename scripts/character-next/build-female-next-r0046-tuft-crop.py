"""B: explicit free 3D cubic tufts, after surface-track crop looked painted.
Only root/end locations use actual skin; the shaft volume is independently
authored. No old curtain offsets, artist-data transfer or all-path skin hug.
"""
import bpy,importlib.util,time
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('crop46A',Path(__file__).with_name('build-female-next-r0046-textured-crop.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
BASE=a.E;a.E=BASE/'b-explicit-tufts';a.E.mkdir(exist_ok=True);a.OUT=a.S/'aevrynd-female-next-r0046-b-explicit-tuft-crop.blend';originalSave=a.save
def save(n,x):
    if n=='round-contract.json':
        x.update(revision='female-next-r0046-b',candidateCount=2,priorCandidateDecision='A is visually rejected: near-surface short paths remain a flat painted cap. Do not run its full expensive contact gates.',method='Explicit independent3D cubic tufts with root,exit,mid-volume and free-end controls; source skin only anchors root/end. Region and tuft controls set crown/fringe/temple/ear/nape lengths and distinct raised inner/outer volumes. No all-path skin track or offsets of old bob.',hypothesis='A readable3D crown and feathered fringe/temple/nape silhouette can emerge from independently raised curved tufts, without the flat shell of candidate A.',reference='Short textured crop silhouette references only, not copied mesh/pixels, own authored cubic control data on unchanged native roots.')
    originalSave(n,x)
a.save=save
def path(root,index,part,tree,V,T):
    hit,n,tid,d=tree.find_nearest(Vector(root));foot=np.array(hit);N=a.norm(np.array(n));tri=V[T[tid]];co=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),foot-tri[0],rcond=None)[0];bc=np.array((1-co.sum(),co[0],co[1]));assert bc.min()>-1e-3
    crown=float(a.smooth((root[2]-1.512)/.050));front=float(a.smooth((-root[1]-.025)/.065));nape=float(1-a.smooth((root[2]-1.465)/.032));phi=float(np.arctan2(root[0],-(root[1]+.015)));tuft=int(np.floor((phi+np.pi)/.24))*5+int(np.clip((root[2]-1.44)/.031,0,4));rng=np.random.default_rng(tuft+460001);clump=float(rng.uniform(-1,1));angle=float(rng.uniform(-.25,.25));rr=np.random.default_rng(index+460123);fine=float(rr.uniform(-1,1));length=(.012+.030*crown+.012*front*(1-nape)+.005*(1-crown)*(1-nape))*(1+.18*clump+.04*fine);lift=(.005+.022*crown)*(1+.22*clump);F=np.array((part*(.35+.55*front),.65*(1-front)+.25,-.65*(1-crown)-.18*front));F-=N*(F@N);F=a.norm(F);F=np.cos(angle)*F+np.sin(angle)*np.cross(N,F)
    q=foot.copy();lastN=N.copy();direction=F.copy()
    for j in range(18):
        direction-=lastN*(direction@lastN);direction=a.norm(direction);h,nn,_,_=tree.find_nearest(Vector(q+direction*(length/18)));q=np.array(h);lastN=a.norm(np.array(nn))
    end=q+lastN*(.0018+.0050*crown)*(1+.15*fine);side=a.norm(np.cross(lastN,direction));end+=side*.00035*fine
    p1=root+N*(.001+.005*crown)+F*(length*.14);p2=root*.35+end*.65+N*lift;u=np.linspace(0,1,128)[:,None];P=(1-u)**3*root+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end;P[0]=root
    region=0 if front>.6 and crown>.3 else 1 if crown>.5 else 4 if nape>.5 else 2 if abs(root[0])>.045 else 3
    return P,{'bodyTriangle':int(tid),'barycentric':bc.tolist(),'surfaceM':foot.tolist(),'rootOffsetWorldM':(root-foot).tolist(),'normal':N.tolist(),'targetCutLengthM':length,'region':region,'outerLayer':bool(clump>0),'tuft':tuft,'cubicControlsWorldM':[root.tolist(),p1.tolist(),p2.tolist(),end.tolist()],'maximumPlannedLiftM':lift}
a.path=path
if __name__=='__main__':a.main()
