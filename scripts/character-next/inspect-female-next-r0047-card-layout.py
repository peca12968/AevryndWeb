"""Read CC0 authored quad columns; no source mutation or collision claim."""
import bpy,importlib.util,numpy as np,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('bob47',Path(__file__).with_name('build-female-next-r0047-authored-bob.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def columns(mesh):
    P=np.array([v.co[:]for v in mesh.vertices]);adj={};edgefaces={}
    for p in mesh.polygons:
        v=list(p.vertices)
        if len(v)!=4:continue
        es=[tuple(sorted((v[j],v[(j+1)%4])))for j in range(4)]
        for j,e in enumerate(es):adj.setdefault(e,set()).add(es[(j+2)%4]);edgefaces.setdefault(e,[]).append(p.index)
    used=set();rows=[]
    for e in adj:
        if e in used or len(adj[e])!=1:continue
        chain=[];prev=None;cur=e
        while cur is not None and cur not in used:
            used.add(cur);chain.append(cur);n=[x for x in adj[cur]if x!=prev];prev,cur=cur,(n[0]if n else None)
        C=np.array([P[list(x)].mean(0)for x in chain]);peak=int(np.argmax(C[:,2]))
        for arm in (chain[:peak+1][::-1],chain[peak:]):
            C=np.array([P[list(x)].mean(0)for x in arm]);length=float(np.linalg.norm(np.diff(C,axis=0),axis=1).sum());width=np.linalg.norm(P[np.array(arm)[:,0]]-P[np.array(arm)[:,1]],axis=1)
            if len(arm)<3 or C[0,2]-C[-1,2]<.035 or length<.05 or float(np.median(width))>.04:continue
            # Root first; consistent opposite-edge transport maintains width.
            rails=[list(arm[0])]
            for edge in arm[1:]:
                left,right=P[rails[-1]];x,y=edge
                rails.append([x,y]if np.linalg.norm(P[x]-left)+np.linalg.norm(P[y]-right)<=np.linalg.norm(P[y]-left)+np.linalg.norm(P[x]-right)else[y,x])
            rows.append({'rails':rails,'lengthM':length,'widthMedianM':float(np.median(width)),'rootM':P[rails[0]].mean(0).tolist(),'tipM':P[rails[-1]].mean(0).tolist()})
    return rows
if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(a.OUT));o=bpy.data.objects['AFN47_CC0_Bob02_AuthoredCards'];rows=columns(o.data);a.save('b-authored-quad-columns.json',{'scope':'Structural feasibility for authored card-to-native-strand construction. Not roots/contacts/dynamics.','columns':rows});print('COLUMNS',len(rows),[(round(x['lengthM'],3),round(x['widthMedianM'],3),[round(z,3)for z in x['rootM']])for x in rows],flush=True)
