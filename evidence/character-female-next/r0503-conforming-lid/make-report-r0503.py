"""Verify all r503 artifacts and summarize the native and visual decisions."""
from collections import Counter
from hashlib import file_digest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
R500=ROOT.parent/'r0500-multi-pose-lid'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with Path(path).open('rb') as handle:
        return file_digest(handle,'sha256').hexdigest()


def verify(row):
    assert digest(row['path'])==row['sha256'],row['path']
    if 'bytes' in row:
        assert Path(row['path']).stat().st_size==row['bytes']


def main():
    proof=read(ROOT/'construction-receipt.json')
    preview=read(ROOT/'preview-receipt.json')
    contact=read(ROOT/'reopen-contact.json')
    screen=read(ROOT/'screen-receipt.json')
    visual=read(ROOT/'visual-decision.json')
    assert proof['source']==preview['source']==contact['source']
    assert screen['sourceSha256']==proof['source']['sha256']
    for row in (proof['source'],proof['parent'],*preview['renders'].values(),*preview['baseline'].values()):
        verify(row)
    assert len(preview['renders'])==20 and len(preview['baseline'])==10 and len(contact['poses'])==12
    boards={}
    for view in ('macro','turned','head','blink-body'):
        p=ROOT/f'r0503-{view}-comparison.png'
        boards[view]=dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
    side=ROOT/'r0503-local-contact-comparison.png'
    if side.exists():
        boards['localized-contact']=dict(path=str(side),bytes=side.stat().st_size,sha256=digest(side))
    times={}
    observations={}
    for mode in ('control','fair','rest'):
        old,new=Counter(),Counter()
        signed=[]
        for pose,variants in contact['poses'].items():
            row=variants[mode]
            old.update(w['pair'][0] for w in row['newAgainstR500'])
            new.update(w['pair'][0] for w in row['newRawAgainstSplitControl'])
            signed.append((row['signedSamples']['cornea']['metres'],pose,row['signedSamples']['cornea']))
            times.setdefault(pose,{})[mode]=dict(baseline=row['baseline'],current=row['current'],
                newR500=len(row['newAgainstR500']),newRaw=len(row['newRawAgainstSplitControl']),
                maxExternalDisplacementMetres=row['externalChangeMaxMetres'])
        _,pose,closest=min(signed)
        observations[mode]=dict(newOriginalPolygonPairs=old,newNativePolygonPairs=new,
            minCorneaSignedSample=dict(pose=pose,**closest))
    assert not observations['rest']['newOriginalPolygonPairs'] and not observations['rest']['newNativePolygonPairs']
    assert observations['fair']['newNativePolygonPairs']['skin']==44
    fixed=preview['fixedFrontalNormalSteps']
    fixed['baseline']=read(R500/'facial-contact.json')['fixedFrontalNormalSteps']['separated']
    normal_pairs={mode:[r['angleDegrees'] for r in steps if r['pixel'][0] in (204,436) and r['pixel'][1]==342]
                  for mode,steps in fixed.items()}
    turn,gap=max(contact['splitControlInterpolationMetres'].items(),key=lambda item:item[1]['metres'])
    preferred=visual['decision']=='RETAIN_CONFORMING_LID_UNACCEPTED'
    review=dict(
        round='r0503',
        decision=visual['decision'],
        preferredResearch='r0503 B' if preferred else 'r0500 B',
        productionAccepted=False,
        source=proof['source'],
        parent=proof['parent'],
        defaultVisibleVariant='rest',
        topology=proof['topology'],
        sceneStats=contact['stats'],
        retainedPosteriorFacesExact=contact['protectedReturnFaces'],
        retainedPosteriorVerticesExact=contact['protectedReturnVertices'],
        splitFrontWallFaces=len(proof['splitFrontReturnFaces']),
        originalKeysVerified=contact['originalKeyHashesVerified'],
        protectedLashAnchors=contact['preservedLashAnchors'],
        splitSupportMaxDeviation=dict(pose=turn,**gap),
        reopenedOperation=contact['operation'],
        scope=contact['scope'],
        nativeObservations=observations,
        testedHeldPoses=times,
        originalTriangleIdentities='Correspond through per-face ownership. New identities native to the split control are tested separately.',
        fixedFrontalNormalStepsDegrees=normal_pairs,
        originalTrainingCounts={mode:[r['newPairObservations'] for r in rows] for mode,rows in screen['variants'].items()},
        boards=boards,
        matchedViews=10,
        freshRenders=20,
        visualAssessment=visual['assessment'],
        categoryReview=dict(
            anatomy='Body rest silhouette compared in complete views. No added anatomical evidence.',
            face=visual['assessment'],
            eyes='B retains the r500 eyelid/cornea overlap result in the tested field. A introduces native skin pair observations.',
            skin='Same shader, textures, exposure and preserved original UV samples. New support corners interpolate their parent UVs.',
            hair='Original authored groom geometry verified. The crown and temple still read as large glossy sheets.',
            clothing='Outside the current reconstruction and review.',
            motion='Original blink range and head poses. Twelve discrete evaluations, including five not in the fitting screen.',
            collision='B adds no scoped overlap identities. The baseline contacts persist, so continuous and whole-character clearance are open.',
            performance='Local Blender resources measured. Aevrynd import and benchmarks pending.'),
        scoreIncrease=False,
        resources=visual['resources'],
        nextAction=visual['nextAction'])
    (ROOT/'r0503-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
    note=(
        '# Female character r0503\n\n'
        + ('Variant B is retained as an unaccepted offline research source.\n\n' if preferred
           else 'Both variants are rejected. The working comparison remains r0500 B.\n\n')
        + 'Open the Blender file and select AFN138_ACTUAL_CURRENT_GAZE_RIG. R503_Front_Lid 0 selects the conforming topology control, 1 selects A and 2 selects B. '
          'R448_Blink operates the original blink range. The source opens at frame 1 with B active and eyes open.\n\n'
          'The conforming patch subdivides selected original triangles in the visible upper margin and front return. '
          'The posterior wall, lash anchors and ocular layers were verified on reopen. A reduces spatial curvature. B transports the local rest curvature. '
          'Each variant is driven by three native shape keys and checked using the real deformed triangles.\n\n'
          'B adds zero original-owner or split-native triangle-pair observations in 12 held poses. '
          'A adds 44 split-native skin pair observations. These are discrete finite overlap comparisons and leave inherited contacts in scope. '
          'The largest split support deviation from a deformed parent centroid is 0.0233 mm at frame 37, full blink. '
          'Continuous-time clearance and engine performance were not measured. Inherited rights and attribution apply.\n')
    (ROOT/'README-r0503.md').write_text(note,encoding='utf-8',newline='\n')
    print('r503 verified',len(preview['renders']),len(contact['poses']),normal_pairs,review['decision'])


if __name__=='__main__':
    main()

