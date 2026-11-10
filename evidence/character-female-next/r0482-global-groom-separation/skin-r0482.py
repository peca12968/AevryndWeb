from pathlib import Path
from runpy import run_path
import numpy as np

ROOT=Path(__file__).resolve().parent
l=run_path(str(ROOT/'solve-r0482.py'))
old,groom=l['old'],l['groom']
v=run_path(str(l['l']['R469']/'verify-r0469.py'))


def main():
    _,radius,ids,_,_,_,body,tri=l['l']['p']['raw_data']()
    proof=old.read(ROOT/'global-receipt.json')
    tree=l['l']['solver']['body_tree'](body,tri)
    rows={}
    for tag,item in proof['variants'].items():
        path=ROOT/item['file']; assert old.file_sha(path)==item['sha256']
        with np.load(path,allow_pickle=False) as f:
            q=f['position']; faces=f['skinTriangle']; weights=f['barycentric']; c=f['curveIDs']; r=f['radius']
        assert np.array_equal(c,ids) and np.array_equal(r,radius)
        assert (faces>=0).all() and (faces<len(tri)).all() and weights.min()>-1.e-4
        assert np.max(abs(weights.sum(1)-1.))<1.e-5
        result=v['clearance'](tree,q,radius,ids,np.ones(q.shape[:2],dtype=bool))
        rows[tag]=result
        old.save(ROOT/f'skin-{tag}-receipt.json',dict(variant=tag,geometryHash=groom.arr_sha(q),result=result,
            scope='All neutral points and spans against the actual archived complete skin mesh. Roots and early root spans included.'))
        print('R482_SKIN_FULL',tag,[result[k] for k in ('negativePoints','crossings','uncertifiedSpans','minimumEnvelopeMm')],flush=True)
    old.save(ROOT/'skin-receipt.json',dict(variants=rows,scope='Complete selected groom in neutral. No rig or time sweep claim.'))


if __name__=='__main__':
    main()