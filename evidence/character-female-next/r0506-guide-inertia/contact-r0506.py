"""Audit native finite-radius curve chords against the actual posed skin."""
from pathlib import Path
from runpy import run_path
from math import atan2,degrees
import bpy
from mathutils import Matrix
import numpy as np

ROOT=Path(__file__).resolve().parent
preview=run_path(str(ROOT/'preview-r0506.py'))
contact=preview['author']['contact']
read_json,write_json,digest,attribute,array_hash,r500=(
    preview[k] for k in ('read_json','write_json','digest','attribute','array_hash','r500'))
modes=preview['modes']


def population(hair,rest,bake,frame):
    n=len(rest)
    ranks=set(range(0,n,29))
    temple=attribute(hair.data,'AEVRYND_R504_TEMPLE_GROUP')>=0
    bridge=attribute(hair.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0.
    for group in (temple,bridge):
        ranks.update(np.flatnonzero(group)[::9].tolist())
    for mode in modes[1:]:
        offset=preview['expected_offset'](bake,rest,mode,frame)
        ranking=np.max(np.linalg.norm(offset,axis=2),axis=1)
        for side in (-1,1):
            rows=np.flatnonzero(rest[:,0,0]*side>0)
            best=rows[np.argsort(ranking[rows],kind='stable')[-385:]]
            ranks.update(best.tolist())
    active=np.zeros(n,dtype=bool)
    active[sorted(ranks)]=True
    return active


def projection_diagnostic(scene,skin,gaze,hair,rest,bake,proof):
    author=preview['author']
    r500['activate'](scene,gaze,'separated',0.,1.)
    vertices,faces,_=contact['mesh_data'](skin)
    local=contact['xform'](vertices,np.asarray(hair.matrix_world.inverted()))
    near=local[faces,2].max(1)>1.265
    bvh=contact['tree'](local,faces[near])
    guide=rest[bake['guideRows']][:,bake['stations']].astype('f8')
    matrices=[Matrix(m) for m in bake['matrices']]
    events=[]
    calls=0

    def record(p,inverse,matrix,bvh,clearance):
        nonlocal calls
        before=p.copy()
        hits,magnitude=author['collision'](p,inverse,matrix,bvh,clearance)
        calls+=1
        if hits:
            distance=np.linalg.norm(p-before,axis=2)
            for i,j in np.argwhere(distance>0):
                previous=contact['xform'](before[i,j],inverse)
                current=contact['xform'](p[i,j],inverse)
                events.append(dict(frame=2+(calls-1)//author['SUBSTEPS'],substep=1+(calls-1)%author['SUBSTEPS'],
                    guideCurveId=int(bake['curveIDs'][i]),controlIndex=int(bake['stations'][j]),
                    guideRow=int(i),station=int(j),correctionMm=float(distance[i,j]*1000.),
                    beforeLocalMetres=previous.tolist(),afterLocalMetres=current.tolist(),
                    signedBeforeMm=float(author['signed'](previous,bvh)[0]*1000.),
                    signedAfterMm=float(author['signed'](current,bvh)[0]*1000.)))
        return hits,magnitude

    def identity(p,inverse,matrix,bvh,clearance):
        return 0,0.

    solve=author['solve']
    reproduced,stats=solve(guide,matrices,bvh,proof['motionFps'],'rod',project_collision=record)
    error=float(np.max(np.abs(reproduced-bake['rod'])))
    assert error<5e-7,error
    ablation,ablation_stats=solve(guide,matrices,bvh,proof['motionFps'],'rod',project_collision=identity)
    step=np.linalg.norm(np.diff(reproduced,axis=0),axis=3)
    f,i,j=np.unravel_index(step.argmax(),step.shape)
    row=dict(source=proof['source'],reproductionMaxErrorMetres=error,projectionEvents=events,
        maximumStep=dict(frame=int(f+2),guideCurveId=int(bake['curveIDs'][i]),controlIndex=int(bake['stations'][j]),
                         projectedMm=float(step[f,i,j]*1000.),
                         withoutProjectionMm=float(np.linalg.norm(ablation[f+1,i,j]-ablation[f,i,j])*1000.)),
        bakedPeakTipMm=stats['peakTipMetres']*1000.,diagnosticNoProjectionPeakTipMm=ablation_stats['peakTipMetres']*1000.,
        largestProjection=max(events,key=lambda row:row['correctionMm']),
        scope='Reproduced the saved rod bank, then bypassed only knot projection in memory. The ablation is a diagnostic with no source or render output. It isolates the projection as a contributor and does not identify mesh topology or algorithm as the underlying cause.')
    write_json(ROOT/'projection-diagnostic.json',row)
    print('R506_PROJECTION_DIAGNOSTIC',error,row['bakedPeakTipMm'],row['diagnosticNoProjectionPeakTipMm'],flush=True)


def main():
    proof,scene,hair,skin,gaze,rest,bake=preview['open_source']()
    reopened=read_json(ROOT/'reopen-verification.json')
    assert proof['source']==reopened['source']
    ids=attribute(hair.data,'AFN409_CURVE_ID')
    radius=attribute(hair.data,'radius').reshape(rest.shape[:2])
    assert array_hash(radius)==proof['radiusHash']
    if not (ROOT/'projection-diagnostic.json').exists():
        projection_diagnostic(scene,skin,gaze,hair,rest,bake,proof)
    rig=hair.parent
    r500['activate'](scene,gaze,'separated',0.,1.)
    head0=(rig.matrix_world@rig.pose.bones['Head'].matrix).inverted()
    apex=reopened['rodGuideApexFrame']
    rebound=17
    frames=sorted(set((apex,12,rebound)))
    path=ROOT/'contact-progress.json'
    report=read_json(path) if path.exists() else dict(source=proof['source'],target=skin.name,frames={},
        scope='Same deterministically selected population for all three modes per pose. At each sampled frame includes fixed systematic samples, temple and bridge strata, and the highest displacement trajectories on both sides. Checks evaluated Blender spline samples, chords and interpolated strand radii against actual evaluated posed skin. Discrete pose sample only.')
    assert report['source']==proof['source']
    for frame in frames:
        active=population(hair,rest,bake,frame)
        r500['activate'](scene,gaze,'separated',0.,float(frame))
        matrix=rig.matrix_world@rig.pose.bones['Head'].matrix@head0
        vertices,faces,_=contact['mesh_data'](skin)
        target=contact['tree'](vertices,faces)
        label=str(frame)
        pose=report['frames'].setdefault(label,dict(frame=frame,
            yawDegrees=degrees(atan2(matrix[1][0],matrix[0][0])),
            population=ids[active].tolist(),populationHash=array_hash(ids[active]),results={}))
        assert pose['populationHash']==array_hash(ids[active])
        for mode in modes:
            if mode in pose['results']:
                continue
            preview['mode_set'](hair,proof,mode)
            bank=preview['evaluated'](hair)
            h=array_hash(bank)
            if f'{mode}:{frame}' in reopened['verified']:
                assert h==reopened['verified'][f'{mode}:{frame}']['positionHash']
            result=contact['measure_mode'](hair,bank,active,ids,radius,target)
            result['positionHash']=h
            pose['results'][mode]=result
            if mode!='rigid':
                base=pose['results']['rigid']
                result['newFailedCurveIds']=sorted(set(result['failedCurveIds'])-set(base['failedCurveIds']))
            write_json(path,report)
            print('R506_CONTACT',frame,mode,result['sampledCurves'],result['evaluatedPoints'],
                  result['insideCentres'],result['centrelineCrossingSegments'],result['unresolvedRadiusSegments'],
                  len(result.get('newFailedCurveIds',[])),flush=True)
    assert digest(Path(proof['source']['path']))==proof['source']['sha256']
    write_json(ROOT/'skin-contact.json',report)


if __name__=='__main__':
    main()

