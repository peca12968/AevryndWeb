"""Audit evaluated changed strands against the displayed neutral skin."""
from pathlib import Path
from runpy import run_path
from time import perf_counter

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
author=run_path(str(ROOT/'author-r0504.py'))
r497=run_path(str(ROOT.parent/'r0497-feathered-rear-locks/native-contact-r0497.py'))
body_helpers=run_path(str(ROOT.parent/'r0498-orbit-cheek/contact-r0498.py'))
r500=run_path(str(author['BASELINE']/'author-r0500.py'))
read_json,write_json,digest,positions,attribute,array_hash=(
    author[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash'))
mesh_data,tree=(body_helpers[k] for k in ('mesh_data','tree'))
ray_counts=r497['probe']['ray_counts']
CHUNK=625


def event(ids,point,radius,slot,distance,role):
    return dict(curveID=int(ids[slot]),positionMetres=point.tolist(),radiusMetres=float(radius),
                signedOrBoundMetres=float(distance),kind=role)


def audit(points,rows,radii,ids,body_tree,state):
    unsigned=np.empty(len(points),'f8')
    outside=np.ones(len(points),dtype=bool)
    oriented=np.empty(len(points),'f8')
    warned=np.zeros(len(points),dtype=bool)
    confirmed_points=np.zeros(len(points),dtype=bool)
    for i,xyz in enumerate(points):
        p=Vector(xyz)
        q,n,_,d=body_tree.find_nearest(p)
        unsigned[i]=d
        s=d if (p-q).dot(n)>=0 else -d
        oriented[i]=s-radii[i]
        if oriented[i]>=0:
            continue
        warned[i]=True
        state['orientedWarnings']+=1
        parity=[num%2 for num in ray_counts(p,body_tree)]
        if all(parity):
            outside[i]=False
            oriented[i]=-d-radii[i]
            state['insideCentres']+=1
            confirmed_points[i]=True
            state['failedCurveIds'].add(int(ids[rows[i]]))
        elif not any(parity):
            oriented[i]=d-radii[i]
            if oriented[i]<0:
                state['radiusOverlapPoints']+=1
                confirmed_points[i]=True
                state['failedCurveIds'].add(int(ids[rows[i]]))
        else:
            outside[i]=False
            state['mixedParityWarnings']+=1
            state['ambiguousCurveIds'].add(int(ids[rows[i]]))
    confirmed=confirmed_points
    minimum=int(np.argmin(oriented))
    sample=event(ids,points[minimum],radii[minimum],rows[minimum],oriented[minimum],
                 'negative with ray recheck' if warned[minimum] else 'positive oriented sample')
    if state['minimumSample'] is None or sample['signedOrBoundMetres']<state['minimumSample']['signedOrBoundMetres']:
        state['minimumSample']=sample
    if confirmed.any():
        selected=np.flatnonzero(confirmed)
        i=selected[np.argmin(oriented[selected])]
        q=event(ids,points[i],radii[i],rows[i],oriented[i],'confirmed negative')
        if state['mostNegativeFailedCurveSample'] is None or q['signedOrBoundMetres']<state['mostNegativeFailedCurveSample']['signedOrBoundMetres']:
            state['mostNegativeFailedCurveSample']=q
    indices=np.flatnonzero(rows[:-1]==rows[1:])
    vec=points[indices+1]-points[indices]
    length=np.linalg.norm(vec,axis=1)
    radius=np.maximum(radii[indices],radii[indices+1])
    lower=.5*(unsigned[indices]+unsigned[indices+1]-length)-radius
    need=(lower<=0.)|(~outside[indices])|(~outside[indices+1])
    state['segments']+=len(indices)
    state['segmentsClearByDistanceBound']+=int(np.count_nonzero(~need))
    state['minimumChordRadiusLowerBoundMetres']=min(state['minimumChordRadiusLowerBoundMetres'],float(lower.min()))
    for k in np.flatnonzero(need):
        i=indices[k]
        a=Vector(points[i])
        d=float(length[k])
        if d<=1.e-8:
            state['unresolvedRadiusSegments']+=1
            continue
        travel=Vector(vec[k]/d)
        hit,_,_,distance=body_tree.ray_cast(a,travel,d)
        if hit is not None and 0.<distance<d:
            state['centrelineCrossingSegments']+=1
            state['failedCurveIds'].add(int(ids[rows[i]]))
            if len(state['crossingWitnesses'])<30:
                state['crossingWitnesses'].append(event(ids,np.asarray(hit),radius[k],rows[i],0.,'centreline triangle crossing'))
            continue
        if not (outside[i] and outside[i+1]):
            state['unresolvedRadiusSegments']+=1
            continue
        mid=(points[i]+points[i+1])*.5
        mid_vec=Vector(mid)
        q,n,_,md=body_tree.find_nearest(mid_vec)
        mid_radius=.5*(radii[i]+radii[i+1])
        if md<mid_radius:
            state['radiusOverlapMidpoints']+=1
            state['failedCurveIds'].add(int(ids[rows[i]]))
            if len(state['crossingWitnesses'])<30:
                state['crossingWitnesses'].append(event(ids,mid,mid_radius,rows[i],md-mid_radius,'midpoint radius overlap'))
        else:
            left=.5*(unsigned[i]+md-.5*d)-radius[k]
            right=.5*(unsigned[i+1]+md-.5*d)-radius[k]
            if min(left,right)>0.:
                state['segmentsClearByDistanceBound']+=1
            else:
                state['unresolvedRadiusSegments']+=1
    state['evaluatedPoints']+=len(points)


def empty():
    return dict(evaluatedPoints=0,orientedWarnings=0,insideCentres=0,radiusOverlapPoints=0,
        mixedParityWarnings=0,segments=0,segmentsClearByDistanceBound=0,centrelineCrossingSegments=0,
        radiusOverlapMidpoints=0,unresolvedRadiusSegments=0,minimumSample=None,mostNegativeFailedCurveSample=None,
        minimumChordRadiusLowerBoundMetres=float('inf'),failedCurveIds=set(),ambiguousCurveIds=set(),crossingWitnesses=[])


def summarize(state):
    return {key:sorted(value) if isinstance(value,set) else value for key,value in state.items()}


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    reopen=read_json(ROOT/'reopen-verification.json')
    source=Path(proof['source']['path'])
    assert digest(source)==proof['source']['sha256'] and proof['source']==reopen['source']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    body,gaze=(bpy.data.objects[proof[k]] for k in ('body','gaze'))
    r500['activate'](scene,gaze,'separated',0.,1.)
    v,f,_=mesh_data(body)
    body_tree=tree(v,f)
    control=bpy.data.objects[proof['controlObject']]
    variants={'control':control,**{label:bpy.data.objects[info['object']] for label,info in proof['variants'].items()}}
    radii=attribute(control.data,'radius').reshape(proof['strands'],proof['pointsPerStrand'])
    ids=attribute(control.data,'AFN409_CURVE_ID')
    assert array_hash(radii)==proof['radiusHash'] and array_hash(ids)==proof['idsHash']
    active=attribute(variants['returned'].data,'AEVRYND_R504_TEMPLE_WEIGHT')>0
    assert np.array_equal(active,attribute(variants['swept'].data,'AEVRYND_R504_TEMPLE_WEIGHT')>0)
    progress=ROOT/'contact-progress.json'
    saved=read_json(progress) if progress.exists() else dict(source=proof['source'],results={})
    assert saved['source']==proof['source']
    results=saved['results']
    for label,obj in variants.items():
        if label in results:
            continue
        for g in scene.objects:
            if g.type=='CURVES':
                g.hide_set(g!=obj)
        bpy.context.view_layer.update()
        bank=positions(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        expected=proof['controlPositionHash'] if label=='control' else proof['variants'][label]['positionHash']
        assert array_hash(bank)==expected
        host,group,lower,upper=r497['make_sample_modifier'](obj)
        state=empty()
        started=perf_counter()
        low_length=2**31
        high_length=0
        for first in range(0,len(ids),CHUNK):
            end=min(first+CHUNK,len(ids))
            if not active[first:end].any():
                continue
            points,rows,r=r497['evaluate_chunk'](host,group,lower,upper,first,end)
            lo,hi=r497['verify_endpoints'](points,rows,r,bank,radii,first,end)
            low_length=min(lo,low_length)
            high_length=max(hi,high_length)
            select=active[rows]
            audit(points[select],rows[select],r[select],ids,body_tree,state)
        data=host.data
        bpy.data.objects.remove(host,do_unlink=True)
        bpy.data.meshes.remove(data)
        bpy.data.node_groups.remove(group)
        row=summarize(state)
        row['elapsedSeconds']=perf_counter()-started
        row['samplesPerCurveRange']=[low_length,high_length]
        row['sampledCurves']=int(active.sum())
        results[label]=row
        print('R504_CONTACT',label,row['evaluatedPoints'],row['insideCentres'],row['radiusOverlapPoints'],
              row['centrelineCrossingSegments'],row['unresolvedRadiusSegments'],row['minimumSample'],flush=True)
        write_json(progress,saved)
    prior=set(results['control']['failedCurveIds'])
    for label in author['MODES']:
        results[label]['addedFailedCurveIds']=sorted(set(results[label]['failedCurveIds'])-prior)
    assert digest(source)==proof['source']['sha256']
    write_json(ROOT/'neutral-contact.json',dict(source=proof['source'],pose='frame 1, neutral face',
        target=body.name,bodyTriangleCount=len(f),scope='All native evaluated points and consecutive chords of the changed strand population, full displayed skin, exact strand IDs. Point sign uses nearest normal and three ray parity queries for warnings. Endpoint and midpoint bounds test the circumscribed radius of each sampled chord. Original carrier has no motion modifiers. Curve self-contact, garment contact and continuous motion were not measured.',
        results=results))


if __name__=='__main__':
    main()

