"""Verify the saved comparison and summarize native strand and skin results."""
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
    contact=read(ROOT/'neutral-contact.json')
    visual=read(ROOT/'visual-decision.json')
    assert proof['source']==preview['source']==reopen['source']==contact['source']
    check(proof['source'])
    check(proof['parent'])
    modes=('control','swept','returned')
    views=('front','oblique','profile','opposite','crown','rear','blink','full-body')
    assert set(preview['renders'])=={f'{m}:{v}' for m in modes for v in views}
    for view in views:
        rows=[preview['renders'][f'{m}:{view}'] for m in modes]
        for prop in ('carrier','camera','lens','exposure','blink','seed'):
            assert all(row[prop]==rows[0][prop] for row in rows[1:]),(view,prop)
        for row in rows:
            check(row)
    boards={}
    for view in ('head','profile','crown','body'):
        path=ROOT/f'r0504-{view}-comparison.png'
        boards[view]=dict(path=str(path),bytes=path.stat().st_size,sha256=digest(path))
    summary={}
    for mode,row in contact['results'].items():
        item={k:row[k] for k in ('sampledCurves','evaluatedPoints','orientedWarnings','insideCentres',
            'radiusOverlapPoints','mixedParityWarnings','segments','segmentsClearByDistanceBound',
            'centrelineCrossingSegments','radiusOverlapMidpoints','unresolvedRadiusSegments',
            'minimumSample','mostNegativeFailedCurveSample','minimumChordRadiusLowerBoundMetres',
            'elapsedSeconds','samplesPerCurveRange')}
        item['initialChordRadiusLowerBoundMetres']=item.pop('minimumChordRadiusLowerBoundMetres')
        item['confirmedFailedCurveCount']=len(row['failedCurveIds'])
        item['newFailedCurveCount']=len(row.get('addedFailedCurveIds',()))
        item['ambiguousCurveCount']=len(row['ambiguousCurveIds'])
        item['firstWitnesses']=row['crossingWitnesses'][:5]
        summary[mode]=item
    kept=visual['decision']=='RETAIN_TEMPLE_WAVES_UNACCEPTED'
    selected=summary['returned']
    review=dict(
        round='r0504',
        decision=visual['decision'],
        preferredResearch='r0504 B as a hairstyle construction comparison' if kept else 'r0500 B',
        workingModelRetained=proof['parent'],
        productionAccepted=False,
        source=proof['source'],
        parent=proof['parent'],
        defaultVisibleVariant=proof['defaultVisible'],
        originalHairCount=proof['strands'],
        posteriorStrandsExactlyRetained=proof['rearStrandsExact'],
        exactOriginalFolliclePositionHash=proof['rootHash'],
        follicleReconstructionMaximumMetres=reopen['bindingMaximumErrorMetres'],
        variantGeometry=proof['variants'],
        nativeEdit=reopen['operation'],
        stats=reopen['stats'],
        visualAssessment=visual['assessment'],
        matchedViews=len(views),
        renderCount=len(preview['renders']),
        comparisonBoards=boards,
        collisionPose=contact['pose'],
        collisionScope=contact['scope'],
        contactByVariant=summary,
        categoryReview=dict(
            anatomy='Rest body and head preserved. Whole-woman and blink views verified against one carrier.',
            face='Original r500 B facial geometry and cheek key verified on reopened candidate.',
            eyes='Same r500 B blink layout and original ocular layers.',
            skin='Same original texture and material under fixed lighting. More exposed ear area results from the new hair paths.',
            hair=visual['assessment'],
            clothing='No clothing verification in this hair rest round.',
            motion='Blink is driven on the same r500 character. Hair is a rest construction; turn, gait and dynamic hair solver still require testing.',
            collision='Only the modified strand population is included. Evaluated curve samples and their consecutive chords were checked against the actual neutral display skin. See per-variant counts and witnesses.',
            performance='Blender worker resources and capture times only. Engine CPU, GPU, memory, export and LOD remain open.'),
        rights='Original Aevrynd route generation on the inherited licensed character and follicles. The previously acquired Angelica head was inspected as a shape and flow reference. No external geometry, runtime, or new shader was imported in this round. Original attribution remains.',
        scoreIncrease=False,
        resources=visual['resources'],
        nextAction=visual['nextAction'])
    (ROOT/'r0504-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
    note=(
        '# Female character r0504\n\n'
        + ('Variant B is retained as unaccepted rest-shape research. The current working whole woman remains r0500 B.\n\n' if kept
           else 'Both hairstyle variants are rejected. The current working whole woman remains r0500 B.\n\n')
        + 'Open the included Blender file at frame 1. R504 full hair | returned is the visible candidate, '
          'R504 full hair | swept is the alternative and R497 complete hair | supported is the control. '
          'Toggle exactly one of the three groom objects in the viewport and render. '
          'The measured route objects are reference splines. The full editable groom is stored as native curves, with the generating script alongside the archive.\n\n'
        + f'Both variants reroute {selected["sampledCurves"]} existing full-length strands over measured scalp and independently authored free paths. '
          f'All {proof["strands"]} follicle positions, radii, persistent IDs and inherited materials are retained. '
          f'The {proof["rearStrandsExact"]} strands of the inherited posterior zones remain exact. '
          'The reopened variant was edited on actual curve points and restored exactly. The render comparison contains eight matched views per groom.\n\n'
        + visual['assessment']+'\n\n'
        + f'Variant B has {selected["centrelineCrossingSegments"]} crossing chord observations, '
          f'{selected["insideCentres"]} inside centres, and {selected["newFailedCurveCount"]} newly failing curve IDs in the measured neutral population. '
          'The contact report gives signed sampled gaps and unresolved chord counts. '
          'Hair self-contact, moving heads, garments, solver performance and Aevrynd runtime are outside this evidence. The inherited attribution and license notices apply.\n')
    (ROOT/'README-r0504.md').write_text(note,encoding='utf-8',newline='\n')
    print('r504 verified',len(views),len(preview['renders']),visual['decision'])
    print({m:{k:r[k] for k in ('evaluatedPoints','centrelineCrossingSegments','newFailedCurveCount','unresolvedRadiusSegments','minimumSample')} for m,r in summary.items()})


if __name__=='__main__':
    main()

