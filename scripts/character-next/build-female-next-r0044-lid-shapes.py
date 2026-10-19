"""Topology-defined upper/lower corrective lid shapes: cheap cage falsification.

No global angular blink field. Explicit native front socket loop handles, a
shared authored closure curve, graph tissue extension and actual-eye support
planes. Stop before detail/attachments if a key pose violates actual surfaces.
"""
import bpy,importlib.util,json,time,heapq
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('r43for44',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;S=b.S;R=b.R;E=R/'Evidence/character-female-next/r0044-lid-shapes';E.mkdir(exist_ok=True)
SRC=S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend'
q=f.flowcheck.module('native29r44','build-female-next-r0029-native-eye-interface.py')
v=f.flowcheck.module('verify29r44','verify-female-next-r0029-native-eye-interface.py')
inspection=json.loads((R/'Evidence/character-female-next/r0035-neutral-lid-rest/aperture-topology-inspection.json').read_text())
regions=json.loads((R/'Evidence/character-female-next/r0029-native-eye-interface/coarse-feasibility.json').read_text())['regions']
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def world_write(o,P):
    m=np.array(o.matrix_world);a=(P-m[:3,3])@np.linalg.inv(m[:3,:3]).T;o.data.vertices.foreach_set('co',a.astype('f4').ravel());o.data.update();bpy.context.view_layer.update()
def loop_paths(V,side):
    info=inspection['native'][side];ids={int(x['id']) for x in info['wallBoundaryVertices'] if V[x['id'],1]<-.108};adj={v:[] for v in ids}
    for a,c in info['wallBoundaryEdges']:
        if a in ids and c in ids:adj[a].append(c);adj[c].append(a)
    assert all(len(x)==2 for x in adj.values()),(side,adj)
    lo=min(ids,key=lambda x:V[x,0]);hi=max(ids,key=lambda x:V[x,0]);paths=[]
    for n in adj[lo]:
        path=[lo,n]
        while path[-1]!=hi:
            nn=[j for j in adj[path[-1]] if j!=path[-2]];assert len(nn)==1;path.append(nn[0]);assert len(path)<=len(ids)
        paths.append(path)
    paths.sort(key=lambda p:np.mean(V[p,2]),reverse=True)
    return paths
def make_patch(V,polys,adj,side,eye):
    upper,lower=loop_paths(V,side);c=np.array(i.i.FITS[side]['centerM']);et=i.i.tree(*eye);handles={};targets=[]
    for part,path,other in [('upper',upper,lower),('lower',lower,upper)]:
        for vi in path:
            p=V[vi];order=np.argsort(V[other,0]);otherz=float(np.interp(p[0],V[other,0][order],V[other,2][order]));uz=p[2] if part=='upper' else otherz;lz=otherz if part=='upper' else p[2]
            seam=.20*uz+.80*lz;w=np.sin(np.pi*(p[0]-V[upper[0],0])/(V[upper[-1],0]-V[upper[0],0]))**2
            z=seam+(1 if part=='upper' else -1)*.00008*w
            old=et.ray_cast(Vector((p[0],-.25,p[2])),Vector((0,1,0)),.3)[0];new=et.ray_cast(Vector((p[0],-.25,z)),Vector((0,1,0)),.3)[0]
            dy=float(new.y-old.y) if old is not None and new is not None else 0.
            # Upper margin is anterior to lower at closure; retain source gap.
            dy-=.00020*w if part=='upper' else 0.
            d=np.array((0.,dy,z-p[2]));handles[vi]=d;targets.append({'vertex':vi,'part':part,'closedDeltaWorldM':d.tolist(),'closedTargetWorldM':(p+d).tolist()})
    # True topology distance, with pinned orbital/brow/back boundaries.
    dist=np.full(len(V),np.inf);heap=[]
    for vi in handles:dist[vi]=0.;heapq.heappush(heap,(0.,vi))
    while heap:
        d,vi=heapq.heappop(heap)
        if d!=dist[vi] or d>.020:continue
        for n in adj[vi]:
            dd=d+float(np.linalg.norm(V[n]-V[vi]))
            if dd<dist[n]:dist[n]=dd;heapq.heappush(heap,(dd,n))
    eligible=(dist<.016)&(abs(V[:,0]-c[0])<.022)&(V[:,1]<-.097)&(abs(V[:,2]-c[2])<.019)
    domain=set(np.flatnonzero(eligible))|set(handles);fixed={j for j in domain if any(n not in domain for n in adj[j])}|{j for j in domain if not eligible[j]};fixed-=set(handles)
    prescribed={j:np.zeros(3) for j in fixed};prescribed.update(handles);unknown=sorted(domain-set(prescribed));idx={j:k for k,j in enumerate(unknown)};A=np.zeros((len(idx),len(idx)));rhs=np.zeros((len(idx),3))
    for vi,k in idx.items():
        A[k,k]=len(adj[vi])
        for n in adj[vi]:
            if n in idx:A[k,idx[n]]-=1
            elif n in prescribed:rhs[k]+=prescribed[n]
    sol=np.linalg.solve(A,rhs);D=np.zeros_like(V)
    for j,d in prescribed.items():D[j]=d
    for j,d in zip(unknown,sol):D[j]=d
    return D,{'side':side,'upperPath':upper,'lowerPath':lower,'targets':targets,'domain':sorted(map(int,domain)),'fixed':sorted(map(int,fixed))}
def support(V,desired,polys,patches,eyes):
    out=desired.copy();constraints={};rows=[];fixed={j for p in patches.values() for j in p['fixed']};moving=np.linalg.norm(desired-V,axis=1)>1e-10
    for side,(ev,et) in eyes.items():
        center=np.array(i.i.FITS[side]['centerM'])
        for pi in regions[i.i.FITS[side]['name']]['inwardWallFaces']:
            ids=polys[pi]
            if not moving[ids].any():continue
            n=desired[ids].mean(0)-center;n/=np.linalg.norm(n);h=float(np.max(ev@n)+.00008)
            for j in ids:
                if j in fixed or not moving[j]:
                    if h-n@out[j]>1e-6:raise RuntimeError(('Fixed native support conflict',side,pi,j,float(h-n@out[j])))
                else:constraints.setdefault(j,[]).append((n,h))
    for j,cs in constraints.items():out[j],_=q.project(out[j],cs)
    return out,{'constrainedVertices':len(constraints),'maximumContactCorrectionM':float(np.linalg.norm(out-desired,axis=1).max())}
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;body=bpy.data.objects[b.BODY];mult=body.modifiers[0];mult.levels=0;bpy.context.view_layer.update();V,T=b.evaluated(body,True);polys=[list(p.vertices) for p in body.data.polygons];adj={j:set() for j in range(len(V))}
    for e in body.data.edges:a,c=map(int,e.vertices);adj[a].add(c);adj[c].add(a)
    eyes={side:i.i.outer(side) for side in ('L','R')};D=np.zeros_like(V);patches={}
    for side in eyes:dd,p=make_patch(V,polys,adj,side,eyes[side]);D+=dd;patches[side]=p
    save('round-contract.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'previousTurn':'progress: user-requested v11 prompt maintenance completed, no character appearance gain','primaryDefect':'Unchanging staring full-face eyes; existing neutral-gap-only study has insufficient whole-face benefit','hypothesis':'Explicit native upper/lower closure shapes and a shared canthus-to-canthus seam, with actual-eye support, can support credible asymmetric blink rather than global angle fields','cheapTest':'Native half/closed actual body/8optics and changed self before high-resolution sculpt, attachment rebuild or animation','candidateCount':1,'resources':{'startUTC':'2026-10-19 14:41:34 UTC','checkpointUTC':'2026-10-19 15:26:34 UTC','diagnosticInitialDeadlineUTC':'2026-10-19 14:55:00 UTC','threads':4,'heavyJobs':1},'reject':['Native support infeasible','Actual body/optics crossing or changed self','Gross fold/shape distortion or no complete-head function benefit'],'preserved':['Eyeballs/skin/lighting/scalp and original working source','No runtime/site/score promotion'],'reference':{'url':'https://la.disneyresearch.com/publication/modeling-and-animating-eye-blinks/','principle':'Complete closure and asymmetric open/close timing; own authored parameters, no captured data or paper implementation imported'},'scope':'First native shape feasibility; not finished blink or continuous contact proof'})
    save('native-lid-targets.json',patches);poses=[];arrays={}
    for value in (.5,1.):
        try:P,sr=support(V,V+D*value,polys,patches,eyes)
        except Exception as ex:
            save('native-feasibility.json',{'status':'REJECT_NATIVE_SUPPORT','blink':value,'error':str(ex),'poses':poses,'seconds':time.time()-tick});print('R44_REJECT_SUPPORT',str(ex),flush=True);return
        world_write(body,P);pv,pt=b.evaluated(body,True);bt=i.i.tree(pv,pt);contacts={}
        for side in eyes:
            for part in ('Sclera','Cornea','Iris','Pupil'):
                name=f'AFN30_{side}_{part}';ev,et=b.evaluated(bpy.data.objects[name],True);contacts[name]=len(bt.overlap(i.i.tree(ev,et)))
        changed=np.linalg.norm(pv-V,axis=1)>1e-9;selfR,_=v.changed_self(pv,pt,changed,bt);rows={'blink':value,'bodyOpticsPairs':contacts,'bodySelf':selfR,'support':sr,'changedVertices':int(changed.sum()),'maximumMoveM':float(np.linalg.norm(pv-V,axis=1).max())};poses.append(rows);arrays[f'pose{value}']=pv
        save('native-feasibility.json',{'status':'RUNNING_NATIVE_GATE','poses':poses,'seconds':time.time()-tick});print('R44_NATIVE_POSE',value,contacts,selfR['nonAdjacentTrianglePairs'],flush=True)
        if any(contacts.values()) or selfR['nonAdjacentTrianglePairs']:
            np.savez_compressed(E/'rejected-native-shapes.npz',restWorld=V,triangles=pt,**arrays);save('native-feasibility.json',{'status':'REJECT_NATIVE_SURFACE','poses':poses,'seconds':time.time()-tick,'nextDecision':'Stop this native harmonic/support closure route; do not expand details or relax contact tolerances.'});return
    np.savez_compressed(E/'native-shapes.npz',restWorld=V,triangles=pt,**arrays);save('native-feasibility.json',{'status':'PASS_NATIVE_KEY_POSES_ONLY','poses':poses,'seconds':time.time()-tick});print('R44_NATIVE_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
