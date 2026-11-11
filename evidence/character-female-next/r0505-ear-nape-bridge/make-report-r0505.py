"""Check the r505 artifact set and summarize visual, attachment and collision evidence."""
from hashlib import file_digest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with Path(path).open('rb') as handle:
        return file_digest(handle,'sha256').hexdigest()


def check(row):
    assert digest(row['path'])==row['sha256'],row['path']
    if 'bytes' in row:
        assert Path(row['path']).stat().st_size==row['bytes']


def main():
    proof=read(ROOT/'construction-receipt.json')
    preview=read(ROOT/'preview-receipt.json')
    reopen=read(ROOT/'reopen-verification.json')
    contact=read(ROOT/'skin-contact.json')
    visual=read(ROOT/'visual-decision.json')
    assert proof['source']==preview['source']==reopen['source']==contact['source']
    check(proof['source'])
    check(proof['parent'])
    check(proof['fullWorkingRollback'])
    modes=('control','graded','layered')
    views=('rear','opposite','profile','front','oblique','crown','turn','full-body','blink')
    assert set(preview['renders'])=={f'{m}:{v}' for m in modes for v in views}
    for view in views:
        rows=[preview['renders'][f'{m}:{view}'] for m in modes]
        for prop in ('carrier','camera','lens','exposure','blink','seed','frame','carrierMatrix'):
            assert all(row[prop]==rows[0][prop] for row in rows[1:]),(view,prop)
        for row in rows:
            check(row)
    boards={}
    for view in ('join','head','profile','body'):
        path=ROOT/f'r0505-{view}-comparison.png'
        boards[view]=dict(path=str(path),bytes=path.stat().st_size,sha256=digest(path))
    cohort={(a['side'],a['lowerYMillimetres']):a for a in reopen['fixedTipCohorts']}
    step={m:{str(s):abs(cohort[s,24.]['medianTipHeightMm'][m]-cohort[s,34.]['medianTipHeightMm'][m])
             for s in (-1,1)} for m in modes}
    summary={}
    for pose,native in contact['results'].items():
        trials={}
        for mode,row in native['results'].items():
            item={k:row[k] for k in ('sampledCurves','evaluatedPoints','orientedWarnings','insideCentres',
                'radiusOverlapPoints','mixedParityWarnings','segments','segmentsClearByDistanceBound',
                'centrelineCrossingSegments','radiusOverlapMidpoints','unresolvedRadiusSegments',
                'minimumSample','mostNegativeFailedCurveSample','elapsedSeconds','samplesPerCurveRange','sampleSpaces')}
            item['initialChordRadiusLowerBoundMetres']=row['minimumChordRadiusLowerBoundMetres']
            item['confirmedFailedCurveCount']=len(row['failedCurveIds'])
            item['newFailedCurveCount']=len(row.get('addedFailedCurveIds',()))
            item['ambiguousCurveCount']=len(row['ambiguousCurveIds'])
            item['witnesses']=row['crossingWitnesses'][:5]
            trials[mode]=item
        assert set(trials)==set(modes)
        summary[pose]=dict(headingDegrees=native['headingDegrees'],
            rootDriftBeyondNeutral=native['rootDriftBeyondNeutral'],
            changedPopulationRootDriftBeyondNeutral=native['changedPopulationRootDriftBeyondNeutral'],
            results=trials)
    kept=visual['decision']=='RETAIN_EAR_NAPE_BRIDGE_UNACCEPTED'
    selected=visual['preferredMode']
    review=dict(
        round='r0505',
        decision=visual['decision'],
        preferredResearch=visual['preferredResearch'],
        preferredMode=selected,
        productionAccepted=False,
        source=proof['source'],
        parent=proof['parent'],
        fullWorkingRollback=proof['fullWorkingRollback'],
        defaultVisibleVariant=proof['defaultVisible'],
        restHairControl=proof['controlObject'],
        curveCount=proof['strands'],
        protectedPosteriorCurves=proof['originalPosteriorCount'],
        fixedOriginalFolliclePositionHash=proof['rootHash'],
        variantGeometry=proof['variants'],
        fixedBaselineTipCohorts=reopen['fixedTipCohorts'],
        fixedCohortTipHeightStepMm=step,
        nativeEdit=reopen['operation'],
        nativeHeadOperation=reopen['headOperation'],
        stats=reopen['stats'],
        visualAssessment=visual['assessment'],
        matchedViews=len(views),
        renderCount=len(preview['renders']),
        comparisonBoards=boards,
        collisionScope=contact['scope'],
        neutralDisplayFollicleReferenceError=contact['rootNeutralError'],
        poseContact=summary,
        categoryReview=dict(
            anatomy='Rest body and pose source preserved. No whole-body anatomical change.',
            face='Original r500 B eyelid and orbital cheek keys unchanged. Native blink used in the head-turn capture.',
            eyes='Original optics and eye motion preserved. No new ocular clearance evidence.',
            skin='Same body surface and original lighting and shaders; skin serves as the actual collider.',
            hair=visual['assessment'],
            clothing='No garment contact assessment in this round.',
            motion='Native rigid head attachment verified in a held turn. The control has identical attachment for comparison. Secondary hair physics are pending.',
            collision='Changed strand population tested at the evaluated held poses. See confirmed curve counts and signed gaps. No continuous or all-layer certification.',
            performance='Only Blender source size, scene budgets, timings and peak memory are measured. Engine runtime, CPU/GPU and export remain open.'),
        rights='New curve geometry and native bone attachment on the inherited offline licensed woman. Original assets, materials, attribution and licenses apply.',
        scoreIncrease=False,
        resources=visual['resources'],
        nextAction=visual['nextAction'])
    (ROOT/'r0505-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
    note=(
        '# Female character r0505\n\n'
        + (f'{visual["preferredResearch"]} is retained as unaccepted hairstyle research. The full working woman remains r0500 B.\n\n' if kept
           else 'Both candidates are rejected. Retain r0504 B as the side-hair shape reference and r0500 B as the whole-woman rollback.\n\n')
        + 'Open the included Blender file at frame 1. R505 full hair | layered is visible. '
          'R505 full hair | graded is the alternative and R504 full hair | returned is the rest shape control. '
          'The two r505 objects are parented to AFN69_BODY_CONTROLS, Head bone. The original authored roots, strand IDs, radii, materials and protected posterior region are retained. '
          'The comparison applies the same calibrated attachment to all three grooms. The turn is a rigid head-follow operation without secondary hair physics.\n\n'
        + visual['assessment']+'\n\n'
        + 'The fixed tip cohorts are selected once from r504 at ear height. Their original IDs are tracked through both candidates. '
          'The collision evidence records every evaluated point and consecutive chord of the changed strand population for each held pose. '
          'It does not cover all inherited strands, continuous-time motion, inter-strand contact or garments. Inherited attribution and rights apply.\n')
    (ROOT/'README-r0505.md').write_text(note,encoding='utf-8',newline='\n')
    print('r505 verified',len(views),len(preview['renders']),visual['decision'],step)
    print({p:{k:(q['newFailedCurveCount'],q['centrelineCrossingSegments'],q['minimumSample']['signedOrBoundMetres']) for k,q in r['results'].items()} for p,r in summary.items()})


if __name__=='__main__':
    main()

