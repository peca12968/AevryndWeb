"""Second structural route: measured semantic free-fall corridor and C1 join.

The failed A curves turned inwards while still alongside cheek/pinna. B uses
actual head-belt dimensions to author outer free-fall controls, with a Hermite
transition. This is not per-point skin pushing or a hull projection.
"""
import bpy,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('g33',Path(__file__).with_name('build-female-next-r0033-parted-bob.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
BASE_PATH=g.path;DIMS=None

def hermite(p0,p1,t0,t1,t):
    return (2*t**3-3*t*t+1)*p0+(t**3-2*t*t+t)*t0+(-2*t**3+3*t*t)*p1+(t**3-t*t)*t1

def landmark_path(tree,tri,side,a,u):
    theta=g.theta_min(a)+(1.42-g.theta_min(a))*u
    goal=a+.85*math.exp(-(a/.8)**2)-.06*math.sin(2*a)
    # Different scalp layers leave at distinct elevations and volume. Keep the
    # crown part unchanged, but avoid funneling every layer into one tight ring.
    theta_end=min(theta,.12+.13*u);lift=.0045+.002*(.5+.5*math.sin(2*a+4*u))
    P=[];root=None
    for t in np.linspace(0,1,65):
        # Nonzero terminal parameter derivative defines the tangent at exit.
        f=t*t*(2-t)
        p,n,tid,bary=g.scalp(tree,tri,side*(a+(goal-a)*f),theta+(theta_end-theta)*f)
        P.append(p+n*(.00018+lift*math.sin(math.pi*.5*t)**1.2))
        if root is None:root={'triangle':tid,'barycentric':bary.tolist(),'skinPoint':p.tolist(),'normal':n.tolist(),'standOffM':.00018,'part':int(side),'scalpParam':[a,u],'azimuth':side*a,'elevation':theta}
    p0=P[-1];tangent=g.normalized(P[-1]-P[-2])
    phi=side*goal;rx,rf,rb=DIMS
    # One explicit free-fall handle above the pinna, one below it, and a soft
    # feathered tip. No point is projected onto an envelope or adjusted after
    # collision; a failed corridor is rejected as a whole.
    shoulder=g.ellipse(phi,rx+.003*u,rf+.003*u,rb+.003*u,1.475+.006*u)
    lower=g.ellipse(phi,rx-.001,rf-.002,rb-.002,1.405+.003*math.sin(2*a+u))
    tip=g.ellipse(phi,rx-.006,rf-.008,rb-.008,1.357+.009*math.sin(3*a+2.3*u))
    tangent_down=np.array((0.,0.,-.07))
    first_length=np.linalg.norm(shoulder-p0)
    for t in np.linspace(0,1,49)[1:]:P.append(hermite(p0,shoulder,tangent*first_length*.9,tangent_down*.55,t))
    for t in np.linspace(0,1,49)[1:]:P.append(hermite(shoulder,lower,tangent_down*.55,tangent_down*.75,t))
    for t in np.linspace(0,1,33)[1:]:P.append(hermite(lower,tip,tangent_down*.75,(tip-lower)*.8,t))
    P=np.array(P);lengths=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))))
    samples=np.linspace(0,lengths[-1],g.N);P=np.column_stack([np.interp(samples,lengths,P[:,k]) for k in range(3)])
    return P,root

def main():
    global DIMS
    assert json.loads((g.E/'a-saved-precision-guide-contact.json').read_text())['status']=='FAIL_OR_UNRESOLVED'
    bpy.ops.wm.open_mainfile(filepath=str(g.SRC));v,t=g.b.evaluated(bpy.data.objects[g.b.BODY],True)
    belt=v[(v[:,2]>1.345)&(v[:,2]<1.485)]
    # Extents are measurements used to place artist controls, not a collider.
    DIMS=(float(np.abs(belt[:,0]).max()+.012),float(g.C[1]-belt[:,1].min()+.010),float(belt[:,1].max()-g.C[1]+.012))
    g.save('b-landmark-measurements.json',{'headBeltZ':[1.345,1.485],'vertices':len(belt),'minM':belt.min(0).tolist(),'maxM':belt.max(0).tolist(),'authoredControlRadiiM':DIMS,'reason':'A had face and pinna centerline crossings; free-length route must remain outside those measured dimensions before tip contraction','routing':'C1 Hermite shoulder/lower/tip controls, no global hull or nearest-point projection'})
    g.path=landmark_path;g.OUT=g.b.S/'aevrynd-female-next-r0033-b-landmark-bob-guides.blend'
    # Separate candidate artifacts without duplicating or overwriting A.
    original_save=g.save
    g.save=lambda n,x:original_save(('b-'+n[2:]) if n.startswith('a-') else ('b-'+n if n in ('round-contract.json','baseline-state.json') else n),x)
    original_guides=g.guides
    def named_guides(paths,body,mat):
        o=original_guides(paths,body,mat);o.name='AFN33_B_EDITABLE_LANDMARK_GUIDES';o.data.name=o.name;return o
    g.guides=named_guides
    original_render=g.q.render
    g.q.render=lambda label:original_render('b-guides' if label=='a-guides' else label)
    # g.main writes a fixed NPZ name: intercept NumPy save for this candidate.
    original_np_save=np.savez_compressed
    def candidate_cache(path,*args,**kwargs):
        path=Path(path)
        if path.name=='aevrynd-female-next-r0033-a-parted-bob-guides.npz':path=path.with_name('aevrynd-female-next-r0033-b-landmark-bob-guides.npz')
        return original_np_save(path,*args,**kwargs)
    np.savez_compressed=candidate_cache
    sys.argv.append('--skip-before');g.main()
    contract_path=g.E/'b-round-contract.json';contract=json.loads(contract_path.read_text());contract.update({'candidate':'B','previousCandidate':'A rejected 48 complete capsules, no child expansion','hypothesis':'Measured head-belt free-fall controls with tangent-continuous crown exit avoid face/pinna interior before contracting toward chin','methodDifference':'New semantic shoulder/lower/tip Hermite routing and distributed layer exit elevations; not density or tolerance change','candidateCount':2});contract_path.write_text(json.dumps(contract,indent=2)+'\n')

if __name__=='__main__':main()
