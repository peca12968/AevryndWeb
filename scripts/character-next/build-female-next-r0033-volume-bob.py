"""Final bounded candidate: continuous free-volume Bezier, full crown roots.

B's semantic Hermite ring passed contact but gave box-like shoulders. C starts
volume earlier on the crown and uses one degree-five free-length curve rather
than a sequence of vertical shoulder constraints. No post-collision pushing.
"""
import bpy,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b33',Path(__file__).with_name('build-female-next-r0033-landmark-bob.py'));h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);g=h.g

def volume_path(tree,tri,side,a,u):
    theta=g.theta_min(a)+(1.54-g.theta_min(a))*u
    goal=a+.85*math.exp(-(a/.8)**2)-.06*math.sin(2*a)
    theta_end=min(theta,.30+.13*u);lift=.010+.005*u+.001*math.sin(2*a+4*u)
    P=[];root=None
    for t in np.linspace(0,1,97):
        f=t*t*(2-t)
        p,n,tid,bary=g.scalp(tree,tri,side*(a+(goal-a)*f),theta+(theta_end-theta)*f)
        # Root remains a true ~180um follicle exit. Volume builds through the
        # upper scalp flow, not as a late horizontal ear-avoidance ledge.
        P.append(p+n*(.00018+lift*math.sin(math.pi*.5*t)**1.2))
        if root is None:root={'triangle':tid,'barycentric':bary.tolist(),'skinPoint':p.tolist(),'normal':n.tolist(),'standOffM':.00018,'part':int(side),'scalpParam':[a,u],'azimuth':side*a,'elevation':theta}
    p0=P[-1];tangent=g.normalized(P[-1]-P[-2]);phi=side*goal;rx,rf,rb=h.DIMS
    # A single Bezier has no internal shoulder/ring join. Author controls at
    # anatomical levels, with distinct layer volume and feathered endpoints.
    controls=np.array((p0,p0+tangent*.035,
        g.ellipse(phi,rx+.010,rf+.010,rb+.010,1.485),
        g.ellipse(phi,rx+.008,rf+.006,rb+.008,1.425),
        g.ellipse(phi,rx-.003,rf-.005,rb-.003,1.379),
        g.ellipse(phi,rx-.008,rf-.012,rb-.008,1.353+.010*math.sin(3*a+2.3*u))))
    for t in np.linspace(0,1,97)[1:]:
        weights=np.array([math.comb(5,k)*t**k*(1-t)**(5-k) for k in range(6)])
        point=weights@controls
        phase=2*a+3*u;point+=.0018*math.sin(math.pi*t)**2*np.array((side*math.sin(phase+2*t),math.cos(phase+1.7*t),.3*math.sin(phase+t)))
        P.append(point)
    P=np.array(P);lengths=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))))
    samples=np.linspace(0,lengths[-1],g.N);return np.column_stack([np.interp(samples,lengths,P[:,k]) for k in range(3)]),root

def configure():
    h.DIMS=tuple(json.loads((g.E/'b-landmark-measurements.json').read_text())['authoredControlRadiiM'])
    g.path=volume_path;g.N=128;g.U=np.linspace(0,1,6)

def main():
    configure();g.OUT=g.b.S/'aevrynd-female-next-r0033-c-volume-bob-guides.blend'
    original_save=g.save
    g.save=lambda n,x:original_save(('c-'+n[2:]) if n.startswith('a-') else ('c-'+n if n in ('round-contract.json','baseline-state.json') else n),x)
    original_guides=g.guides
    def named_guides(paths,body,mat):
        o=original_guides(paths,body,mat);o.name='AFN33_C_EDITABLE_VOLUME_GUIDES';o.data.name=o.name;return o
    g.guides=named_guides
    original_render=g.q.render;g.q.render=lambda label:original_render('c-guides' if label=='a-guides' else label)
    original_np_save=np.savez_compressed
    def candidate_cache(path,*args,**kwargs):
        path=Path(path)
        if path.name=='aevrynd-female-next-r0033-a-parted-bob-guides.npz':path=path.with_name('aevrynd-female-next-r0033-c-volume-bob-guides.npz')
        return original_np_save(path,*args,**kwargs)
    np.savez_compressed=candidate_cache
    sys.argv.append('--skip-before');g.main()
    contract_path=g.E/'c-round-contract.json';contract=json.loads(contract_path.read_text());contract.update({'candidate':'C / final bounded route','candidateCount':3,'previousCandidates':'A contact failed; B guide/body pass but box-like shoulder silhouette rejected','hypothesis':'Early crown volume, complete pole coverage and one degree-five free curve produce a continuous rounded bob rather than a vertical ring/corner','methodDifference':'Early scalp volume and a single continuous free-length curve replace the semantic Hermite ring architecture','pilot':{'guides':108,'pointsPerGuide':128,'radiusM':.00008,'fullBodyCapsules':True}});contract_path.write_text(json.dumps(contract,indent=2)+'\n')

if __name__=='__main__':main()
