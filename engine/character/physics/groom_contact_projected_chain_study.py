"""R93 second construction: active supporting planes inside stretch Jacobian.

Own research extension, not formal runtime or a general contact/friction solve.
Active bilateral linearized planes may temporarily stick; refreshed closest
surface queries/release do not prove finite shaft exclusion or naturalness.
"""
from pathlib import Path
import importlib.util
import numpy as np
sp=importlib.util.spec_from_file_location('direct93base',Path(__file__).with_name('groom_direct_chain_study.py'))
base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base)
STATUS='UNACCEPTED_R0093_ACTIVE_CONTACT_RESEARCH_NOT_RUNTIME'

class ContactProjectedChains(base.DirectChains):
    def stretch_solve(self,lamb,contact):
        edge=np.diff(self.x,axis=1)
        length=np.maximum(np.linalg.norm(edge,axis=2),1e-12)
        n=edge/length[...,None]
        N=contact.normals.reshape(self.x.shape)
        active=contact.active.reshape(self.x.shape[:2])
        def project(v,normal,mask):
            return v-normal*(np.einsum('nki,nki->nk',v,normal)*mask)[...,None]
        left=project(n,N[:,:-1],active[:,:-1])
        right=project(n,N[:,1:],active[:,1:])
        a=self.w[:,:-1]*np.einsum('nki,nki->nk',n,left)+self.w[:,1:]*np.einsum('nki,nki->nk',n,right)+self.as_
        off=-self.w[:,1:-1]*np.einsum('nki,nki->nk',right[:,:-1],n[:,1:])
        z=base.tridiagonal(a,off,-(length-self.length)-self.as_*lamb)
        delta=np.zeros_like(self.x)
        delta[:,:-1]-=n*z[...,None]
        delta[:,1:]+=n*z[...,None]
        self.x+=self.w[...,None]*project(delta,N,active)
        lamb+=z

    def advance(self,roots,curvature,contact,iterations=6):
        old=self.x.copy();self.v*=np.exp(-1.5*self.dt);self.v[...,2]-=9.81*self.dt;self.x+=self.v*self.dt;self.x[:,0]=roots
        ls=np.zeros_like(self.length);lb=np.zeros_like(self.curvature)
        for _ in range(iterations):
            self.bend_solve(curvature,lb)
            self.x[:,0]=roots
            contact(self.x)
            self.stretch_solve(ls,contact)
            self.x[:,0]=roots
        # Re-query the real surface after the last tangential Newton step.
        contact(self.x);self.x[:,0]=roots
        self.v=(self.x-old)/self.dt;self.v[:,0]=0
        strain=abs(np.linalg.norm(np.diff(self.x,axis=1),axis=2)/self.length-1)
        return {'maximumRelativeEdgeStrain':float(strain.max()),'p99RelativeEdgeStrain':float(np.quantile(strain,.99)),'maximumVelocityMS':float(np.linalg.norm(self.v,axis=2).max())}
