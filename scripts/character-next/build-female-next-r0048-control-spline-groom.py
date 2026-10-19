"""Final bounded alternative: construct a new spline at each actual follicle.

Interpolate authored world-space control KNOTS, not complete transported paths
or nonlinear radial coordinates. Every spline gets its own exact root and
normal handle; a persistent root residual prevents a shared exit/funnel.
"""
import importlib.util,numpy as np,time,math
from pathlib import Path
sp=importlib.util.spec_from_file_location('g48spline',Path(__file__).with_name('build-female-next-r0048-anatomical-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
a.E=a.E/'c-control-spline';a.E.mkdir(exist_ok=True);a.PILOT=a.S/'aevrynd-female-next-r0048-c-control-spline-pilot.blend';a.OUT=a.S/'aevrynd-female-next-r0048-c-control-wave-groom.blend'
a.METHOD='Direct per-follicle Bezier construction: actual body-triangle root and its own normal exit handle, independently authored world-space free control knots interpolated across three same-side guide root locations. Preserve each root residual across all free controls, without a common exit/ring, transported complete paths or radial-body lookup. Same actual whole-body capsule gate, unchanged tolerances.'
a.INTERPOLATION='World-space free control knots interpolated before spline construction; each actual follicle supplies root and normal handle. Root residual remains in every free control to retain distinct routes. No copying/rotating whole paths, no common scalp exit and no surface unfolding.'
def followers(roots,normals,G,GN,which):
    tick=time.time();free=[]
    for name,az,el,knots in a.GUIDES:
        K=np.array(knots);t=np.linspace(0,1,len(K));free.append(np.column_stack([np.interp(np.linspace(0,1,6),t,K[:,j])for j in range(3)]))
    free=np.array(free);result=[];lineage=[];rng=np.random.default_rng(480348);u=np.linspace(0,1,a.N)
    for index,ci in enumerate(which):
        R0=roots[ci];n=normals[ci];D=np.linalg.norm(G[:,0]-R0,axis=1);same=(G[:,0,0]*R0[0]>=0)|(abs(G[:,0,0])<.009);D[~same]=np.inf;near=np.argsort(D)[:3];w=1/np.maximum(D[near],.001)**3;w/=w.sum();residual=R0-w@G[near,0];F=np.einsum('i,ijk->jk',w,free[near])+residual
        K=np.vstack((R0,R0+n*.008,F));T=np.zeros_like(K);T[0]=n*.008;T[1]=(K[2]-K[0])*.40;T[2:-1]=(K[3:]-K[1:-2])*.38;T[-1]=(K[-1]-K[-2])*.55;P=a.sample(K,T)
        # Small authored three-dimensional fibre variation, fixed at roots.
        phase=float(rng.uniform(0,2*math.pi));axis=a.norm(np.cross(n,(0,0,1)))
        if np.linalg.norm(axis)<.1:axis=np.array((1.,0,0))
        P+=axis*(float(rng.uniform(.00010,.00035))*np.sin(7*math.pi*u+phase)*np.sin(math.pi*u)**2)[:,None];trim=float(rng.uniform(.94,1));P=np.column_stack([np.interp(u*trim,u,P[:,j])for j in range(3)]);P[0]=R0;result.append(P);lineage.append({'rootId':int(ci),'guides':near.tolist(),'weights':w.tolist(),'persistentWorldRootResidualM':residual.tolist(),'trimFraction':trim,'construction':'Own per-root control spline, not complete-path transfer'})
        if index%1000==0:print('R48_SPLINE',index,len(which),time.time()-tick,flush=True)
        if time.time()-tick>720:raise TimeoutError('Per-follicle spline construction exceeded720seconds')
    return np.array(result),lineage
a.followers=followers
if __name__=='__main__':a.main()
