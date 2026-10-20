"""Actual independent shafts: stretch/bend, finite capsule self/body response.

This replaces the failed kinematic follow-frame assumption. Same61follicles,
render radii and timestep. Scalar-angle rods omit twist/friction/calibration.
Closest body planes accelerate response only; exact shaft CCD is independent.
"""
from pathlib import Path
import bpy,numpy as np,time,math,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('independent62',Path(__file__).with_name('build-female-next-r0062-packed-bundle.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
sp=importlib.util.spec_from_file_location('owned62',m.R/'engine/character/physics/groom_xpbd_reference.py');eng=importlib.util.module_from_spec(sp);sp.loader.exec_module(eng)
DT=1/240;WARM=120;STEPS=480;ITER=16;SELF_GAP=.000003

def angles(x):
    u=x[:,:-2]-x[:,1:-1];v=x[:,2:]-x[:,1:-1];a=np.linalg.norm(u,axis=2);b=np.linalg.norm(v,axis=2);c=np.clip(np.einsum('ijk,ijk->ij',u,v)/(a*b),-1+1e-12,1-1e-12);ss=np.sqrt(np.maximum(1-c*c,1e-12));A=-(v/(a*b)[:,:,None]-c[:,:,None]*u/(a*a)[:,:,None])/ss[:,:,None];C=-(u/(a*b)[:,:,None]-c[:,:,None]*v/(b*b)[:,:,None])/ss[:,:,None]
    return np.arccos(c),np.stack((A,-A-C,C),axis=2)

def self_project(x,radii,w):
    pairs,_=m.pair.candidates(x,radii+SELF_GAP*.5);A,B=m.pair.endpoints(x);physical=np.maximum(radii[:,:-1],radii[:,1:]).ravel();i,j=pairs.T;distance,s,t=m.pair.closest(A[i],B[i],A[j],B[j]);gap=distance-physical[i]-physical[j];bad=np.flatnonzero(gap<SELF_GAP);vertices=x.reshape(-1,3);weights=w.ravel();N=x.shape[1];corrections=0
    # Exact finite features, sequential only for the actual active contacts.
    for p in bad:
        ia=int(i[p]);ib=int(j[p]);ci,si=divmod(ia,N-1);cj,sj=divmod(ib,N-1);ids=np.array((ci*N+si,ci*N+si+1,cj*N+sj,cj*N+sj+1));aa,bb,cc,dd=vertices[ids];d,ss,tt=m.pair.closest(aa[None],bb[None],cc[None],dd[None]);d=float(d[0]);s0=float(ss[0]);t0=float(tt[0]);target=physical[ia]+physical[ib]+SELF_GAP
        if d>=target:continue
        normal=(aa+s0*(bb-aa))-(cc+t0*(dd-cc))
        if d<1e-12:
            normal=np.cross(bb-aa,dd-cc)
            if np.linalg.norm(normal)<1e-12:normal=np.cross(bb-aa,np.array((1.,.371,.193)))
            normal/=max(np.linalg.norm(normal),1e-20)
        else:normal/=d
        factors=np.array((1-s0,s0,-(1-t0),-t0));den=float(np.sum(weights[ids]*factors*factors));assert den>0,'Infeasible fixed-root contact.';dl=(target-d)/den;vertices[ids]+=weights[ids,None]*factors[:,None]*normal[None]*dl;corrections+=1
    return corrections,float(gap.min()) if len(gap) else np.inf

def main():
    tick=time.time();raw=np.load(m.E/'a-packed-bundle-authoring.npz');rest=raw['positions'].astype('f8');radii=raw['radii'].astype('f8');F,N=rest.shape[:2];ds=np.linalg.norm(np.diff(rest,axis=1),axis=2);density=1300.;young=3e9;r=.000035;EA=young*math.pi*r*r;EI=young*math.pi*r**4/4;mass=density*math.pi*r*r*np.concatenate((ds,ds[:,-1:]),axis=1);w=1/mass;w[:,:3]=0;restAngle,_=angles(rest);compliance=((ds[:,:-1]+ds[:,1:])*.5)/EI;support=np.maximum(np.concatenate((ds[:,:1],ds),axis=1),np.concatenate((ds,ds[:,-1:]),axis=1))*.5+np.concatenate((np.maximum(radii[:,:-1],radii[:,1:]),radii[:,-1:]),axis=1)+.00005
    cache=np.load(m.R/'Evidence/character-female-next/r0061-surface-flow-groom/actual-body-render-surface.npz');P=cache['P'];T=cache['T'];tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True);x=rest.copy();velocity=np.zeros_like(x);planeNormal=np.zeros_like(x);planePoint=np.zeros_like(x);cachePosition=x.copy();cacheDistance=np.zeros((F,N));dynamic=np.broadcast_to(np.arange(N)[None]>=3,(F,N));bodyCorrections=0;selfCorrections=0;maximumStrain=0.;maximumSpeed=0.;states=[];worstFinalResidual=0.
    def update_planes():
        nonlocal cachePosition,cacheDistance,planeNormal,planePoint
        # Unsigned nearest-distance Lipschitz exclusion only accelerates far
        # response points. It never serves as inside/outside or CCD acceptance.
        moved=np.linalg.norm(x-cachePosition,axis=2);query=dynamic&(cacheDistance-moved<=support+.003)
        for fi,j in np.argwhere(query):
            point,normal,ti,distance=tree.find_nearest(Vector(x[fi,j]));planePoint[fi,j]=point;planeNormal[fi,j]=normal;cacheDistance[fi,j]=distance;cachePosition[fi,j]=x[fi,j]
    def body_project():
        nonlocal bodyCorrections
        gap=np.einsum('ijk,ijk->ij',x-planePoint,planeNormal)-support;active=dynamic&(gap<0)&(np.linalg.norm(planeNormal,axis=2)>.5);x[active]-=planeNormal[active]*gap[active,None];bodyCorrections+=int(active.sum());return float(max(0,-gap[dynamic].min()))
    for step in range(WARM+STEPS+1):
        if step>=WARM:states.append(x.astype('f4').copy())
        if step==WARM+STEPS:break
        old=x.copy();t=(step-WARM)*DT;gust=0. if t<.25 or t>1.10 else math.sin(math.pi*(t-.25)/.85)**2;air=np.array((.30*gust,-1.50*gust,0.));tangent=np.concatenate((np.diff(x,axis=1),x[:,-1:]-x[:,-2:-1]),axis=1);tangent/=np.linalg.norm(tangent,axis=2)[:,:,None];relative=air[None,None]-velocity;transverse=relative-tangent*np.einsum('ijk,ijk->ij',relative,tangent)[:,:,None];force=.5*1.2*1.1*(2*r)*np.concatenate((ds,ds[:,-1:]),axis=1)[:,:,None]*np.linalg.norm(transverse,axis=2)[:,:,None]*transverse;velocity*=math.exp(-DT*1.2);x+=DT*velocity+DT*DT*(np.array((0.,0.,-9.81))+force/mass[:,:,None]);x[:,:3]=rest[:,:3];stretchLambda=np.zeros_like(ds);bendLambda=np.zeros_like(restAngle);update_planes()
        for iteration in range(ITER):
            for color in range(3):
                value,grad=angles(x);ids=np.arange(color,N-2,3);ww=w[:,ids[:,None]+np.arange(3)];gg=grad[:,ids];den=np.sum(ww*np.einsum('ijkl,ijkl->ijk',gg,gg),axis=2);alpha=compliance[:,ids]/(DT*DT);dl=(-(value[:,ids]-restAngle[:,ids])-alpha*bendLambda[:,ids])/(den+alpha);bendLambda[:,ids]+=dl;x[:,ids[:,None]+np.arange(3)]+=ww[:,:,:,None]*dl[:,:,None,None]*gg
            eng.coupled_stretch(x,w,ds,stretchLambda,ds/EA,DT)
            if iteration%4==3:body_project();count,gap=self_project(x,radii,w);selfCorrections+=count
            x[:,:3]=rest[:,:3]
        # Fresh actual response planes and fixed residual convergence gate.
        update_planes()
        for correction in range(64):
            eng.coupled_stretch(x,w,ds,stretchLambda,ds/EA,DT);bodyViolation=body_project();count,gap=self_project(x,radii,w);selfCorrections+=count;x[:,:3]=rest[:,:3];strain=float(np.max(abs(np.linalg.norm(np.diff(x,axis=1),axis=2)/ds-1)))
            if strain<.001 and count==0 and bodyViolation<1e-6:break
        worstFinalResidual=max(worstFinalResidual,strain);maximumStrain=max(maximumStrain,strain);velocity=(x-old)/DT;velocity[:,:3]=0;maximumSpeed=max(maximumSpeed,float(np.linalg.norm(velocity,axis=2).max()));assert np.isfinite(x).all() and np.linalg.norm(x-rest,axis=2).max()<.6;assert strain<.02,('Independent rod length gate failed',step,strain)
        if step%30==0:print('R62_INDEPENDENT',step,WARM+STEPS,'strain',strain,'self',selfCorrections,'body',bodyCorrections,flush=True)
    Q=np.array(states);np.savez_compressed(m.E/'c-independent-shaft-motion.npz',positions=Q,radii=radii.astype('f4'),dt=DT);m.save('c-independent-simulation-report.json',{'model':'61independent uniform-radius scalar-angle XPBD rods; actual tapered capsule contacts, own coupled-stretch engine reference, explicit finite segment self constraints. No kinematic guide-follow display assumption.','stateCount':len(Q),'dt':DT,'warmupSteps':WARM,'durationSeconds':STEPS*DT,'youngAssumptionPa':young,'densityAssumptionKgM3':density,'materialAndDragCalibrated':False,'maximumRelativeLengthError':maximumStrain,'maximumPointSpeedMps':maximumSpeed,'bodyPlaneResponseCorrections':bodyCorrections,'actualCapsuleSelfCorrections':selfCorrections,'selfDesignStandOffM':SELF_GAP,'bodyResponseSupport':'Actual max radius + half rest segment length +50um; conservative response only. Exact whole-motion gates remain independent.','fullDisplayBodySelfContinuousVerification':'PENDING','torsionFrictionCalibrationRuntime':'NOT_IMPLEMENTED_OR_NOT_TESTED','seconds':time.time()-tick});print('R62_INDEPENDENT_CACHE_READY',time.time()-tick,maximumStrain,selfCorrections,flush=True)
if __name__=='__main__':main()
