"""Own bounded guide-level XPBD prototype with actual packed follow fibres.

Distance and scalar turning-angle compliance, gravity, approximate transverse
cylinder drag and a conservative bundle/body contact envelope. Not a full
Cosserat/DER model: independent fibre motion, torsion, friction and calibrated
material/aerodynamic response remain absent. Finite display/continuous gates
are independent of the guide/contact model.
"""
from pathlib import Path
import bpy,numpy as np,math,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('packed62sim',Path(__file__).with_name('build-female-next-r0062-packed-bundle.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E;DT=1/240;DURATION=2.;ITER=16;WARM=120
sp=importlib.util.spec_from_file_location('ownedEngineStretch62',m.R/'engine/character/physics/groom_xpbd_reference.py');engine=importlib.util.module_from_spec(sp);sp.loader.exec_module(engine)

def angle_grad(x,i):
    u=x[i]-x[i+1];v=x[i+2]-x[i+1];a=np.linalg.norm(u);b=np.linalg.norm(v);c=float(np.clip((u@v)/(a*b),-1+1e-12,1-1e-12));ss=math.sqrt(max(1-c*c,1e-12))
    A=-(v/(a*b)-c*u/(a*a))/ss;C=-(u/(a*b)-c*v/(b*b))/ss
    return math.acos(c),np.array((A,-A-C,C))

def all_angles(x):
    u=x[:-2]-x[1:-1];v=x[2:]-x[1:-1];a=np.linalg.norm(u,axis=1);b=np.linalg.norm(v,axis=1);c=np.clip(np.einsum('ij,ij->i',u,v)/(a*b),-1+1e-12,1-1e-12);ss=np.sqrt(np.maximum(1-c*c,1e-12));A=-(v/(a*b)[:,None]-c[:,None]*u/(a*a)[:,None])/ss[:,None];C=-(u/(a*b)[:,None]-c[:,None]*v/(b*b)[:,None])/ss[:,None]
    return np.arccos(c),np.stack((A,-A-C,C),axis=1)

def coupled_projection(x,w,ds,EA,angleCompliance,restAngle,minimumAngle,envelope,tree,lambdas):
    """One mass-weighted global XPBD linearization of all active constraints.

    Angle constraints are scaled by their rest dual length, with compliance
    scaled by length squared. This is algebraic conditioning, not softer hair.
    """
    N=len(x);nD=N-1;nB=N-2;dual=(ds[:-1]+ds[1:])*.5;edges=np.diff(x,axis=0);length=np.linalg.norm(edges,axis=1);direction=edges/length[:,None];angle,grad=all_angles(x);grad=grad*dual[:,None,None];turnC=(angle-restAngle)*dual
    barrierC=(angle-minimumAngle)*dual;activeB=np.flatnonzero((barrierC<0)|(lambdas['barrier']>0));activeB=activeB[np.any(w[activeB[:,None]+np.arange(3)]>0,axis=1)]
    contact=[]
    for j in range(3,N):
        hit,n,fi,distance=tree.find_nearest(Vector(x[j]));normal=np.array(n);support=envelope[j]+max(ds[max(0,j-1):min(N-1,j+1)])*.5+.00005;gap=float((x[j]-np.array(hit))@normal-support)
        if gap<0 or lambdas['contact'][j]>0:contact.append((j,gap,normal))
    count=nD+nB+len(activeB)+len(contact);J=np.zeros((count,N,3));C=np.empty(count);alpha=np.zeros(count);old=np.zeros(count)
    ii=np.arange(nD);J[ii,ii]=-direction;J[ii,ii+1]=direction;C[:nD]=length-ds;alpha[:nD]=(ds/EA)/(DT*DT);old[:nD]=lambdas['stretch']
    ii=np.arange(nB);rows=nD+ii
    for local in range(3):J[rows,ii+local]=grad[:,local]
    C[nD:nD+nB]=turnC;alpha[nD:nD+nB]=angleCompliance*dual**2/(DT*DT);old[nD:nD+nB]=lambdas['bend']
    offset=nD+nB
    for row,j in enumerate(activeB):
        J[offset+row,j:j+3]=grad[j];C[offset+row]=barrierC[j];old[offset+row]=lambdas['barrier'][j]
    offset+=len(activeB)
    for row,(j,gap,normal) in enumerate(contact):J[offset+row,j]=normal;C[offset+row]=gap;old[offset+row]=lambdas['contact'][j]
    flat=J.reshape(count,-1);inverse=np.repeat(w,3);A=(flat*inverse[None])@flat.T;A.flat[::count+1]+=alpha;rhs=-C-alpha*old
    dl=np.linalg.solve(A,rhs);new=old+dl
    # Clamp multipliers for true inequality constraints. Active-set removal is
    # followed by the next global projection; actual residuals remain gated.
    inequality=np.arange(nD+nB,count);new[inequality]=np.maximum(new[inequality],0);dl=new-old;x+=((flat.T@dl)*inverse).reshape(N,3)
    lambdas['stretch']=new[:nD];lambdas['bend']=new[nD:nD+nB];lambdas['barrier'][activeB]=new[nD+nB:offset]
    for row,(j,gap,n) in enumerate(contact):lambdas['contact'][j]=new[offset+row]
    return len(contact)

def main():
    start=time.time();raw=np.load(E/'a-packed-bundle-authoring.npz');rest=raw['guide'].copy();N=len(rest);ds=np.linalg.norm(np.diff(rest,axis=0),axis=1);arc=np.r_[0,np.cumsum(ds)];nF=len(raw['hexXY']);radius=.000035;density=1300.;young=3e9;EA=nF*young*math.pi*radius**2;EI=nF*young*math.pi*radius**4/4;mass=nF*density*math.pi*radius**2*np.r_[ds,ds[-1]];w=1/mass;w[:3]=0.;restAngle=np.array([angle_grad(rest,i)[0] for i in range(N-2)]);angleCompliance=((ds[:-1]+ds[1:])*.5)/EI
    envelope=4*(.00018+(.00065-.00018)*np.exp(-arc/.015))+radius
    # A finite bundle cannot bend through its own thickness. This geometric
    # barrier is a constraint, not shrinking/deleting colliding display fibres.
    maxTurn=np.minimum(.45,.18*np.r_[ds,ds[-1]]/envelope);minimumAngle=math.pi-maxTurn[1:-1]
    cache=np.load(m.R/'Evidence/character-female-next/r0061-surface-flow-groom/actual-body-render-surface.npz');P=cache['P'];T=cache['T'];tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True)
    x=rest.copy();velocity=np.zeros_like(x);guide=[];contacts=0;maximumStrain=0.;maximumSpeed=0.;maximumTurn=0.
    total=WARM+int(DURATION/DT)
    for step in range(total+1):
        t=(step-WARM)*DT
        if step>=WARM:guide.append(x.astype('f4').copy())
        if step==total:break
        old=x.copy();tangent=np.vstack((np.diff(x,axis=0),x[-1]-x[-2]));tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        gust=0. if t<.25 or t>1.10 else math.sin(math.pi*(t-.25)/.85)**2
        air=np.array((.30*gust,-1.50*gust,0.));relative=air[None]-velocity;crossflow=relative-tangent*np.einsum('ij,ij->i',relative,tangent)[:,None]
        force=.5*1.2*1.1*(2*radius)*nF*np.r_[ds,ds[-1]][:,None]*np.linalg.norm(crossflow,axis=1)[:,None]*crossflow
        acceleration=np.array((0.,0.,-9.81))+force/mass[:,None];velocity*=math.exp(-DT*1.2);x+=DT*velocity+DT*DT*acceleration;x[:3]=rest[:3];lambdas={'stretch':np.zeros(N-1),'bend':np.zeros(N-2),'barrier':np.zeros(N-2),'contact':np.zeros(N)}
        for iteration in range(ITER):
            # Retained Aevrynd whole-chain distance solve, not the rejected
            # under-resolved local edge projection or dense Newton step.
            for color in range(3):
                angle,grad=all_angles(x);ids=np.arange(color,N-2,3);ww=w[ids[:,None]+np.arange(3)];gg=grad[ids];den=np.sum(ww*np.einsum('ijk,ijk->ij',gg,gg),axis=1);alpha=angleCompliance[ids]/(DT*DT);dl=(-(angle[ids]-restAngle[ids])-alpha*lambdas['bend'][ids])/(den+alpha);lambdas['bend'][ids]+=dl;x[ids[:,None]+np.arange(3)]+=ww[:,:,None]*dl[:,None,None]*gg
                angle,grad=all_angles(x);constraint=angle[ids]-minimumAngle[ids];active=(constraint<0)|(lambdas['barrier'][ids]>0);ii=ids[active];ww=w[ii[:,None]+np.arange(3)];gg=grad[ii];den=np.sum(ww*np.einsum('ijk,ijk->ij',gg,gg),axis=1);dl=-(angle[ii]-minimumAngle[ii])/np.maximum(den,1e-20);new=np.maximum(0,lambdas['barrier'][ii]+dl);dl=new-lambdas['barrier'][ii];lambdas['barrier'][ii]=new;x[ii[:,None]+np.arange(3)]+=ww[:,:,None]*dl[:,None,None]*gg
            engine.coupled_stretch(x[None],w[None],ds[None],lambdas['stretch'][None],(ds/EA)[None],DT)
            if iteration%4==3:
                for j in range(3,N):
                    hit,n,fi,distance=tree.find_nearest(Vector(x[j]));support=envelope[j]+max(ds[max(0,j-1):min(N-1,j+1)])*.5+.00005
                    if (x[j]-np.array(hit))@np.array(n)<support:x[j]=np.array(hit)+np.array(n)*support;contacts+=1
            x[:3]=rest[:3]
        # Convergence, not parameter trials: solve coupled contact/length to a
        # fixed residual bound, with a bounded cap and the same hard gate.
        for correction in range(64):
            engine.coupled_stretch(x[None],w[None],ds[None],lambdas['stretch'][None],(ds/EA)[None],DT);x[:3]=rest[:3];remaining=0
            for j in range(3,N):
                hit,n,fi,distance=tree.find_nearest(Vector(x[j]));support=envelope[j]+max(ds[max(0,j-1):min(N-1,j+1)])*.5+.00005;gap=float((x[j]-np.array(hit))@np.array(n)-support)
                if gap<0:x[j]-=np.array(n)*gap;contacts+=1;remaining=max(remaining,-gap)
            residual=float(np.max(abs(np.linalg.norm(np.diff(x,axis=0),axis=1)/ds-1)))
            if residual<.001 and remaining<1e-6:break
        velocity=(x-old)/DT;velocity[:3]=0.;strain=float(np.max(abs(np.linalg.norm(np.diff(x,axis=0),axis=1)/ds-1)));maximumStrain=max(maximumStrain,strain);maximumSpeed=max(maximumSpeed,float(np.linalg.norm(velocity,axis=1).max()));maximumTurn=max(maximumTurn,max(math.pi-angle_grad(x,j)[0] for j in range(N-2)))
        assert np.isfinite(x).all() and np.linalg.norm(x-rest,axis=1).max()<.6,'Explosive guide; reject method before display expansion.'
        assert strain<.02,('Coupled guide failed2percentlengthgate',step,strain)
        if step%60==0:print('R62_XPBD',step,total,'strain',strain,'contacts',contacts,flush=True)
    guides=np.array(guide);np.savez_compressed(E/'b-global-guide-motion.npz',guide=guides,dt=DT)
    report={'source':str(m.OUT),'sourceSha256':m.sha(m.OUT),'model':'Own guide-level XPBD distance+scalar turning-angle compliance, finite tube curvature barrier, approximate transverse drag and conservative body-envelope response. Follow61actualpackedshafts; not independent61rod dynamics.','simulationDT':DT,'iterationsPerStep':ITER,'warmupSteps':WARM,'durationSeconds':DURATION,'guideStates':len(guides),'youngModulusAssumptionPa':young,'densityAssumptionKgM3':density,'individualRadiusM':radius,'effectiveGuideEA':EA,'effectiveGuideEI':EI,'airDragCdAssumption':1.1,'velocityDampingPerSecond':1.2,'assumptionsPhysicallyCalibrated':False,'maximumRelativeSegmentExtension':maximumStrain,'maximumPointSpeedMPerS':maximumSpeed,'maximumGuideTurnRadians':maximumTurn,'bodyEnvelopeCorrections':contacts,'displayBodySelfContinuousContact':'PENDING_ACTUAL_SHAFT_VERIFICATION','twistFrictionAndIndependentFibres':'NOT_IMPLEMENTED','runtimeBenchmark':'NOT_TESTED','seconds':time.time()-start}
    report['solver']='Retained own engine batched Thomas whole-chain stretch, colored scalar-angle XPBD, finite guide-envelope contact and bounded contact/length residual solve. Same radius, material assumptions, timestep and16outeriterations as rejected local pilot. Dense unsafeguarded Newton projection also rejected before cache creation.'
    m.save('b-global-simulation-report.json',report);print('R62_XPBD_CACHE_READY',report['seconds'],maximumStrain,contacts,flush=True)
if __name__=='__main__':main()
