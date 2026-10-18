"""Physical controls: compliance equilibrium, zero-force rest, and yaw continuity."""
import json,math,importlib.util
import numpy as np
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0015-guide-dynamics';E.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('xpbd',R/'engine/character/physics/groom_xpbd_reference.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
results=[]
# Compare the independent dense constraint system against the tridiagonal solve.
rng=np.random.default_rng(15);q=np.cumsum(rng.normal(size=(2,9,3))*.02,axis=1);w=np.full((2,9),1000.);w[:,0]=0.;L=np.linalg.norm(np.diff(q,axis=1),axis=-1)*.97;alpha=np.full_like(L,.0002);lam=np.zeros_like(L);expected=q.copy();dt=1/240
for g in range(2):
    delta=q[g,1:]-q[g,:-1];length=np.linalg.norm(delta,axis=1);n=delta/length[:,None];J=np.zeros((8,27))
    for i in range(8):J[i,i*3:i*3+3]=-n[i];J[i,(i+1)*3:(i+1)*3+3]=n[i]
    M=np.repeat(w[g],3);H=(J*M[None,:])@J.T+np.diag(alpha[g]/dt**2);solution=np.linalg.solve(H,-(length-L[g]));expected[g]+=((J.T@solution)*M).reshape(-1,3)
test=q.copy();p.coupled_stretch(test,w,L,lam,alpha,dt);error=float(np.max(np.abs(test-expected)));assert error<1e-12;results.append({'case':'coupled_stretch_against_dense_linear_system','maximumPositionErrorM':error})
for dt in (1/120,1/240):
    x=np.array([[[0.,0.,0.],[0.,0.,-1.]]]);v=np.zeros_like(x);w=np.array([[0.,10.]]);rest=np.ones((1,1));alpha=np.full((1,1),.01)
    for _ in range(round(6/dt)):
        old=x.copy();v[:,1,2]-=9.81*dt;v[:,1]*=math.exp(-5*dt);x+=v*dt;lam=np.zeros((1,1))
        for i in range(4):p.distance_group(x,w,np.array([0]),1,rest,lam,alpha,dt)
        v=(x-old)/dt
    actual=float(-x[0,1,2]-1);expected=.1*9.81*.01*math.exp(-5*dt)
    assert abs(actual-expected)<2e-5,(dt,actual,expected);results.append({'case':'single_compliant_mass_equilibrium','dt':dt,'extensionM':actual,'analyticExpectedForDiscreteDragM':expected,'errorM':abs(actual-expected)})
rest=np.stack([np.column_stack((np.zeros(12),np.zeros(12),np.linspace(0,-.1,12)))])
s=p.GuideSolver(rest);s.gravity[:]=0
for _ in range(50):s.step(1/240,rest[:,:3],np.zeros(3))
assert np.max(np.abs(s.x-rest))<1e-12;results.append({'case':'zero_force_rest','maximumErrorM':float(np.max(np.abs(s.x-rest)))})
angles=[p.head_yaw(t) for t in np.linspace(0,3,721)];assert all(b>=a-1e-12 for a,b in zip(angles,angles[1:]));assert abs(angles[-1]-math.radians(25))<1e-12;results.append({'case':'yaw_protocol','finalDegrees':math.degrees(angles[-1]),'monotonic':True})
(E/'solver-controls.json').write_text(json.dumps({'status':'PASS_LIMITED_MATH_CONTROLS','cases':results,'scope':'Basic update/units/rest/protocol controls. Does not calibrate hair elasticity, bending, aero, contacts, dynamics realism or runtime performance.'},indent=2)+'\n');print(json.dumps(results))
