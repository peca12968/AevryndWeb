from pathlib import Path
from runpy import run_path
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
R479 = ROOT.parent/'r0479-parallel-transport-locks'
R480 = ROOT.parent/'r0480-lock-clearance-projection'
l = run_path(str(R479/'layout-r0479.py'))
prior = run_path(str(ROOT.parent/'r0478-direction-density-control'/'rear-coverage-r0478.py'))
depth, step = prior['depth'], prior['STEP']


def cover(rays,skin):
    return rays > skin+.00001


def main():
    v,r,ids,keep,cap,pivot,body,tri = l['p']['raw_data']()
    proof = l['old'].read(ROOT/'binding-receipt.json')
    with np.load(R480/'clearance-B.npz',allow_pickle=False) as parent:
        banks = dict(base=parent['position'])
    for tag,item in proof['variants'].items():
        path = ROOT/item['file']
        assert l['old'].file_sha(path) == item['sha256']
        with np.load(path,allow_pickle=False) as f:
            banks[tag] = f['position']
    all_samples = {}
    for degrees in (0,-55,55):
        theta = np.deg2rad(degrees)
        c,s = np.cos(theta),np.sin(theta)
        rotation = np.array(((c,-s,0.),(s,c,0.),(0.,0.,1.)),dtype='f4')
        x0 = s*.037-.051
        z0 = 1.411
        shape = (408,408)
        origin = np.array([x0+.5*step,z0+.5*step])
        mask = np.zeros(len(v),dtype=bool)
        depths = {tag:depth(q@rotation,r,mask,origin,shape)[0] for tag,q in banks.items()}
        skin = np.full(shape[0]*shape[1],np.nan,dtype='f4')
        tree = l['solver']['body_tree'](body@rotation,tri)
        direction = Vector((0.,-1.,0.))
        covered_ray = np.isfinite(np.maximum.reduce(list(depths.values())))
        for i in np.flatnonzero(covered_ray):
            x,z = np.array((i%shape[0],i//shape[0]))*step+origin
            hit,n,_,_ = tree.ray_cast(Vector((x,.17,z)),direction,.174)
            if hit is not None and n.y>.13:
                skin[i] = hit.y
        base = cover(depths['base'],skin)
        rows = {}
        x = x0 + (np.arange(102)*4+2)*step
        z = z0 + (np.arange(102)*4+2)*step
        interior = (abs(x-s*.037)[None,:]<.037)&((z>=1.450)&(z<1.506))[:,None]
        base_blocks = base.reshape(102,4,102,4).sum(axis=(1,3))
        eligible = interior & (base_blocks>=14)
        for tag in ('A','B'):
            mask = cover(depths[tag],skin)
            loss = base&~mask
            gain = mask&~base
            blocks = mask.reshape(102,4,102,4).sum(axis=(1,3))
            rows[tag] = dict(interiorBlocksWithAtLeast87PctBaselineCoverage=int(eligible.sum()),newMajorOpenings=int((eligible&(blocks<=3)).sum()),newModerateOpenings=int((eligible&(blocks<=8)).sum()),covered=int(mask.sum()),loss=int(loss.sum()),gain=int(gain.sum()),
                             lossPctOfBaseline=float(100.*loss.sum()/base.sum()),
                             gainPctOfBaseline=float(100.*gain.sum()/base.sum()))
        all_samples[str(degrees)] = dict(gridOrigin=origin.tolist(),rays=len(skin),baselineCovered=int(base.sum()),variants=rows)
        print('R482_INTERIOR',degrees,all_samples[str(degrees)],flush=True)
    l['old'].save(ROOT/'coverage-interior-receipt.json',dict(spacingMm=step*1000.,
        scope='Neutral rear skin mesh with r480 B as the reference. Orthographic rays at 0 and 55 degrees to both sides, using nearest planar strand centre and interpolated radius. Rays sample potential line-of-sight skin coverage and do not equate to rendered pixels.',samples=all_samples))


if __name__ == '__main__':
    main()