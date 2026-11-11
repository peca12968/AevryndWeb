"""Validate captures, summarize the visible and technical gates, and write the review."""
from pathlib import Path
from datetime import datetime
from hashlib import file_digest
import json

ROOT=Path(__file__).resolve().parent
MODES=('control','open_sweep','layered_tuck')


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
    silhouette=read('front-silhouette.json')
    for mode in MODES:
        assert silhouette['modes'][mode]['sha256']==shots[f'{mode}:front']['sha256']
    assert set(audit['poses'])=={str(f) for f,_,_ in visual['contactPlan']}
    by_pose={}
    for frame,blink,modes in visual['contactPlan']:
        pose=audit['poses'][str(frame)]
        assert pose['blink']==blink and set(pose['modes'])==set(modes)
        details={}
        for mode,result in pose['modes'].items():
            assert result['positionHash']==reopen['replay'][mode]['positionHash']
            assert result['sampledCurves']==audit['changedStrandCount']==7502
            details[mode]=dict(curves=result['sampledCurves'],samples=result['evaluatedPoints'],
                inside=result['insideCentres'],finiteRadiusOverlapPoints=result['radiusOverlapPoints'],
                crossingChords=result['centrelineCrossingSegments'],unresolvedChords=result['unresolvedRadiusSegments'],
                failedCurves=len(result['failedCurveIds']),ambiguousCurves=len(result['ambiguousCurveIds']),newFailedCurves=len(result.get('newFailedCurveIds',[])),
                minimumSample=result['minimumSample'],minimumChordBoundMetres=result['minimumChordRadiusLowerBoundMetres'],
                elapsedSeconds=result['elapsedSeconds'])
        by_pose[str(frame)]=dict(frame=frame,blink=blink,yawDegrees=pose['yawDegrees'],root=pose['root'],modes=details)
    preferred=visual['preferredResearch']
    decision=visual['decision']
    next_action=visual['nextAction']
    selection=visual['selectedMode']
    if selection is not None:
        selected=[p['modes'][selection] for p in by_pose.values() if selection in p['modes']]
        assert len(selected)==3
        open_check=any(row['failedCurves'] or row['unresolvedChords'] or row['ambiguousCurves']
                       for row in selected)
        if open_check:
            visual['categoryReview']['collision']+=' The chosen visible candidate has measured contact warnings.'
            decision='REJECT_R0509_KEEP_R0507'
            preferred='r0507 B'
            next_action=('Keep r0507 B as the hair source and r0500 B as the complete working woman. '
                         'Trace the frontal collision IDs at the reported positions before reusing the routes. '
                         'A distinct layered envelope and narrower natural front release remain the next construction problem.')
        else:
            visual['categoryReview']['collision']+=' No intersections were detected for the chosen modified strands and poses.'
    failure=read('failure-location.json')
    turns=read('temple-turns.json')
    assert failure['source']==turns['source']==source
    assert all(not row['failedCurveCount'] and not row['unresolvedChords'] for row in failure['poses']['1'].values())
    assert all(len(row['priorR508FailedCurveIdsWithoutConfirmedFailure'])==10 for row in failure['poses']['1'].values())
    visual['categoryReview']['collision']+=' Neither candidate shows detected skin crossings in the neutral changed population, including the ten earlier failure IDs.'
    visual['categoryReview']['hair']+=' The 90th-percentile peak turn in the measured temple band rises from 12.29 degrees to 30.05 in A and 27.73 in B.'
    board_names=('r0509-frontal-comparison.png','r0509-profile-comparison.png','r0509-body-comparison.png')
    result=dict(round='r0509',source=source,parent=build['parent'],workingWoman=build['workingRollback'],
        decision=decision,preferredResearch=preferred,productionAccepted=False,
        scoreIncrease=False,runtimeOrWebsiteChanged=False,maleWorkStarted=False,
        visualAssessment=visual['visualAssessment'],categoryReview=visual['categoryReview'],
        frontSilhouette={mode:{k:v for k,v in row.items() if k!='contourY'} for mode,row in silhouette['modes'].items()},
        views=views,renderCount=len(shots),boards={name:info(ROOT/name) for name in board_names},
        geometry=dict(variants=build['variants'],pinnedControls=build['pinnedControls'],stats=reopen['stats'],
            editAndRestore=reopen['liveNativeEdit'],headOperation=reopen['headTurn']),
        scope=audit['scope'],skinContact=by_pose,contactFailure=failure,templeTurns=turns,resources=read('resources-r0509.json'),rights=build['rights'],
        nextAction=next_action,recordedAt=datetime.now().astimezone().isoformat())
    (ROOT/'r0509-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['decision'],result['preferredResearch'],len(shots),'captures')
    for frame,pose in by_pose.items():
        for mode,row in pose['modes'].items():
            print(frame,mode,row['curves'],row['inside'],row['crossingChords'],row['unresolvedChords'],
                  row['newFailedCurves'],row['minimumSample']['signedOrBoundMetres'])


if __name__=='__main__':
    main()

