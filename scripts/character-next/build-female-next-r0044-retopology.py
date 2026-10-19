"""Independent ocular cup topology pilot before any production expansion.

Replaces the entire old socket disk with explicit lid annuli, lip, actual-eye
radial cavity and posterior cap. Keeps the exterior cut boundary welded. This
is a different topology, not another amplitude of the rejected native field.
"""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('lid44a',Path(__file__).with_name('build-female-next-r0044-lid-shapes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;i=a.i;E=a.E;S=a.S;SRC=a.SRC
exact=a.f.flowcheck.module('actual37r44','verify-female-next-r0037-eye-margin.py')
def save(n,x):a.save(n,x)
def normalize(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
def outerloop(V,T,mask):
    edges=np.concatenate([T[mask][:,[0,1]],T[mask][:,[1,2]],T[mask][:,[2,0]]]);edges=np.sort(edges,axis=1);e,c=np.unique(edges,axis=0,return_counts=True);boundary=e[c==1];adj={int(v):[] for v in np.unique(boundary)}
    for x,y in boundary:adj[int(x)].append(int(y));adj[int(y)].append(int(x))
    assert all(len(n)==2 for n in adj.values()),'Cut boundary not a manifold loop'
    start=min(adj);out=[start,adj[start][0]]
    while out[-1]!=start:
        ns=[v for v in adj[out[-1]] if v!=out[-2]];assert len(ns)==1;out.append(ns[0]);assert len(out)<=len(adj)+1
    out=out[:-1];assert len(out)==len(adj),'More than one orbital cut loop'
    P=V[out][:,[0,2]];area=float(np.sum(P[:,0]*np.roll(P[:,1],-1)-P[:,1]*np.roll(P[:,0],-1)))
    if area<0:out=out[::-1]
    return np.array(out,dtype='i4')
def lip(c,theta,amount,tree):
    cs=np.cos(theta);sn=np.sin(theta);s=np.abs(sn);base=c[2]-.0012+.0005*cs
    restz=base+np.where(sn>=0,.00555*s,-.00345*s);seam=base-.0023*s
    # At full closure the projected aperture has zero height; a finite front/
    # back lip section remains in Y. Geometry must still pass exact self gates.
    z=(1-amount)*restz+amount*seam;x=c[0]+.012*cs;y=[]
    for xx,zz,ss in zip(x,z,sn):
        h,_,_,_=tree.ray_cast(Vector((xx,-.25,zz)),Vector((0,1,0)),.3)
        yy=float(h.y)-.00040 if h is not None else c[1]-.0038
        yy-=amount*.00030*ss;y.append(yy)
    return np.column_stack((x,y,z))
def patch(V,T,bt,eye,side,amount,baseIndex,prepared=None):
    c=np.array(i.i.FITS[side]['centerM']);tv=V[T];rho=((tv[:,:,0]-c[0])/.0195)**2+((tv[:,:,2]-c[2])/.0175)**2;mask=np.all(rho<1,axis=1)&np.all(tv[:,:,1]<-.093,axis=1);loop=outerloop(V,T,mask);boundary=V[loop];theta=np.unwrap(np.arctan2((boundary[:,2]-c[2])/.0175,(boundary[:,0]-c[0])/.0195));theta=theta-theta[0];theta+=np.arctan2((boundary[0,2]-c[2])/.0175,(boundary[0,0]-c[0])/.0195)
    assert np.min(np.diff(theta))>-.15,('Orbital boundary folds in chart',side,float(np.min(np.diff(theta))))
    n=len(loop);et=i.i.tree(*eye);front=lip(c,theta,amount,et);restfront=lip(c,theta,0,et);rings=[loop.tolist()];positions=[];ringTypes=[]
    def add(P,kind):
        ids=list(range(baseIndex+len(positions),baseIndex+len(positions)+len(P)));positions.extend(P.tolist());rings.append(ids);ringTypes.append(kind)
    # Anterior lid tissue chart. Original source ray provides the rest fold;
    # new topology follows the authored lip and actual globe front clearance.
    for step in range(1,17):
        t=step/16;P=(1-t)*boundary+t*front;RP=(1-t)*boundary+t*restfront
        for j in range(n):
            old,_,_,_=bt.ray_cast(Vector((RP[j,0],-.25,RP[j,2])),Vector((0,1,0)),.3)
            oy=float(old.y) if old is not None else RP[j,1]
            eh0=et.ray_cast(Vector((RP[j,0],-.25,RP[j,2])),Vector((0,1,0)),.3)[0];eh1=et.ray_cast(Vector((P[j,0],-.25,P[j,2])),Vector((0,1,0)),.3)[0]
            dy=float(eh1.y-eh0.y) if eh0 is not None and eh1 is not None else front[j,1]-restfront[j,1]
            P[j,1]=oy+dy*t*t
            if eh1 is not None:P[j,1]=min(P[j,1],float(eh1.y)-.00040)
            # Join lip exactly, independent of original inward-ray surface.
            P[j,1]=(1-t**8)*P[j,1]+t**8*front[j,1]
        add(P,'anterior')
    fv=front-c;fd=normalize(fv);rad=np.linalg.norm(fv,axis=1);eq=normalize(np.column_stack((np.cos(theta),np.full(n,.04),np.sin(theta))))
    def on_eye(d):
        P=[]
        for vec in d:
            h,_,_,_=et.ray_cast(Vector(c+vec*.05),Vector(-vec),.1);assert h is not None
            P.append(np.array(h))
        return np.array(P)
    actualFront=on_eye(fd);extra=rad-np.linalg.norm(actualFront-c,axis=1)
    assert extra.min()>0,('Lip penetrates actual eye',side,float(extra.min()))
    for step in range(1,25):
        t=step/24;d=normalize((1-t)*fd+t*eq);P=on_eye(d)+d*((1-t)*extra+t*.00040)[:,None];add(P,'inner-wall')
    for step in range(1,16):
        t=step/16;d=normalize((1-t)*eq+t*np.array((0.,1.,0.)));P=on_eye(d)+d*.00040;add(P,'posterior')
    faces=[]
    for A,B in zip(rings,rings[1:]):
        for j in range(n):k=(j+1)%n;faces.extend(((A[j],A[k],B[k]),(A[j],B[k],B[j])))
    pole=baseIndex+len(positions);pp=on_eye(np.array(((0.,1.,0.),)))[0]+np.array((0.,.0004,0.));positions.append(pp.tolist())
    for j in range(n):faces.append((rings[-1][j],rings[-1][(j+1)%n],pole))
    return np.array(positions),np.array(faces,dtype='i4'),mask,{'side':side,'boundaryIndices':loop.tolist(),'ringCount':len(rings),'ringVertices':n,'vertices':len(positions),'triangles':len(faces),'minimumLipActualRadialGapM':float(extra.min()),'theta':theta.tolist(),'rings':rings,'ringTypes':ringTypes}
def actual_self(V,T,changed):
    bt=i.i.tree(V,T);ids=np.flatnonzero(changed);pairs=bt.overlap(i.i.tree(V,T[ids]));bad=set()
    for x,y in pairs:
        z=int(ids[y]);x=int(x)
        if x!=z and set(T[x]).isdisjoint(T[z]) and exact.intersections(V[T[x]],V[T[z]]):bad.add(tuple(sorted((x,z))))
    return bt,bad
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects[b.BODY];body.modifiers[0].levels=0;bpy.context.view_layer.update();V,T=b.evaluated(body,True);bt=i.i.tree(V,T);eyes={s:i.i.outer(s) for s in ('L','R')};rows=[]
    save('b-retopology-contract.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'method':'Replace complete native socket disks with explicit source-boundary-welded anterior eyelid charts, finite lip, actual-globe radial interior walls and posterior cap. Independent topology and phase-specific lip shapes; no old angular displacement field or support/harmonic closure.','cheapTest':'Actual native exterior with new topology in open,half,closed states, body/8optics and exact changed self triangles','reject':['Nonmanifold boundary','Folded chart, self intersection, actual optical crossing','Unnatural complete-head appearance after production integration'],'scope':'Topology pilot, not complete character candidate or continuous animation','resources':{'threads':4,'heavyJobs':1,'diagnosticInitialMinutes':10}})
    for value in (0.,.5,1.):
        vv=[V];tt=[];remove=np.zeros(len(T),bool);records={};count=len(V)
        try:
            for side in eyes:
                pv,pt,mask,record=patch(V,T,bt,eyes[side],side,value,count);vv.append(pv);tt.append(pt);remove|=mask;count+=len(pv);records[side]=record
        except Exception as ex:
            save('b-retopology-feasibility.json',{'status':'REJECT_CHART_CONSTRUCTION','blink':value,'error':str(ex),'rows':rows,'seconds':time.time()-tick});raise
        allV=np.vstack(vv);allT=np.vstack((T[~remove],*tt));change=np.arange(len(allT))>=int((~remove).sum());full,selfPairs=actual_self(allV,allT,change);contacts={}
        for side in eyes:
            for part in ('Sclera','Cornea','Iris','Pupil'):
                name=f'AFN30_{side}_{part}';ev,et=b.evaluated(bpy.data.objects[name],True);contacts[name]=len(full.overlap(i.i.tree(ev,et)))
        edges=np.sort(np.concatenate((allT[:,[0,1]],allT[:,[1,2]],allT[:,[2,0]])),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);row={'blink':value,'vertices':len(allV),'triangles':len(allT),'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum()),'actualBodyOpticsPairs':contacts,'actualNonAdjacentSelfPairs':len(selfPairs),'selfExamples':sorted(selfPairs)[:16]};rows.append(row);print('R44_RETOPO_POSE',row,flush=True)
        np.savez_compressed(E/f'b-pilot-{value}.npz',worldPositions=allV,triangles=allT,removedTriangles=remove);save('b-retopology-chart.json',records)
        if any(contacts.values()) or selfPairs or np.any(counts!=2):
            save('b-retopology-feasibility.json',{'status':'REJECT_ACTUAL_TOPOLOGY_SURFACE','rows':rows,'seconds':time.time()-tick,'decision':'Stop this cup-chart construction, preserve evidence; do not expand to child/attachment or animation production.'});return
    save('b-retopology-feasibility.json',{'status':'PASS_NATIVE_RETOPO_KEY_POSES_ONLY','rows':rows,'seconds':time.time()-tick});print('R44_RETOPO_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
