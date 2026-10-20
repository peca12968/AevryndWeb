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

def angle_grad(x,i):
    u=x[i]-x[i+1];v=x[i+2]-x[i+1];a=np.linalg.norm(u);b=np.linalg.norm(v);c=float(np.clip((u@v)/(a*b),-1+1e-12,1-1e-12));ss=math.sqrt(max(1-c*c,1e-12))
    A=-(v/(a*b)-c*u/(a*a))/ss;C=-(u/(a*b)-c*v/(b*b))/ss
    return math.acos(c),np.array((A,-A-C,C))

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
        acceleration=np.array((0.,0.,-9.81))+force/mass[:,None];velocity*=math.exp(-DT*1.2);x+=DT*velocity+DT*DT*acceleration;x[:3]=rest[:3];stretchLambda=np.zeros(N-1);bendLambda=np.zeros(N-2);barrierLambda=np.zeros(N-2)
        for iteration in range(ITER):
            order=range(N-1) if iteration%2==0 else range(N-2,-1,-1)
            for j in order:
                d=x[j+1]-x[j];L=np.linalg.norm(d);n=d/max(L,1e-20);alpha=(ds[j]/EA)/(DT*DT);dl=(-(L-ds[j])-alpha*stretchLambda[j])/(w[j]+w[j+1]+alpha);stretchLambda[j]+=dl;x[j]-=w[j]*dl*n;x[j+1]+=w[j+1]*dl*n
            order=range(N-2) if iteration%2==0 else range(N-3,-1,-1)
            for j in order:
                angle,grad=angle_grad(x,j);ww=w[j:j+3];den=float(np.sum(ww*np.einsum('ij,ij->i',grad,grad)));alpha=angleCompliance[j]/(DT*DT);dl=(-(angle-restAngle[j])-alpha*bendLambda[j])/(den+alpha);bendLambda[j]+=dl;x[j:j+3]+=ww[:,None]*dl*grad
                angle,grad=angle_grad(x,j);constraint=angle-minimumAngle[j]
                if constraint<0 or barrierLambda[j]>0:
                    den=float(np.sum(ww*np.einsum('ij,ij->i',grad,grad)));dl=-constraint/max(den,1e-20);new=max(0.,barrierLambda[j]+dl);dl=new-barrierLambda[j];barrierLambda[j]=new;x[j:j+3]+=ww[:,None]*dl*grad
            # Closest normals provide a contact correction direction only.
            # Closed-volume anchors and actual swept display checks validate it.
            for j in range(3,N):
                hit,n,fi,distance=tree.find_nearest(Vector(x[j]));support=envelope[j]+max(ds[max(0,j-1):min(N-1,j+1)])*.5+.00005
                if distance<support:x[j]=np.array(hit)+np.array(n)*support;contacts+=1
            x[:3]=rest[:3]
        velocity=(x-old)/DT;velocity[:3]=0.;strain=float(np.max(abs(np.linalg.norm(np.diff(x,axis=0),axis=1)/ds-1)));maximumStrain=max(maximumStrain,strain);maximumSpeed=max(maximumSpeed,float(np.linalg.norm(velocity,axis=1).max()));maximumTurn=max(maximumTurn,max(math.pi-angle_grad(x,j)[0] for j in range(N-2)))
        assert np.isfinite(x).all() and np.linalg.norm(x-rest,axis=1).max()<.6,'Explosive guide; reject method before display expansion.'
        if step%60==0:print('R62_XPBD',step,total,'strain',strain,'contacts',contacts,flush=True)
    guides=np.array(guide);np.savez_compressed(E/'b-guide-motion.npz',guide=guides,dt=DT)
    report={'source':str(m.OUT),'sourceSha256':m.sha(m.OUT),'model':'Own guide-level XPBD distance+scalar turning-angle compliance, finite tube curvature barrier, approximate transverse drag and conservative body-envelope response. Follow61actualpackedshafts; not independent61rod dynamics.','simulationDT':DT,'iterationsPerStep':ITER,'warmupSteps':WARM,'durationSeconds':DURATION,'guideStates':len(guides),'youngModulusAssumptionPa':young,'densityAssumptionKgM3':density,'individualRadiusM':radius,'effectiveGuideEA':EA,'effectiveGuideEI':EI,'airDragCdAssumption':1.1,'velocityDampingPerSecond':1.2,'assumptionsPhysicallyCalibrated':False,'maximumRelativeSegmentExtension':maximumStrain,'maximumPointSpeedMPerS':maximumSpeed,'maximumGuideTurnRadians':maximumTurn,'bodyEnvelopeCorrections':contacts,'displayBodySelfContinuousContact':'PENDING_ACTUAL_SHAFT_VERIFICATION','twistFrictionAndIndependentFibres':'NOT_IMPLEMENTED','runtimeBenchmark':'NOT_TESTED','seconds':time.time()-start}
    m.save('b-simulation-report.json',report);print('R62_XPBD_CACHE_READY',report['seconds'],maximumStrain,contacts,flush=True)
if __name__=='__main__':main()
