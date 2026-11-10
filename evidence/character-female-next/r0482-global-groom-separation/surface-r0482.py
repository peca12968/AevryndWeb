from pathlib import Path
from runpy import run_path
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
l=run_path(str(ROOT/'solve-r0482.py'))
old,groom=l['old'],l['groom']


def bound(tree,p,q,a,b,depth=0):
    middle=(p+q)*.5; hit,n,_,distance=tree.find_nearest(middle)
    if (middle-hit).dot(n)<=0.:
        return -float(distance)-max(a,b)
    lower=float(distance)-(q-p).length*.5-max(a,b)-.000010
    if lower>0. or depth==12:
        return lower
    radius=(a+b)*.5
    return min(bound(tree,p,middle,a,radius,depth+1),bound(tree,middle,q,radius,b,depth+1))


def row_bound(tree,row,radius):
    vectors=[Vector(x) for x in row]
    values=np.array([bound(tree,vectors[k],vectors[k+1],radius[k],radius[k+1]) for k in range(79)])
    return values


def initial_bounds(tree,q,r):
    distance=np.empty(q.shape[:2],dtype='f4')
    for i,row in enumerate(q):
        for k,x in enumerate(row):
            hit,n,_,d=tree.find_nearest(Vector(x))
            distance[i,k]=d if (Vector(x)-hit).dot(n)>=0. else -d
    edge=np.linalg.norm(np.diff(q,axis=1),axis=2)
    result=np.minimum(distance[:,:-1],distance[:,1:])-edge*.5-np.maximum(r[:,:-1],r[:,1:])-.000010
    candidate=result<=0.
    for i in np.flatnonzero(candidate.any(1)):
        vectors=[Vector(x) for x in q[i]]
        for k in np.flatnonzero(candidate[i]):
            result[i,k]=bound(tree,vectors[k],vectors[k+1],r[i,k],r[i,k+1])
    return result


def main():
    _,radius,ids,_,_,_,body,tri=l['l']['p']['raw_data']()
    tree=l['l']['solver']['body_tree'](body,tri)
    proof=old.read(ROOT/'global-receipt.json'); outcomes={}
    for tag,item in proof['variants'].items():
        path=ROOT/item['file']; assert old.file_sha(path)==item['sha256']
        with np.load(path,allow_pickle=False) as f:
            bank=dict(f)
        q=bank['position'].copy(); original=q.copy(); anchors=q[:,0].copy()
        lower=initial_bounds(tree,q,radius)
        initial_bad=np.argwhere(lower<=0.); altered=set(); history=[]
        for iteration in range(10):
            bad=np.argwhere(lower<=0.)
            history.append(dict(passNumber=iteration,uncertifiedSpans=len(bad),minimumEnvelopeMm=float(lower.min()*1000.)))
            print('R482_SURFACE_PASS',tag,history[-1],flush=True)
            if not len(bad):
                break
            movement=np.zeros_like(q); counts=np.zeros(q.shape[:2],dtype='f4')
            for i,k in bad:
                worst=None
                for t in np.linspace(0.,1.,17):
                    x=q[i,k]*(1.-t)+q[i,k+1]*t
                    hit,n,_,d=tree.find_nearest(Vector(x))
                    signed=(d if (Vector(x)-hit).dot(n)>=0. else -d)-((1.-t)*radius[i,k]+t*radius[i,k+1])
                    if worst is None or signed<worst[0]:
                        worst=(signed,t,np.asarray(n,dtype='f4'))
                gap,t,n=worst; missing=.000032-gap
                if missing<=0.:
                    continue
                bary=np.array((1.-t,t),dtype='f4')
                bary*=np.array((k!=0,True),dtype='f4')
                correction=n*missing/max(float((bary*bary).sum()),.01)
                for j,w in enumerate(bary):
                    if w:
                        movement[i,k+j]+=w*correction; counts[i,k+j]+=1.
                altered.add(int(i))
            active=counts>0.
            assert active.any(),'No useful surface correction'
            delta=movement/np.maximum(counts,1.)[:,:,None]
            q+=l['p']['vector_limit'](delta,.00015); q[:,0]=anchors
            for i in sorted(altered):
                lower[i]=row_bound(tree,q[i],radius[i])
        assert (lower>0.).all(),(tag,history[-1])
        assert np.array_equal(q[:,0],anchors) and np.isfinite(q).all()
        bank['position']=q
        file=ROOT/f'surface-{tag}.npz'; assert not file.exists(); np.savez_compressed(file,**bank)
        _,contact=l['evaluate'](ROOT/'contacts'/f'surface-{tag}',q,radius,ids,proof['parent'])
        outcomes[tag]=dict(file=file.name,sha256=old.file_sha(file),positionHash=groom.arr_sha(q),
            fullNeutralMinimumSkinEnvelopeMm=float(lower.min()*1000.),initialUncertifiedSpans=int(len(initial_bad)),
            finalUncertifiedSpans=0,changedStrands=len(altered),maxSurfaceCorrectionMm=float(np.linalg.norm(q-original,axis=2).max()*1000.),
            nearAxis=contact['NearAxis'],finite=contact['finiteOverlapWitnesses'],minHairSignedMm=contact['MinSignedM']*1000.,history=history)
        print('R482_SURFACE_FINAL',tag,outcomes[tag],flush=True)
    old.save(ROOT/'surface-receipt.json',dict(parent=proof['parent'],globalReceiptSha256=old.file_sha(ROOT/'global-receipt.json'),variants=outcomes,
        scope='All neutral skin spans certified using a distance lower bound with adaptive subdivision to 12 and a 10-micron guard. Local corrections touch the previously uncertified strands; root positions remain exact. Hair self-contact re-audited from span 0.'))


if __name__=='__main__':
    main()