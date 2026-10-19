"""Private static path authoring with adaptive contact vertices.
Not an inextensible solver or hair dynamics. Original roots stay fixed.
Variable POLY topology preserves contact detours; no unsafe resampling follows.
"""
import bpy, importlib.util, json, time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('rod40',Path(__file__).with_name('build-female-next-r0040-complete-guide-constraints.py'));rod=importlib.util.module_from_spec(sp);sp.loader.exec_module(rod)
a=rod.a;m=rod.m;f=rod.f;b=rod.b;v=rod.v;E=rod.E;PVT=rod.PVT

def save(name,x): (E/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def pack(paths,params,path):
    sizes=np.array([len(x) for x in paths],dtype='i4')
    np.savez_compressed(path,positionsWorld=np.concatenate(paths).astype('f4'),parameters=np.concatenate(params),sizes=sizes,offsets=np.r_[0,np.cumsum(sizes)])

def repair(paths,params,tree,tri,radii,limit=16):
    paths=[x.copy() for x in paths];params=[x.copy() for x in params];fixed=np.array([x[0] for x in paths]);history=[]
    for it in range(limit):
        corrected=0;inserted=0
        for ci,P in enumerate(paths):
            delta,stats=rod.query(P[None],tree,tri,float(np.max(radii[ci])),margin=.00035)
            P[1:]+=delta[0,1:];P[0]=fixed[ci];corrected+=stats['active']
        rr=[np.full(len(x),float(np.max(radii[ci]))) for ci,x in enumerate(paths)]
        proof=f.flowcheck.check([x.astype('f4').astype('f8') for x in paths],rr,tree,tri)
        row={'iteration':it,'unqualifiedSegments':proof['unqualifiedSegments'],'roots':len(proof['rootFailures']),'points':sum(map(len,paths)),'correctedPoints':corrected}
        history.append(row);print('R40_ADAPTIVE',row,flush=True)
        if proof['status']=='PASS_TESTED_STATIC_CAPSULES':return paths,params,proof,history
        # check() truncates diagnostics to120; repair those then audit ALL again.
        groups={}
        for q in proof['failureSamples']: groups.setdefault(q['curve'],set()).add(q['segment'])
        for ci,segments in groups.items():
            if len(paths[ci])+len(segments)>512:continue
            P=paths[ci];t=params[ci];Q=[];U=[]
            for j in range(len(P)-1):
                Q.append(P[j]);U.append(t[j])
                if j in segments:
                    mid=(P[j]+P[j+1])*.5
                    dm,_=rod.query(mid[None,None],tree,tri,float(np.max(radii[ci])),margin=.00035)
                    Q.append(mid+dm[0,0]);U.append((t[j]+t[j+1])*.5);inserted+=1
            Q.append(P[-1]);U.append(t[-1]);paths[ci]=np.array(Q);params[ci]=np.array(U)
        if not inserted:break
    rr=[np.full(len(x),float(np.max(radii[ci]))) for ci,x in enumerate(paths)]
    proof=f.flowcheck.check([x.astype('f4').astype('f8') for x in paths],rr,tree,tri)
    return paths,params,proof,history

def make_native(old,paths,radii,name):
    d=old.data.copy();d.name=name
    if len(paths)<len(d.curves):d.remove_curves(indices=list(range(len(paths),len(d.curves))))
    d.resize_curves(sizes=[len(x) for x in paths])
    mx=np.array(old.matrix_world);inv=np.linalg.inv(mx)
    local=(np.concatenate(paths)-mx[:3,3])@inv[:3,:3].T
    d.position_data.foreach_set('vector',local.astype('f4').ravel())
    ar=d.attributes.get('radius');ar.data.foreach_set('value',np.concatenate(radii).astype('f4'))
    obj=old.copy();obj.data=d;obj.name=name
    for mm in list(obj.modifiers):obj.modifiers.remove(mm)
    for k in list(obj.keys()):del obj[k]
    obj['aevrynd_layer']='PRIVATE_ADAPTIVE_STATIC_GROOM';obj['author']='Daniel Bystedt original groom; Aevrynd contact reauthoring'
    obj['license']='Upstream CC BY-SA version unresolved; private study only, not publicly adopted.'
    bpy.context.scene.collection.objects.link(obj);obj.hide_render=False;obj.hide_set(False)
    return obj

def read_native(obj):
    d=obj.data;p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);p=p.reshape(-1,3).astype('f8');mx=np.array(obj.matrix_world);p=p@mx[:3,:3].T+mx[:3,3]
    rr=np.empty(len(d.points),dtype='f4');d.attributes['radius'].data.foreach_get('value',rr);rr=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    return [p[q.first_point_index:q.first_point_index+q.points_length] for q in d.curves],[rr[q.first_point_index:q.first_point_index+q.points_length] for q in d.curves]

def main():
    start=time.time();d=np.load(PVT/'a-rebuilt-guide-paths.npz');rest=d['restPositionsWorld'].astype('f8');paths=list(rest);params=[np.linspace(0,1,len(x)) for x in paths]
    save('b-round-contract.json',{'revision':'female-next-r0040-b-private','source':str(rod.SRC),'sourceSha256':b.sha(rod.SRC),'previousGoalTurnClassification':'progress: v10 prompt maintenance completed; no model appearance improvement',
      'primaryDefect':'Owned full hairstyle cap/sheets; natural reference transfer still contains impossible late paths.',
      'method':'Adaptive POLY contact detours on complete paths, fixed roots, insertion at failed finite segments; no inextensibility claim and no resampling after qualification.',
      'differenceFromA':'Changes path representation rather than more fixed128point length/bend solver passes. A fails11segments and266.7percent local relative stretch; rejected.',
      'privateReference':'Daniel Bystedt, HairStyles demo, upstream CC BY-SA version unresolved; derivatives remain private.',
      'reject':['Any guide or displayed-child finite-segment/root failure','More than40mm authored displacement or severe visible distortion','No believable complete-head improvement'],
      'resources':{'startUTC':'2026-10-19 13:10:11 UTC','checkpointUTC':'2026-10-19 13:55:11 UTC','threads':4,'heavyJobsAtOnce':1,'adaptivePasses':16,'maximumPointsPerCurve':512},
      'scope':'Static geometric reauthoring; not dynamics, self collision, all layers, runtime or formal asset adoption.'})
    bpy.ops.wm.open_mainfile(filepath=str(rod.SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T];f.flowcheck.cap.math_controls()
    paths,params,proof,history=repair(paths,params,tree,tri,[np.array([.000046]) for x in paths])
    displacement=max(float(np.linalg.norm(x-np.column_stack([np.interp(t,np.linspace(0,1,128),r[:,j]) for j in range(3)]),axis=1).max()) for x,t,r in zip(paths,params,rest))
    ratios=np.array([np.linalg.norm(np.diff(x,axis=0),axis=1).sum()/np.linalg.norm(np.diff(r,axis=0),axis=1).sum() for x,r in zip(paths,rest)])
    pack(paths,params,PVT/'b-adaptive-guide-paths.npz');save('b-all-guide-body-contact.json',proof)
    save('b-guide-summary.json',{'body':proof,'history':history,'maximumDisplacementM':displacement,'contourLengthRatioRange':[float(ratios.min()),float(ratios.max())],'nativePoints':sum(map(len,paths)),'fixedRootErrorM':max(float(np.linalg.norm(x[0]-r[0])) for x,r in zip(paths,rest)),'sourceStateExact':f.state()==before,'seconds':time.time()-start,'childrenSelfDynamicsRuntime':'NOT_TESTED'})
    print('R40_B_GUIDES_DONE',proof['status'],proof['unqualifiedSegments'],displacement,ratios.min(),ratios.max(),time.time()-start,flush=True)

if __name__=='__main__':main()
