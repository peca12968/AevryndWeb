"""Validate captures, summarize the visible and technical gates, and write the review."""
from pathlib import Path
from datetime import datetime
from hashlib import file_digest
import json

ROOT=Path(__file__).resolve().parent
MODES=('control','separated','overlapping')


def read(name):
    return json.loads((ROOT/name).read_bytes())


def info(path):
    with path.open('rb') as handle:
        return dict(path=str(path),sha256=file_digest(handle,'sha256').hexdigest(),bytes=path.stat().st_size)


def main():
    build=read('construction-receipt.json')
    source=build['source']
    reopen=read('reopen-verification.json')
    preview=read('preview-receipt.json')
    visual=read('visual-decision.json')
    audit=read('skin-contact.json')
    assert all(x['source']==source for x in (reopen,preview,visual,audit))
    assert info(Path(source['path']))==source
    shots=preview['renders']
    views=preview['views']
    assert set(shots)=={f'{mode}:{view}' for mode in MODES for view in views}
    for view in views:
        rows=[shots[f'{mode}:{view}'] for mode in MODES]
        for key in ('frame','blink','hairMatrix','camera','lens','exposure','samples','seed','resolution','carrier'):
            assert all(row[key]==rows[0][key] for row in rows),(view,key)
        for mode,row in zip(MODES,rows):
            assert row['sourceSha256']==source['sha256']
            assert row['positionHash']==reopen['replay'][mode]['positionHash']
            assert row['sha256']==info(Path(row['path']))['sha256']
    assert set(audit['poses'])=={str(f) for f,_,_ in visual['contactPlan']}
    by_pose={}
    for frame,blink,modes in visual['contactPlan']:
        pose=audit['poses'][str(frame)]
        assert pose['blink']==blink and set(pose['modes'])==set(modes)
        details={}
        for mode,result in pose['modes'].items():
            assert result['positionHash']==reopen['replay'][mode]['positionHash']
            assert result['sampledCurves']==audit['changedStrandCount']==10416
            details[mode]=dict(curves=result['sampledCurves'],samples=result['evaluatedPoints'],
                inside=result['insideCentres'],finiteRadiusOverlapPoints=result['radiusOverlapPoints'],
                crossingChords=result['centrelineCrossingSegments'],unresolvedChords=result['unresolvedRadiusSegments'],
                failedCurves=len(result['failedCurveIds']),ambiguousCurves=len(result['ambiguousCurveIds']),newFailedCurves=len(result.get('newFailedCurveIds',[])),
                minimumSample=result['minimumSample'],minimumChordBoundMetres=result['minimumChordRadiusLowerBoundMetres'],
                elapsedSeconds=result['elapsedSeconds'])
        by_pose[str(frame)]=dict(frame=frame,blink=blink,yawDegrees=pose['yawDegrees'],root=pose['root'],modes=details)
    b_rows=[p['modes']['overlapping'] for p in by_pose.values() if 'overlapping' in p['modes']]
    preferred=visual['preferredResearch']
    decision=visual['decision']
    next_action=visual['nextAction']
    if preferred=='r0507 B':
        b_has_open_checks=any(row['failedCurves'] or row['unresolvedChords'] or row['ambiguousCurves']
                              for row in b_rows)
        if b_has_open_checks:
            visual['categoryReview']['collision']+=' B has measured skin contact warnings and remains unaccepted.'
            decision='REJECT_R0507_KEEP_R0505'
            preferred='r0505 B'
            next_action=('Continue from the r0505 B hairstyle and r0500 B whole woman. Preserve the r0507 diagonal tier '
                         'construction as evidence. Trace the failing curve IDs to the posed surface before bringing '
                         'that design forward. Rebuild the crown-to-temple connection as the next visible form task.')
        else:
            visual['categoryReview']['collision']+=' B has no detected skin intersections in the tested strand population and frames.'
    board_names=('r0507-rear-comparison.png','r0507-head-comparison.png','r0507-body-comparison.png')
    result=dict(round='r0507',source=source,parent=build['parent'],workingWoman=build['workingRollback'],
        decision=decision,preferredResearch=preferred,productionAccepted=False,
        scoreIncrease=False,runtimeOrWebsiteChanged=False,maleWorkStarted=False,
        visualAssessment=visual['visualAssessment'],categoryReview=visual['categoryReview'],
        views=views,renderCount=len(shots),boards={name:info(ROOT/name) for name in board_names},
        geometry=dict(variants=build['variants'],pinnedControls=build['pinnedControls'],stats=reopen['stats'],
            editAndRestore=reopen['liveNativeEdit'],headOperation=reopen['headTurn']),
        scope=audit['scope'],skinContact=by_pose,resources=read('resources-r0507.json'),rights=build['rights'],
        nextAction=next_action,recordedAt=datetime.now().astimezone().isoformat())
    (ROOT/'r0507-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['decision'],result['preferredResearch'],len(shots),'captures')
    for frame,pose in by_pose.items():
        for mode,row in pose['modes'].items():
            print(frame,mode,row['curves'],row['inside'],row['crossingChords'],row['unresolvedChords'],
                  row['newFailedCurves'],row['minimumSample']['signedOrBoundMetres'])


if __name__=='__main__':
    main()

