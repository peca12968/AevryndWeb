"""Own all-native-strand CPU reference; not a runtime or full collision claim.

Per-edge stretch and co-rotated vector rest-curvature XPBD, root-tangent
boundary, gravity and drag. Frozen closest-skin planes are response caches,
never exact curved-fibre/continuous collision certificates. No self contact,
torsional state, friction or calibrated material response is implemented.
Design reference: GPUOpen TressFXSimulation local shape/length/collision split.
No TressFX code, library or runtime service is used.
"""
import numpy as np
STATUS='REJECTED_R0070_TECHNICAL_STUDY_NOT_ENGINE_RUNTIME'
YOUNG=3e9;DENSITY=1300.;DRAG_RATE=1.5;SUBSTEPS=4;ITERATIONS=8
class NativeRods:
    def __init__(self,rest,counts,radii):
        self.rest=rest.copy();self.x=rest.copy();self.v=np.zeros_like(rest);self.counts=counts;self.starts=np.r_[0,np.cumsum(counts)[:-1]];local=np.concatenate([np.arange(n) for n in counts]);self.local=local
        edge=np.flatnonzero(local<np.repeat(counts,counts)-1);self.edge=edge;self.colors=[edge[local[edge]%2==i] for i in range(2)];bend=np.flatnonzero((local>=1)&(local<np.repeat(counts,counts)-1));self.bend=bend;self.bcolors=[bend[local[bend]%3==i] for i in range(3)]
        length=np.linalg.norm(rest[edge+1]-rest[edge],axis=1);assert (length>1e-7).all();self.ds=np.zeros(len(rest));self.ds[edge]=length;dual=np.zeros(len(rest));dual[edge]+=length*.5;dual[edge+1]+=length*.5
        # Physical response is approximate for the source's decorative subpixel flyaways.
        physics_radius=np.maximum(radii,1e-6);area=np.pi*physics_radius**2;self.w=1/(DENSITY*area*np.maximum(dual,1e-6));self.w[self.starts]=0;self.ealpha=np.zeros(len(rest));self.ealpha[edge]=length/(YOUNG*(area[edge]+area[edge+1])*.5);self.balpha=np.zeros(len(rest));ell=(self.ds[bend-1]+self.ds[bend])*.5;EI=YOUNG*np.pi*physics_radius[bend]**4/4;self.balpha[bend]=ell**3/EI
        first=self.starts+1;self.first=first;self.talpha=self.ds[self.starts]**3/(YOUNG*np.pi*physics_radius[first]**4/4)
    @staticmethod
    def corotate(value,reference,current):
        a=reference/np.maximum(np.linalg.norm(reference,axis=1),1e-20)[:,None];b=current/np.maximum(np.linalg.norm(current,axis=1),1e-20)[:,None];v=np.cross(a,b);c=np.einsum('ij,ij->i',a,b);den=np.maximum(1+c,1e-8);return value+np.cross(v,value)+np.cross(v,np.cross(v,value))/den[:,None]
    def advance(self,previous_target,target,plane_old,plane_new,normal_old,normal_new,radii,frame_dt=1/24):
        dt=frame_dt/SUBSTEPS;w=self.w;x=self.x;contacts=0
        for sub in range(SUBSTEPS):
            t=(sub+1)/SUBSTEPS;K=previous_target*(1-t)+target*t;point=plane_old*(1-t)+plane_new*t;normal=normal_old*(1-t)+normal_new*t;normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-20)[:,None];old=x.copy();self.v*=np.exp(-DRAG_RATE*dt);x+=self.v*dt+np.array((0,0,-9.81))*dt*dt;x[self.starts]=K[self.starts];le=np.zeros(len(x));lb=np.zeros_like(x);lt=np.zeros((len(self.first),3))
            for _ in range(ITERATIONS):
                for ids in self.colors:
                    d=x[ids+1]-x[ids];length=np.maximum(np.linalg.norm(d,axis=1),1e-20);n=d/length[:,None];alpha=self.ealpha[ids]/dt**2;dl=-(length-self.ds[ids]+alpha*le[ids])/(w[ids]+w[ids+1]+alpha);le[ids]+=dl;x[ids]-=w[ids,None]*n*dl[:,None];x[ids+1]+=w[ids+1,None]*n*dl[:,None]
                for ids in self.bcolors:
                    prev=ids-1;nxt=ids+1;rest_bend=K[prev]-2*K[ids]+K[nxt];wanted=self.corotate(rest_bend,K[ids]-K[prev],x[ids]-x[prev]);C=x[prev]-2*x[ids]+x[nxt]-wanted;alpha=self.balpha[ids]/dt**2;dl=-(C+alpha[:,None]*lb[ids])/(w[prev]+4*w[ids]+w[nxt]+alpha)[:,None];lb[ids]+=dl;x[prev]+=w[prev,None]*dl;x[ids]-=2*w[ids,None]*dl;x[nxt]+=w[nxt,None]*dl
                ids=self.first;root=self.starts;alpha=self.talpha/dt**2;C=x[ids]-x[root]-(K[ids]-K[root]);dl=-(C+alpha[:,None]*lt)/(w[ids]+alpha)[:,None];lt+=dl;x[ids]+=w[ids,None]*dl
                gap=np.einsum('ij,ij->i',x-point,normal)-radii;bad=(gap<0)&(w>0);x[bad]-=normal[bad]*gap[bad,None];contacts+=int(bad.sum());x[root]=K[root]
            self.v=(x-old)/dt;self.v[self.starts]=(target[self.starts]-previous_target[self.starts])/frame_dt
        strain=np.abs(np.linalg.norm(x[self.edge+1]-x[self.edge],axis=1)/self.ds[self.edge]-1);assert np.isfinite(x).all() and np.isfinite(self.v).all()
        return {'maximumRelativeEdgeStrain':float(strain.max()),'p99RelativeEdgeStrain':float(np.quantile(strain,.99)),'maximumSpeedMPerS':float(np.linalg.norm(self.v,axis=1).max()),'contactPlaneProjectionOperations':contacts,'rootMaximumCorrespondenceErrorM':float(np.linalg.norm(x[self.starts]-target[self.starts],axis=1).max()),'maximumDepartureFromRigidTargetM':float(np.linalg.norm(x-target,axis=1).max())}

class NativeInextensibleFTL(NativeRods):
    """Geometric length-sphere/contact-cap solve plus DFTL velocity correction.

    Source principle: Mueller/Kim/Chentanez, Fast Simulation of Inextensible
    Hair and Fur, VRIPHYS2012. Own variable-length/native-strand implementation.
    A cached-plane infeasibility is reported, never hidden by stretching.
    """
    def advance(self,previous_target,target,plane_old,plane_new,normal_old,normal_new,radii,frame_dt=1/24):
        dt=frame_dt/SUBSTEPS;x=self.x;infeasible=0;worst_deficit=0.;contacts=0
        for sub in range(SUBSTEPS):
            t=(sub+1)/SUBSTEPS;K=previous_target*(1-t)+target*t;point=plane_old*(1-t)+plane_new*t;normal=normal_old*(1-t)+normal_new*t;normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-20)[:,None];old=x.copy();self.v*=np.exp(-DRAG_RATE*dt);pred=x+self.v*dt+np.array((0,0,-9.81))*dt*dt;x=pred.copy();x[self.starts]=K[self.starts]
            for j in range(1,int(self.counts.max())):
                active=self.counts>j;ids=self.starts[active]+j;prev=ids-1;length=self.ds[prev]
                if j==1:wanted=K[ids]-K[prev];alpha=self.talpha[active]
                else:wanted=self.corotate(K[ids]-K[prev],K[prev]-K[prev-1],x[prev]-x[prev-1]);alpha=self.balpha[prev]
                spring=dt*dt*self.w[ids]/np.maximum(alpha,1e-30);aim=(pred[ids]+spring[:,None]*(x[prev]+wanted))/(1+spring)[:,None];direction=aim-x[prev];direction/=np.maximum(np.linalg.norm(direction,axis=1),1e-20)[:,None];q=x[prev]+length[:,None]*direction;n=normal[ids];centre_gap=np.einsum('ij,ij->i',x[prev]-point[ids],n)-radii[ids];gap=np.einsum('ij,ij->i',q-point[ids],n)-radii[ids];bad=gap<0
                impossible=bad&(centre_gap+length < -1e-6);infeasible+=int(impossible.sum())
                if impossible.any():worst_deficit=max(worst_deficit,float(np.max(-(centre_gap[impossible]+length[impossible]))))
                cap=bad&(~impossible)&(np.abs(centre_gap)<=length)
                if cap.any():
                    idx=np.flatnonzero(cap);tangent=direction[idx]-n[idx]*np.einsum('ij,ij->i',direction[idx],n[idx])[:,None];nn=np.linalg.norm(tangent,axis=1);zero=nn<1e-12
                    if zero.any():tangent[zero]=np.cross(n[idx][zero],np.array((1.,.371,.193)));nn=np.linalg.norm(tangent,axis=1)
                    tangent/=nn[:,None];circle=np.sqrt(np.maximum(length[idx]**2-centre_gap[idx]**2,0));q[idx]=x[prev[idx]]-centre_gap[idx,None]*n[idx]+circle[:,None]*tangent;contacts+=len(idx)
                x[ids]=q
            correction=x-pred;self.v=(x-old)/dt;self.v[self.edge]-=correction[self.edge+1]/dt;self.v[self.starts]=(target[self.starts]-previous_target[self.starts])/frame_dt
        self.x=x;strain=np.abs(np.linalg.norm(x[self.edge+1]-x[self.edge],axis=1)/self.ds[self.edge]-1);assert np.isfinite(x).all() and np.isfinite(self.v).all()
        return {'maximumRelativeEdgeStrain':float(strain.max()),'p99RelativeEdgeStrain':float(np.quantile(strain,.99)),'maximumSpeedMPerS':float(np.linalg.norm(self.v,axis=1).max()),'contactPlaneProjectionOperations':contacts,'infeasibleCachedSpherePlaneConstraints':infeasible,'maximumCachedFeasibilityDeficitM':worst_deficit,'rootMaximumCorrespondenceErrorM':float(np.linalg.norm(x[self.starts]-target[self.starts],axis=1).max()),'maximumDepartureFromRigidTargetM':float(np.linalg.norm(x-target,axis=1).max())}
