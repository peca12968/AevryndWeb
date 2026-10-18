"""Aevrynd-owned offline guide solver reference, independent of Blender.

XPBD distance update follows the published mathematical formulation, implemented
here without third-party solver code. This is not a production runtime module.
Bending uses two-edge rest distances, not a calibrated Cosserat/twist model.
"""
import math
import numpy as np

def rotate_yaw(vertices,axis,pivot,angle,head_weights=None):
    x=vertices-pivot;c=math.cos(angle);s=math.sin(angle)
    q=pivot+x*c+np.cross(axis,x)*s+(x@axis)[...,None]*axis*(1-c)
    return q if head_weights is None else vertices+head_weights[...,None]*(q-vertices)

def distance_group(x,inv_mass,indices,span,rest,lambdas,compliance,dt):
    a=indices;b=a+span;d=x[:,b]-x[:,a];length=np.linalg.norm(d,axis=-1);n=d/np.maximum(length[...,None],1e-12);wa=inv_mass[:,a];wb=inv_mass[:,b];alpha=compliance[:,a]/(dt*dt);delta=(-(length-rest[:,a])-alpha*lambdas[:,a])/np.maximum(wa+wb+alpha,1e-20)
    lambdas[:,a]+=delta;x[:,a]-=(wa*delta)[...,None]*n;x[:,b]+=(wb*delta)[...,None]*n

def segment_plane_gaps(x,normals,offsets,start=3):
    v=(x.reshape(-1,3)@normals.T-offsets).reshape(*x.shape[:2],-1)
    return np.max(np.minimum(v[:,start:-1],v[:,start+1:]),axis=-1)

def project_segments(x,normals,offsets,margin,start=3):
    # Each color contains disjoint finite segments. A shared separating plane
    # places both endpoints, hence the whole radius capsule, outside the proxy.
    for parity in (0,1):
        ids=np.arange(start,x.shape[1]-1);ids=ids[ids%2==parity]
        if not len(ids):continue
        a=x[:,ids]@normals.T-offsets;b=x[:,ids+1]@normals.T-offsets;common=np.minimum(a,b);index=np.argmax(common,axis=-1);best=np.take_along_axis(common,index[...,None],axis=-1)[...,0];normal=normals[index]
        da=np.maximum(0.,margin-np.take_along_axis(a,index[...,None],axis=-1)[...,0]);db=np.maximum(0.,margin-np.take_along_axis(b,index[...,None],axis=-1)[...,0]);active=best<margin
        x[:,ids]+=normal*(da*active)[...,None];x[:,ids+1]+=normal*(db*active)[...,None]

class GuideSolver:
    def __init__(self,rest,linear_density=2.5e-4,axial_stiffness=5.,bend_compliance=.10,iterations=16,air_drag=2.):
        self.rest=np.array(rest,dtype=np.float64);self.x=self.rest.copy();self.velocity=np.zeros_like(self.x);self.iterations=iterations;self.air_drag=air_drag
        self.length=np.linalg.norm(np.diff(self.rest,axis=1),axis=-1);m=linear_density*np.concatenate((self.length[:,:1]*.5,(self.length[:,:-1]+self.length[:,1:])*.5,self.length[:,-1:]*.5),axis=1);self.inv_mass=1/np.maximum(m,1e-12);self.inv_mass[:,:3]=0
        self.stretch_alpha=self.length/axial_stiffness;self.bend_length=np.linalg.norm(self.rest[:,2:]-self.rest[:,:-2],axis=-1);self.bend_alpha=np.full_like(self.bend_length,bend_compliance);self.mass=m;self.gravity=np.array((0.,0.,-9.81))
    def step(self,dt,anchors,wind_velocity,normals=None,offsets=None,radius=.00006):
        old=self.x.copy();self.velocity+=(self.gravity+self.air_drag*(wind_velocity-self.velocity))*dt;self.x+=self.velocity*dt;self.x[:,:3]=anchors
        stretch_lambda=np.zeros_like(self.length);bend_lambda=np.zeros_like(self.bend_length)
        for iteration in range(self.iterations):
            for color in (0,1):distance_group(self.x,self.inv_mass,np.arange(color,self.x.shape[1]-1,2),1,self.length,stretch_lambda,self.stretch_alpha,dt)
            for color in (0,1,2):distance_group(self.x,self.inv_mass,np.arange(color,self.x.shape[1]-2,3),2,self.bend_length,bend_lambda,self.bend_alpha,dt)
            if normals is not None and iteration%4==3:project_segments(self.x,normals,offsets,radius+.000035)
            self.x[:,:3]=anchors
        if normals is not None:
            for _ in range(3):project_segments(self.x,normals,offsets,radius+.000035)
        self.x[:,:3]=anchors;self.velocity=(self.x-old)/dt
        return self.x
    def statistics(self):
        error=np.abs(np.linalg.norm(np.diff(self.x,axis=1),axis=-1)/self.length-1)
        return {'maximumRelativeStretch':float(error.max()),'p99RelativeStretch':float(np.quantile(error,.99)),'maximumSpeedMps':float(np.linalg.norm(self.velocity,axis=-1).max()),'kineticEnergyJ':float(np.sum(.5*self.mass*np.sum(self.velocity**2,axis=-1))),'finite':bool(np.isfinite(self.x).all() and np.isfinite(self.velocity).all())}

def head_yaw(t):
    omega=math.radians(25)/.325
    if t<=.25:return 0.
    if t<.32:return omega*(t-.25)**2/(2*.07)
    if t<.60:return omega*((t-.32)+.035)
    if t<.62:
        u=t-.60;return omega*(.315+u-u*u/.04)
    return math.radians(25)

def wind(t):
    ramp=min(max((t-.55)/.15,0.),1.)*min(max((1.40-t)/.20,0.),1.)
    return np.array((1.1*ramp,0.,0.))
