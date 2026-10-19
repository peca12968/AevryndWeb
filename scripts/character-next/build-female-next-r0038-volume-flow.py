"""r38: root-seeded autonomous 3D flow; no shared scalp exit/ring/lock loft.
Authoring experiment only. Velocity barriers guide growth near actual skin;
finite capsules remain the independent acceptance test. No dynamics claim.
"""
import bpy, importlib.util, json, time, hashlib, math, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def mod(name,file):
    sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=mod('g37flow38','build-female-next-r0037-eye-margin.py')
b=g.b;v=g.v
flowcheck=mod('g33flow38','build-female-next-r0033-parted-bob.py')
R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0038-volume-flow'
SRC=S/'aevrynd-female-next-r0037-c-anatomical-eye-review.blend'
OUT=S/'aevrynd-female-next-r0038-a-root-volume-flow.blend'
OLD='AFN33_C_BODY_BOUND_FIBRES';NEW='AFN38_A_ROOT_VOLUME_FLOW'
def save(n,x):
    E.mkdir(parents=True,exist_ok=True)
    (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def state():
    names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('AFN38')]
    curves={}
    for o in bpy.context.scene.objects:
        if o.type=='CURVES' and not o.name.startswith('AFN38') and (not o.hide_render or o.name==OLD):
            p,r=v.hair_arrays(o)
            curves[o.name]={'positions':sha(p),'radii':sha(r),'matrix':b.matrix(o.matrix_world),
                'materials':[v.v32.material_signature(m) for m in o.data.materials],
                'indices':sha(np.array([x.value for x in o.data.attributes['material_index'].data],dtype='i4'))}
    return {'meshes':{n:flowcheck.signature(bpy.data.objects[n]) for n in names},
            'materials':v.materials(names),'skinFields':v.fields(bpy.data.objects[b.BODY]),
            'curves':curves,'stage':v.stage()}
def velocity(P,tree):
    nearest=[tree.find_nearest(Vector(p)) for p in P]
    normals=np.array([q[1] for q in nearest],dtype='f8')
    distance=np.array([q[3] for q in nearest],dtype='f8')
    x,y,z=P.T;side=np.tanh(x/.004)
    free=np.clip((1.505-z)/.050,0,1);free=free*free*(3-2*free)
    front=np.exp(-((y+.092)/.060)**2)*np.exp(-((z-1.525)/.060)**2)
    phase=2*math.pi*(z-1.365)/.115
    F=np.column_stack((side*(1.45*front+.57*free*np.cos(phase+.25)),
                       .12+.38*free*np.sin(phase+.9),-np.ones(len(P))))
    # The barrier affects velocity, not a post-hoc CV displacement. It is
    # not a signed-distance/contact proof and never marks paths accepted.
    dot=np.einsum('ij,ij->i',F,normals)
    outward=.65*np.exp(-distance/.0025)
    correction=np.where(distance<.018,np.maximum(outward-dot,0),0)
    F+=normals*correction[:,None]
    return F/np.linalg.norm(F,axis=1)[:,None]
def paths(roots,params,tree):
    az,u=params.T
    cut=1.369+.009*np.cos(2*az+.5)+.008*np.sin(5*az+2*u)+.013*(1-u)+.004*np.sin(19*az+11*u)
    P=roots.copy();lists=[[p.copy()] for p in P];alive=np.ones(len(P),bool);step=.0010
    for k in range(440):
        ids=np.flatnonzero(alive)
        if not len(ids):break
        A=P[ids];f=velocity(A,tree);mid=A+.5*step*f
        Z=A+step*velocity(mid,tree)
        done=Z[:,2]<=cut[ids]
        for j,ci in enumerate(ids):
            q=Z[j]
            if done[j]:
                ratio=(A[j,2]-cut[ci])/max(A[j,2]-q[2],1e-12)
                q=A[j]+np.clip(ratio,0,1)*(q-A[j])
            lists[ci].append(q.copy());P[ci]=q
        alive[ids[done]]=False
        if k%60==0:print('R38_FLOW',k,len(ids),flush=True)
    if alive.any():raise RuntimeError(('flow did not reach free tip',int(alive.sum())))
    out=[]
    for pts in lists:
        pts=np.array(pts);arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
        t=np.linspace(0,arc[-1],128)
        out.append(np.column_stack([np.interp(t,arc,pts[:,q]) for q in range(3)]))
    return np.array(out,dtype='f4')
def render(label,views=('face','oblique','profile')):
    g.E=E;g.render(label,views)
def controls(P,body):
    d=bpy.data.curves.new('AFN38_EDITABLE_FLOW_GUIDES','CURVE');d.dimensions='3D';d.resolution_u=1
    for pts in P:
        sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
        sp.points.foreach_set('co',np.column_stack((pts,np.ones(len(pts)))).astype('f4').ravel())
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(True)
    o['aevrynd_layer']='EDITABLE_FLOW_PATH_STUDY';o['scope']='Static editable curve cache; controls do not yet rebuild children live'
    return o
def main():
    start=time.time();E.mkdir(parents=True,exist_ok=True)
    assert b.sha(SRC)=='4d14d272a7ad71b4b5f0fff1d60e793001e7e1620e69636feac8c6c5837db0b9'
    save('round-contract.json',{'revision':'female-next-r0038-a',
      'previousGoalTurnClassification':'progress: user-requested v9 execution prompt and entry points authored, checked, pushed98f7008; no model iteration or appearance progress claimed',
      'source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefect':'Rejected thin scalp cap and flat straight bob curtains dominate complete-head appearance',
      'secondaryDefects':['Mannequin-like facial rendering and large eye catchlights','Body/clothing/face motion and runtime remain unaccepted'],
      'method':'Own autonomous spatial velocity field, mid-point integration from each actual follicle through free3D space, skin-near outward velocity barrier, coherent low-frequency free-volume wave and layered cut',
      'differenceFromStoppedMethods':'No shared scalp exit, common ring, per-lock loft or common terminal control; no averaging root trajectories into a sheet; no post-hoc nearest-CV pushes',
      'reference':[{'url':'https://research.dreamworks.com/wp-content/uploads/2018/07/a36-somasundaram-Edited.pdf','use':'Primary warning that smooth guide interpolation produces artificial sheets and child contacts need independent checking; our flow is an experimental alternative, not implementation of their algorithm.'}],
      'knownDonorStop':'Four local Hair01CC0 meshes already rejected by v271 as lowpoly/shells; HairEditor already studiedr12. No reimport/research loop.',
      'expectedVisibleChange':'Continuous scalp-to-free paths, readable wavy bob silhouette and depth instead of straight thin curtains; skin/exposure/eye/brow/lash layers exact',
      'smallTest':'256 evenly indexed actual root trajectories and finite segment/body capsules before any full12k growth',
      'reject':['Pilot body/root failure','Complete-head cap/sheet/funnel or detached/inflated root silhouette','No readable full-head benefit'],
      'candidateCount':1,'resourceCheckpointMinutes':45,'threads':4,'heavyJobsAtOnce':1,
      'startUTC':'2026-10-19 11:26:41 UTC','checkpointUTC':'2026-10-19 12:11:41 UTC',
      'scope':'Static hairstyle authoring candidate only; no dynamics/self/contact/runtime acceptance by construction'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene
    b.setup(s,b.config(s));before=state();save('source-state.json',before)
    assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0
    old=bpy.data.objects[OLD];p,r=v.hair_arrays(old);mx=np.array(old.matrix_world)
    world=p.astype('f8')@mx[:3,:3].T+mx[:3,3]
    cache=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');params=cache['scalpParams']
    V,T=b.evaluated(bpy.data.objects[b.BODY],True)
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    ids=np.linspace(0,len(p)-1,256,dtype=int);pilot=paths(world[ids,0],params[ids],tree)
    # Match stored local/world precision and native radius policy.
    pilotR=r[ids].astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    audit=flowcheck.check(pilot.astype('f8'),pilotR,tree,tri);save('a-pilot-body-contact.json',audit)
    np.savez_compressed(S/'aevrynd-female-next-r0038-a-pilot.npz',positions=pilot,rootIds=ids,radii=r[ids])
    if audit['status']!='PASS_TESTED_STATIC_CAPSULES':
        controls(pilot,bpy.data.objects[b.BODY]);bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(S/'aevrynd-female-next-r0038-a-flow-pilot-failed.blend'),compress=True)
        save('a-build.json',{'decision':'PILOT_FAILED_STOP_NO_FULL_EXPANSION','audit':audit,'seconds':time.time()-start})
        return
    print('R38_PILOT_PASS',time.time()-start,flush=True)
    Q=paths(world[:,0],params,tree)
    # All actual follicles retained; invert the exact source object matrix.
    inverse=np.linalg.inv(mx);local=((Q.astype('f8')-mx[:3,3])@inverse[:3,:3].T).astype('f4')
    local[:,0]=p[:,0]
    d=old.data.copy();d.name=NEW
    d.position_data.foreach_set('vector',local.ravel())
    o=old.copy();o.data=d;o.name=NEW;bpy.context.scene.collection.objects.link(o)
    o['aevrynd_layer']='SCALP_HAIR_FIBRES';o['scope']='r38A static visual candidate; not qualified self/dynamic/runtime'
    old.hide_render=True;old.hide_set(True);controls(Q[ids],bpy.data.objects[b.BODY])
    bpy.context.view_layer.update();actual,rr=v.hair_arrays(o)
    assert np.array_equal(actual,local) and np.array_equal(rr,r)
    assert state()==before
    render('a-after')
    o.hide_render=True;old.hide_render=False;render('before')
    o.hide_render=False;old.hide_render=True
    b.camera('face');s.camera.data.lens=85
    s['AFN38_status']='STATIC_VISUAL_CANDIDATE_UNQUALIFIED_SELF_MOTION_RUNTIME'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(S/'aevrynd-female-next-r0038-a-flow-fibres.npz',positions=actual,radii=rr,
        rootTriangles=cache['rootTriangles'],rootBarycentric=cache['rootBarycentric'],scalpParams=params)
    save('a-build.json',{'decision':'AWAIT_COMPLETE_HEAD_VISUAL_REVIEW','output':str(OUT),'outputSha256':b.sha(OUT),
       'cache':str(S/'aevrynd-female-next-r0038-a-flow-fibres.npz'),'sourceExactExceptScalpVisibility':True,
       'radiiRootsMaterialsPrimitiveExact':True,'curves':len(Q),'pointsPerCurve':128,
       'pilot':audit,'fullChildrenContact':'NOT_YET_TESTED','self':'NOT_TESTED','dynamics':'NOT_IMPLEMENTED','runtime':'NOT_IMPLEMENTED',
       'sourceHairRootPositionsSha256':sha(p[:,0]),'newHairRootPositionsSha256':sha(actual[:,0]),
       'seconds':time.time()-start})
    print('R38_BUILD_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
