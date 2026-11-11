
"""Read the rim and cross sections in the native neutral head coordinate system."""
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
def front_depth(vertices, faces, x, z):
    tri = vertices[faces]
    xz = tri[:, :, [0, 2]]
    pt = np.array((x, z))
    near = (xz.min(1) <= pt).all(1) & (xz.max(1) >= pt).all(1)
    tri = tri[near]
    a, b, c = tri[:, :, [0, 2]].transpose(1, 0, 2)
    u, v, d = b-a, c-a, pt-a
    det = u[:,0]*v[:,1]-u[:,1]*v[:,0]
    ok = abs(det)>1.e-12
    safe = np.where(ok, det, 1)
    i = (d[:,0]*v[:,1]-d[:,1]*v[:,0])/safe
    j = (u[:,0]*d[:,1]-u[:,1]*d[:,0])/safe
    select = ok & (i>=-1e-5) & (j>=-1e-5) & (i+j<=1.00001)
    y = tri[:,0,1]*(1-i-j)+tri[:,1,1]*i+tri[:,2,1]*j
    return float(min(y[select],default=np.nan))
if __name__=='__main__':
    with np.load(ROOT/'rim-witness.npz', allow_pickle=False) as bank:
        row=bank['row']; side=bank['side']
        root=bank['3/roots']
        for s in (-1,1):
            for r in (0,2):
                path=root[(side==s)&(row==r)]
                order=np.argsort(abs(path[:,0]))
                print(s,r,np.round(path[order[::5]]*1000,2).tolist(),np.round(path[order[-1]]*1000,2).tolist())
        for k in (1,2,3):
            v=bank[f'{k}/skin']*1000
            f=bank[f'{k}/skinFaces'][bank[f'{k}/orbit']]
            for x in (-46.,-44.,-42.,-39.,39.,42.,44.,46.):
                print(k,x,[round(front_depth(v,f,x,z),2) for z in np.arange(1456.,1471.)])

