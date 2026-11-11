"""Check the full edited strand population on neutral and turned display meshes."""
from pathlib import Path
from runpy import run_path
from time import perf_counter
import math

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
study=run_path(str(ROOT/'author-r0505.py'))
template=run_path(str(study['SOURCE_ROUND']/'contact-r0504.py'))
r497=template['r497']
r500=study['r500']
read_json,write_json,digest,positions,attribute,array_hash=(
    study[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash'))
mesh_data,tree=(template[k] for k in ('mesh_data','tree'))
CHUNK=625


def xform(points,matrix):
    return points@matrix[:3,:3].T+matrix[:3,3]


def follicle_frame(v,tri,weights,offset):
    points=v[tri]
    u=study['base']['normalized'](points[:,1]-points[:,0])
    n=study['base']['normalized'](np.cross(u,points[:,2]-points[:,0]))
    t=np.cross(n,u)
    return np.sum(points*weights[:,:,None],axis=1)+u*offset[:,0,None]+t*offset[:,1,None]+n*offset[:,2,None]


def error_summary(residual,ids):
    distance=np.linalg.norm(residual,axis=1)
    i=int(distance.argmax())
    return dict(maximumMetres=float(distance[i]),p95Metres=float(np.percentile(distance,95)),
        worstCurveID=int(ids[i]),worstDeltaMetres=residual[i].tolist())


def select_poses(scene,gaze,rig):
    r500['activate'](scene,gaze,'separated',0.,1.)
    h0=rig.matrix_world@rig.pose.bones['Head'].matrix
    samples={}
    for frame in (*range(1,13),37):
        r500['activate'](scene,gaze,'separated',0.,float(frame))
        current=(rig.matrix_world@rig.pose.bones['Head'].matrix)@h0.inverted()
        yaw=math.degrees(math.atan2(current[1][0],current[0][0]))
        samples[frame]=yaw
    end=samples[37]
    intermediate=[i for i in range(2,13) if .1*abs(end)<abs(samples[i])<.9*abs(end)]
    poses=[(1.,0.)]
    if intermediate:
        frame=min(intermediate,key=lambda i:abs(samples[i]-end*.5))
        poses.append((float(frame),.48))
    poses.append((37.,.75))
    return poses,samples


def measure_mode(obj,bank,active,ids,radii,body_tree):
    host,group,low,high=r497['make_sample_modifier'](obj)
    state=template['empty']()
    started=perf_counter()
    matrix=np.asarray(obj.matrix_world)
    minimum=2**31
    maximum=0
    source_space=set()
    world_bank=None
    try:
        for first in range(0,len(ids),CHUNK):
            end=min(first+CHUNK,len(ids))
            if not active[first:end].any():
                continue
            points,rows,r=r497['evaluate_chunk'](host,group,low,high,first,end)
            curve_ids,starts=np.unique(rows,return_index=True)
            endpoint_error_local=np.linalg.norm(points[starts]-bank[curve_ids,0],axis=1).max()
            endpoint_error_world=np.linalg.norm(points[starts]-xform(bank[curve_ids,0],matrix),axis=1).max()
            if endpoint_error_local<=2e-7:
                a,b=r497['verify_endpoints'](points,rows,r,bank,radii,first,end)
                points=xform(points,matrix)
                source_space.add('object local, transformed with evaluated carrier matrix')
            else:
                assert endpoint_error_world<2e-7,(endpoint_error_local,endpoint_error_world)
                if world_bank is None:
                    world_bank=xform(bank,matrix)
                a,b=r497['verify_endpoints'](points,rows,r,world_bank,radii,first,end)
                source_space.add('world')
            minimum=min(minimum,a)
            maximum=max(maximum,b)
            pick=active[rows]
            template['audit'](points[pick],rows[pick],r[pick],ids,body_tree,state)
    finally:
        data=host.data
        bpy.data.objects.remove(host,do_unlink=True)
        bpy.data.meshes.remove(data)
        bpy.data.node_groups.remove(group)
    row=template['summarize'](state)
    row.update(elapsedSeconds=perf_counter()-started,sampleSpaces=sorted(source_space),
        samplesPerCurveRange=[minimum,maximum],sampledCurves=int(active.sum()),
        evaluatedWorldMatrix=matrix.tolist())
    return row


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    reopen=read_json(ROOT/'reopen-verification.json')
    p=Path(proof['source']['path'])
    assert digest(p)==proof['source']['sha256'] and proof['source']==reopen['source']
    bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    body,gaze,rig,scalp=(bpy.data.objects[proof[name]] for name in ('body','gaze','rig','scalp'))
    control=bpy.data.objects[proof['controlObject']]
    variants={'control':control,**{mode:bpy.data.objects[v['object']] for mode,v in proof['variants'].items()}}
    r500['activate'](scene,gaze,'separated',0.,1.)
    study['bind_head'](control,rig)
    bank={label:positions(obj) for label,obj in variants.items()}
    for mode,row in bank.items():
        expected=proof['controlPositionHash'] if mode=='control' else proof['variants'][mode]['positionHash']
        assert array_hash(row)==expected and np.array_equal(row[:,0],bank['control'][:,0])
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radii=attribute(control.data,'radius').reshape(bank['control'].shape[:2])
    assert array_hash(ids)==proof['idsHash'] and array_hash(radii)==proof['radiusHash']
    active=np.zeros(len(ids),dtype=bool)
    for mode in study['MODES']:
        active|=attribute(variants[mode].data,'AEVRYND_R505_BRIDGE_WEIGHT')>0
    f0=attribute(control.data,'AFN409_SKIN_TRIANGLE_ID')
    scalp.data.calc_loop_triangles()
    t0=np.empty((len(scalp.data.loop_triangles),3),'i4')
    scalp.data.loop_triangles.foreach_get('vertices',t0.ravel())
    tri=t0[f0]
    w=attribute(control.data,'AFN409_SKIN_BARYCENTRIC').astype('f8')
    off=attribute(control.data,'AEVRYND_ROOT_OFFSET_LOCAL').astype('f8')
    v,f,_=mesh_data(body)
    assert v.shape[0]==len(scalp.data.vertices)
    exact_roots=bank['control'][:,0]
    neutral_matrix=np.asarray(control.matrix_world)
    neutral=xform(exact_roots,neutral_matrix)-follicle_frame(v,tri,w,off)
    poses,angles=select_poses(scene,gaze,rig)
    progress=ROOT/'contact-progress.json'
    saved=read_json(progress) if progress.exists() else dict(source=proof['source'],results={})
    assert saved['source']==proof['source']
    all_results=saved['results']
    for frame,phase in poses:
        label=f'{frame:g}:{phase:g}'
        r500['activate'](scene,gaze,'separated',phase,frame)
        vertices,triangles,_=mesh_data(body)
        tree_=tree(vertices,triangles)
        target=follicle_frame(vertices,tri,w,off)
        matrix=np.asarray(control.matrix_world)
        drift=xform(exact_roots,matrix)-target
        relative=(matrix@np.linalg.inv(neutral_matrix))[:3,:3]
        pose=all_results.setdefault(label,dict(headingDegrees=angles[int(frame)],results={},
            rootAbsolute=error_summary(drift,ids),rootDriftBeyondNeutral=error_summary(drift-neutral@relative.T,ids),
            changedPopulationRootDriftBeyondNeutral=error_summary((drift-neutral@relative.T)[active],ids[active])))
        for mode,obj in variants.items():
            if mode in pose['results']:
                continue
            assert np.max(abs(np.asarray(obj.matrix_world)-matrix))<3e-7
            for g in scene.objects:
                if g.type=='CURVES':
                    g.hide_set(g!=obj)
            bpy.context.view_layer.update()
            row=measure_mode(obj,bank[mode],active,ids,radii,tree_)
            pose['results'][mode]=row
            write_json(progress,saved)
            print('R505_CONTACT',label,mode,row['evaluatedPoints'],row['insideCentres'],row['centrelineCrossingSegments'],
                  row['unresolvedRadiusSegments'],row['minimumSample'],flush=True)
    for pose in all_results.values():
        base_failures=set(pose['results']['control']['failedCurveIds'])
        for mode in study['MODES']:
            row=pose['results'][mode]
            row['addedFailedCurveIds']=sorted(set(row['failedCurveIds'])-base_failures)
    assert digest(p)==proof['source']['sha256']
    write_json(ROOT/'skin-contact.json',dict(source=proof['source'],target=body.name,
        rootNeutralError=error_summary(neutral,ids),sampledYawDegrees=angles,results=all_results,
        scope='All native samples and consecutive chords in the modified strand population. Neutral and distinct held head turns, with real evaluated skin. Control and candidates use identical calibrated head attachment for comparison. No secondary hair physics, continuous collision or garment and inter-strand contact claim.'))


if __name__=='__main__':
    main()

