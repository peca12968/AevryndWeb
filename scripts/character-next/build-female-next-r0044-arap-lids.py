"""Third and final distinct pilot: intrinsic rim chart + ARAP tissue.

The rejected X/Z seam flattens a nonmonotone canthal loop. Here opposite
curves correspond by arc length, retain a finite anterior/posterior lip,
and extend through local rotations rather than harmonic displacement.
"""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('native44c',Path(__file__).with_name('build-female-next-r0044-lid-shapes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;i=a.i;E=a.E;S=a.S;SRC=a.SRC
exact=a.f.flowcheck.module('exact44c','verify-female-next-r0037-eye-margin.py')
def save(n,x):a.save(n,x)
def arc(P):return np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]/np.sum(np.linalg.norm(np.diff(P,axis=0),axis=1))
def interp(P,t,u):return np.column_stack([np.interp(u,t,P[:,j]) for j in range(3)])
def targets(V,side,tree):
    upper,lower=a.loop_paths(V,side);U=V[upper];L=V[lower];tu=arc(U);tl=arc(L);handles={};rows=[]
    for part,path,P,tt,op,ot in [('upper',upper,U,tu,L,tl),('lower',lower,L,tl,U,tu)]:
        other=interp(op,ot,tt);seam=.20*P+.80*other if part=='upper' else .20*other+.80*P
        for vi,p,goal,t in zip(path,P,seam,tt):
            w=np.sin(np.pi*t)**2
            h0=tree.ray_cast(Vector((p[0],-.25,p[2])),Vector((0,1,0)),.3)[0];h1=tree.ray_cast(Vector((goal[0],-.25,goal[2])),Vector((0,1,0)),.3)[0]
            goal[1]=p[1]+(float(h1.y-h0.y) if h0 is not None and h1 is not None else 0.)
            # Finite lip cross-section; zero projected aperture is a target,
            # not proof of visible closure or absence of self contact.
            goal[1]-=.00035*w if part=='upper' else 0.
            handles[int(vi)]=goal-p;rows.append({'vertex':int(vi),'part':part,'intrinsicArcFraction':float(t),'closedTargetWorldM':goal.tolist()})
    return handles,rows
def solve(V,adj,patch,handles,value):
    dom=patch['domain'];fixed=set(patch['fixed']);prescribed={j:V[j].copy() for j in fixed};prescribed.update({j:V[j]+d*value for j,d in handles.items()});unknown=sorted(set(dom)-set(prescribed));idx={j:k for k,j in enumerate(unknown)};A=np.zeros((len(idx),len(idx)));bound=np.zeros((len(idx),3))
    for j,k in idx.items():
        A[k,k]=len(adj[j])
        for n in adj[j]:
            if n in idx:A[k,idx[n]]-=1
            else:bound[k]+=prescribed.get(n,V[n])
    inv=np.linalg.inv(A);P=V.copy();rot=np.broadcast_to(np.eye(3),(len(V),3,3)).copy();domain=sorted(set(dom));edges=[(j,n) for j in domain for n in adj[j]];jj=np.array([j for j,n in edges]);nn=np.array([n for j,n in edges]);rest=V[jj]-V[nn]
    for j,p in prescribed.items():P[j]=p
    energies=[]
    for step in range(32):
        current=P[jj]-P[nn];S=np.zeros((len(V),3,3));np.add.at(S,jj,rest[:,:,None]*current[:,None,:]);u,sv,vh=np.linalg.svd(S[domain]);r=vh.transpose(0,2,1)@u.transpose(0,2,1);negative=np.linalg.det(r)<0;vh[negative,-1]*=-1;r=vh.transpose(0,2,1)@u.transpose(0,2,1);rot[domain]=r
        rhs=np.zeros((len(V),3));desired=.5*np.einsum('nij,nj->ni',rot[jj]+rot[nn],rest);np.add.at(rhs,jj,desired);P[unknown]=inv@(rhs[unknown]+bound)
        err=float(np.linalg.norm(current-desired,axis=1).mean());energies.append(err)
    return P,{'arapIterations':32,'meanEdgeResidualSequenceM':energies,'unknowns':len(idx)}
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects[b.BODY];body.modifiers[0].levels=0;bpy.context.view_layer.update();V,T=b.evaluated(body,True);polys=[list(p.vertices) for p in body.data.polygons];adj={j:set() for j in range(len(V))}
    for e in body.data.edges:x,y=map(int,e.vertices);adj[x].add(y);adj[y].add(x)
    eyes={s:i.i.outer(s) for s in ('L','R')};patches={};handles={};targetsReport={}
    for side in eyes:
        _,patch=a.make_patch(V,polys,adj,side,eyes[side]);patches[side]=patch;handles[side],targetsReport[side]=targets(V,side,i.i.tree(*eyes[side]))
    save('c-arap-contract.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'method':'Intrinsic arc-length correspondence for opposite eyelid margins, finite closed-lip Y section, local/global ARAP tissue shape solve and actual-eye support gate. Addresses nonmonotone source canthus chart rather than changing prior amplitude/tolerance.','candidateCountTotal':3,'stop':'Final distinct pilot this round; any unresolved actual self/eye contact stops production expansion.','scope':'Native key-pose feasibility only, no animation/appearance qualification'});save('c-intrinsic-rim-targets.json',targetsReport);rows=[];arrays={}
    for value in (.5,1.):
        P=V.copy();solveRows={}
        for side in eyes:
            p,sr=solve(V,adj,patches[side],handles[side],value);P+=p-V;solveRows[side]=sr
        try:P,sr=a.support(V,P,polys,patches,eyes)
        except Exception as ex:save('c-arap-feasibility.json',{'status':'REJECT_SUPPORT_CONFLICT','error':str(ex),'blink':value,'rows':rows,'seconds':time.time()-tick});return
        a.world_write(body,P);pv,pt=b.evaluated(body,True);bt=i.i.tree(pv,pt);contacts={}
        for side in eyes:
            for part in ('Sclera','Cornea','Iris','Pupil'):
                name=f'AFN30_{side}_{part}';ev,et=b.evaluated(bpy.data.objects[name],True);contacts[name]=len(bt.overlap(i.i.tree(ev,et)))
        changed=np.linalg.norm(pv-V,axis=1)>1e-9;selfR,selfPairs=a.v.changed_self(pv,pt,changed,bt);actual=[(x,y) for x,y in selfPairs if exact.intersections(pv[pt[x]],pv[pt[y]])];row={'blink':value,'actualBodyOpticsPairs':contacts,'broadSelfPairs':len(selfPairs),'actualNonAdjacentSelfPairs':len(actual),'actualSelfExamples':actual[:20],'support':sr,'arap':solveRows,'maximumDisplacementM':float(np.linalg.norm(pv-V,axis=1).max())};rows.append(row);arrays[f'pose{value}']=pv;np.savez_compressed(E/'c-native-shapes.npz',restWorld=V,triangles=pt,**arrays);save('c-arap-feasibility.json',{'status':'RUNNING','rows':rows,'seconds':time.time()-tick});print('R44_ARAP_POSE',value,len(actual),contacts,flush=True)
        if any(contacts.values()) or actual:save('c-arap-feasibility.json',{'status':'REJECT_ACTUAL_NATIVE_CONTACT','rows':rows,'seconds':time.time()-tick,'decision':'Stop all three pilot families this round. No full candidate, attachment expansion or animation qualification.'});return
    save('c-arap-feasibility.json',{'status':'PASS_NATIVE_ARAP_KEY_POSES_ONLY','rows':rows,'seconds':time.time()-tick});print('R44_ARAP_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
