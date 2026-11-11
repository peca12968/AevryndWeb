
from runpy import run_path
import numpy as np
import json
from pathlib import Path
p=Path(__file__).parent
m=run_path(str(p/'map-return-r0502.py'))
d=json.loads((p/'return-topology.json').read_text())
with np.load(p/'return-topology.npz',allow_pickle=False) as b:
 v=b['0/skin']
 ids=b['ids']
 def xyz(idx): return v[np.searchsorted(ids,idx)]*1000
 groups,ef=m['chart_faces'](d['rings'],d['faceMaterials'])
 eye=b['0/cornea']*1000
 for c in groups:
  ed,links=m['boundary'](c,ef)
  lim=m['partition'](links)
  side=np.sign(xyz(lim[0] if False else sorted(lim[0])).mean(0)[0])
  points=eye[np.sign(eye[:,0])==side]
  system=np.c_[2*points,np.ones(len(points))]
  params=np.linalg.lstsq(system,(points**2).sum(1),rcond=None)[0]
  center=params[:3]
  print('eye',side,len(points),center,np.percentile(np.linalg.norm(points-center,axis=1),[0,10,50,90,100]))
  for q in lim:
   a=min(q);last=None;seq=[a]
   while True:
    a0=next(j for j in sorted(links[a]) if j!=last)
    if a0==seq[0]: break
    last,a=a,a0
    seq.append(a)
   x=xyz(seq)-center
   a=np.unwrap(np.arctan2(x[:,2],x[:,0]))
   s=np.sign(a[-1]-a[0])
   print('loop',len(seq), 'signed one turn',round((a[-1]-a[0])*s,3),'reverse spans',np.count_nonzero(np.diff(a)*s<0), 'min step',min(np.diff(a)*s), 'radius',np.percentile(np.linalg.norm(x,axis=1),[0,10,50,90,100]),'angle start/end',(a[0],a[-1]))

