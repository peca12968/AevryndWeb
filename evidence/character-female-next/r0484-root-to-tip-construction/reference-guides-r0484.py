"""Inspect actual connected source strips and derive longitudinal 3D guide curves."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parent
data=np.load(ROOT/'same-woman-reference-hair.npz',allow_pickle=False)
p=data['world'];tri=data['triangles'];uv=data['uv']
corner_ids=tri.ravel()
keys=np.column_stack((corner_ids,np.rint(uv.reshape(-1,2)*1000000.).astype('i4')))
_,inverse=np.unique(keys,axis=0,return_inverse=True)
uv_tri=inverse.reshape(-1,3)
parent=np.arange(int(inverse.max())+1,dtype='i4')
def find(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
for a,b,c in uv_tri:
    a,b,c=find(a),find(b),find(c);parent[b]=a;parent[c]=a
labels=np.array([find(i) for i in range(len(parent))]);unique,counts=np.unique(labels,return_counts=True)
order=np.argsort(counts)[::-1];rows=[];guides=[];owners=[];columns=[]
for component in unique[order]:
    mask=labels[uv_tri[:,0]]==component;faces=tri[mask];tex=uv[mask]
    ids=np.unique(faces);points=p[ids]
    span=np.ptp(tex.reshape(-1,2),axis=0)
    record=dict(component=int(component),vertices=len(ids),triangles=len(faces),uvBounds=[tex.min((0,1)).tolist(),tex.max((0,1)).tolist()],
        worldBounds=[points.min(0).tolist(),points.max(0).tolist()])
    if len(ids)<8 or len(faces)<6 or min(span)<1.e-7:
        record['guideStatus']='too_small';rows.append(record);continue
    # Estimate each UV axis's physical path length from intersections of the actual triangles.
    candidates=[]
    for axis in (0,1):
        lo,hi=tex[:,:,axis].min(),tex[:,:,axis].max();sections=[]
        for value in np.linspace(lo+span[axis]*.0001,hi-span[axis]*.0001,80):
            hits=[];across=[]
            for a,b in ((0,1),(1,2),(2,0)):
                delta=tex[:,b,axis]-tex[:,a,axis]
                t=np.divide(value-tex[:,a,axis],delta,out=np.full(len(tex),-1.,dtype='f4'),where=abs(delta)>1.e-10)
                take=(t>=0.)&(t<=1.)
                if take.any():
                    mix=t[take,None]
                    hits.append(p[faces[take,a]]*(1.-mix)+p[faces[take,b]]*mix)
                    across.append(tex[take,a,1-axis]*(1.-t[take])+tex[take,b,1-axis]*t[take])
            if not hits:break
            hits=np.concatenate(hits);across=np.concatenate(across);sort=np.argsort(across)
            hits=hits[sort];across=across[sort]
            target=across.min()+np.array((.15,.5,.85))*(across.max()-across.min())
            section=np.stack([np.interp(target,across,hits[:,k]) for k in range(3)],axis=1)
            sections.append(section)
        if len(sections)!=80:candidates.append(None);continue
        curves=np.stack(sections,axis=1).astype('f4')
        length=np.linalg.norm(np.diff(curves[1],axis=0),axis=1).sum()
        candidates.append((float(length),curves))
    valid=[(axis,item) for axis,item in enumerate(candidates) if item is not None]
    if not valid:record['guideStatus']='incomplete_uv_sections';rows.append(record);continue
    axis,(length,curves)=max(valid,key=lambda x:abs(float(x[1][1][1,0,2]-x[1][1][1,-1,2])))
    if curves[:,0,2].mean()<curves[:,-1,2].mean():curves=curves[:,::-1].copy()
    if length<.025:record['guideStatus']='short';rows.append(record);continue
    record.update(guideStatus='derived',longitudinalUVAxis=axis,medianPathLengthMm=length*1000.,rootMean=curves[:,0].mean(0).tolist(),tipMean=curves[:,-1].mean(0).tolist())
    for column,curve in enumerate(curves):guides.append(curve);owners.append(int(component));columns.append(column)
    rows.append(record)
np.savez_compressed(ROOT/'original-strip-guides.npz',position=np.asarray(guides,dtype='f4'),component=np.asarray(owners,dtype='i4'),column=np.asarray(columns,dtype='i4'))
report=dict(sourceVertices=len(p),sourceTriangles=len(tri),connectedComponents=len(unique),derivedGuideCount=len(guides),
    componentVertexCountP0P50P95P100=np.quantile(counts,[0,.5,.95,1]).tolist(),components=rows)
(ROOT/'reference-guide-analysis.json').write_bytes(json.dumps(report,indent=2).encode('utf8'))
print(json.dumps({k:v for k,v in report.items() if k!='components'},indent=2),flush=True)
print(json.dumps(rows[:8],indent=2),flush=True)
