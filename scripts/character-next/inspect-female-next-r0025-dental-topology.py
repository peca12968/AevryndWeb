"""Bounded inspection of original/adapted dental topology and contact regions."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent));import oral_proxy_data as data
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0025-dental-contact';E.mkdir(exist_ok=True)
def save(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
def main():
    folder=S/'oral/makehuman-system-cc0/teeth/teeth_base';V,uv,F,FUV=data.obj(folder/'teeth_base.obj');groups=data.components(len(V),F)
    cache=np.load(S/'aevrynd-female-next-r0024-oral-fit-data.npz');mapping=data.proxy(folder/'teeth_base.mhclo');fitted,scales=data.fit(mapping,data.to_mh(cache['nativeNeutral']));Q=data.to_blender(fitted)
    centres=np.array([V[g].mean(0) for g in groups[1:]]);design=np.column_stack((np.ones(32),centres[:,2],abs(centres[:,0])));residual=centres[:,1]-design@np.linalg.lstsq(design,centres[:,1],rcond=None)[0]
    rows=[]
    for ci,g in enumerate(groups[1:],1):
        ids=set(g);faces=[f for f in F if set(f).issubset(ids)];edges={}
        for f in faces:
            for a,b in zip(f,f[1:]+f[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
        boundary=[edge for edge,count in edges.items() if count==1];boundary_ids=sorted({v for e in boundary for v in e})
        rows.append({'component':ci,'jaw':'upper' if residual[ci-1]>0 else 'lower','vertices':len(g),'faces':len(faces),'edges':len(edges),'euler':len(g)-len(edges)+len(faces),'boundaryEdges':len(boundary),'nonManifoldEdges':sum(n>2 for n in edges.values()),'centreM':Q[g].mean(0).tolist(),'boundsM':[Q[g].min(0).tolist(),Q[g].max(0).tolist()],'boundaryBoundsM':[Q[boundary_ids].min(0).tolist(),Q[boundary_ids].max(0).tolist()] if boundary_ids else None,'boundaryVertices':boundary_ids,'originalIndices':g})
    prior=json.loads((R/'Evidence/character-female-next/r0024-oral-layers/contact-provenance.json').read_text(encoding='utf8'));pairs=prior['adaptedNeutralAsset']['componentPairs'];contacts=[]
    for key,count in pairs.items():
        a,b=map(int,key.split(','))
        if a==0 or b==0:continue
        ca,cb=Q[groups[a]].mean(0),Q[groups[b]].mean(0)
        contacts.append({'components':[a,b],'sameJaw':rows[a-1]['jaw']==rows[b-1]['jaw'],'trianglePairs':count,'centresDistanceM':float(np.linalg.norm(ca-cb))})
    save('topology-inspection.json',{'vertices':len(V),'faces':len(F),'teeth':rows,'contacts':sorted(contacts,key=lambda x:-x['trianglePairs']),'scope':'Actual original topology and adapted neutral coordinates; raw prior contacts only. No contact acceptance.'})
    print(json.dumps({'boundaryDistribution':{str(n):sum(row['boundaryEdges']==n for row in rows) for n in set(row['boundaryEdges'] for row in rows)},'sameJawContactComponentPairs':sum(c['sameJaw'] for c in contacts),'opposingContactComponentPairs':sum(not c['sameJaw'] for c in contacts),'topContacts':sorted(contacts,key=lambda x:-x['trianglePairs'])[:10],'examples':[{k:v for k,v in row.items() if k not in ('originalIndices','boundaryVertices')} for row in rows[:2]+rows[-2:]]},indent=2))
if __name__=='__main__':main()
