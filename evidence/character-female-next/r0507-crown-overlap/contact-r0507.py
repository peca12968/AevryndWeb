"""Test matched native curves against the neutral and posed skin collider."""
from pathlib import Path
from runpy import run_path
from math import atan2,degrees
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
preview=run_path(str(ROOT/'preview-r0507.py'))
check=run_path(str(ROOT.parent/'r0505-ear-nape-bridge'/'contact-r0505.py'))
read_json,write_json,digest,array_hash,positions,attribute,r500=(
    preview[k] for k in ('read_json','write_json','digest','array_hash','positions','attribute','r500'))


def root_witness(scene,body,gaze,control,proof,base,ids):
    scalp=bpy.data.objects[proof['scalp']]
    f0=attribute(control.data,'AFN409_SKIN_TRIANGLE_ID')
    scalp.data.calc_loop_triangles()
    t0=np.empty((len(scalp.data.loop_triangles),3),'i4')
    scalp.data.loop_triangles.foreach_get('vertices',t0.ravel())
    triangle=t0[f0]
    barycentric=attribute(control.data,'AFN409_SKIN_BARYCENTRIC').astype('f8')
    offset=attribute(control.data,'AEVRYND_ROOT_OFFSET_LOCAL').astype('f8')
    v,_,_=check['mesh_data'](body)
    assert len(v)==len(scalp.data.vertices)
    roots=base[:,0]
    reference=check['follicle_frame'](v,triangle,barycentric,offset)
    original=np.asarray(control.matrix_world)
    residual=check['xform'](roots,original)-reference

    def measure(vertices):
        p=check['follicle_frame'](vertices,triangle,barycentric,offset)
        m=np.asarray(control.matrix_world)
        observed=check['xform'](roots,m)-p
        relative=(m@np.linalg.inv(original))[:3,:3]
        return dict(absolute=check['error_summary'](observed,ids),
            beyondNeutral=check['error_summary'](observed-residual@relative.T,ids))

    return measure


def main():
    proof,scene,carrier,gaze,banks=preview['render_source']()
    body,rig=(bpy.data.objects[proof[name]] for name in ('body','rig'))
    reopen=read_json(ROOT/'reopen-verification.json')
    decision=read_json(ROOT/'visual-decision.json')
    assert proof['source']==reopen['source']==decision['source']
    control=carrier
    base=banks['control']
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radius=attribute(control.data,'radius').reshape(base.shape[:2])
    active=attribute(carrier.data,'AEVRYND_R507_LAYER')>=0
    assert array_hash(radius)==proof['radiusHash'] and array_hash(ids)==proof['idsHash']
    for mode,item in proof['variants'].items():
        assert active.sum()==item['changedStrands']
        assert np.array_equal(active,np.any(banks[mode]!=base,axis=(1,2)))
    head0=(rig.matrix_world@rig.pose.bones['Head'].matrix).inverted()
    measure_roots=root_witness(scene,body,gaze,control,proof,base,ids)
    path=ROOT/'contact-progress.json'
    results=read_json(path) if path.exists() else dict(source=proof['source'],target=body.name,poses={},
        decision=decision['decision'],contactCarrier=carrier.name,changedStrandCount=int(active.sum()),persistentCurveIDs=ids[active].tolist(),
        scope='Every native evaluated spline sample and adjacent chord of each changed curve, finite radii, and matched posed display skin for the listed frames. No continuous-time, inter-strand, or garment contact certification.')
    assert results['source']==proof['source'] and results['decision']==decision['decision']
    for frame,blink,modes in decision['contactPlan']:
        r500['activate'](scene,gaze,'separated',blink,float(frame))
        M=rig.matrix_world@rig.pose.bones['Head'].matrix@head0
        verts,faces,_=check['mesh_data'](body)
        target=check['tree'](verts,faces)
        pose=results['poses'].setdefault(str(frame),dict(frame=frame,blink=blink,
            yawDegrees=degrees(atan2(M[1][0],M[0][0])),root=measure_roots(verts),modes={}))
        for mode in modes:
            if mode in pose['modes']:
                continue
            preview['set_positions'](carrier,banks[mode])
            bank=preview['evaluate'](carrier)
            h=array_hash(bank)
            assert h==reopen['replay'][mode]['positionHash'] and np.array_equal(bank[:,:8],base[:,:8])
            row=check['measure_mode'](carrier,bank,active,ids,radius,target)
            row['positionHash']=h
            if mode!='control':
                control_failures=set(pose['modes']['control']['failedCurveIds'])
                row['newFailedCurveIds']=sorted(set(row['failedCurveIds'])-control_failures)
            pose['modes'][mode]=row
            write_json(path,results)
            print('R507_CONTACT',frame,mode,row['sampledCurves'],row['evaluatedPoints'],
                  row['insideCentres'],row['radiusOverlapPoints'],row['centrelineCrossingSegments'],
                  row['unresolvedRadiusSegments'],len(row.get('newFailedCurveIds',[])),flush=True)
    preview['set_positions'](carrier,banks[proof['defaultVisible']])
    r500['activate'](scene,gaze,'separated',0.,1.)
    assert array_hash(preview['evaluate'](carrier))==reopen['replay'][proof['defaultVisible']]['positionHash']
    assert digest(Path(proof['source']['path']))==proof['source']['sha256']
    write_json(ROOT/'skin-contact.json',results)


if __name__=='__main__':
    main()

