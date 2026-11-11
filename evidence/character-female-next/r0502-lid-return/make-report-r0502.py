"""Verify the saved r502 evidence and write the review and source note."""
from hashlib import file_digest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
BASELINE=ROOT.parent/'r0500-multi-pose-lid'


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
    contacts=read(ROOT/'contact-receipt.json')
    finite=read(ROOT/'finite-face-witness.json')
    assert proof['source']==preview['source']==contacts['source']==finite['source']
    for row in (proof['source'],proof['parent'],*preview['renders'].values(),*preview['baseline'].values()):
        check(row)
    assert digest(ROOT/'return-topology.npz')==proof['bankSha256']
    assert len(preview['renders'])==20 and len(preview['baseline'])==10 and len(contacts['poses'])==8
    boards={}
    for view in ('macro','turned','head','blink-body','finite-face'):
        p=ROOT/f'r0502-{view}-comparison.png'
        boards[view]=dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
    times={}
    for pose,variants in contacts['poses'].items():
        times[pose]={}
        for name,row in variants.items():
            layer=row['layer']
            times[pose][name]=dict(skin=row['selfCounts'],cornea=layer['cornea']['counts'],
                eye=layer['eye']['counts'],meniscus=layer['meniscus']['counts'],lashes=layer['lashes']['counts'],
                corneaVertexSigned=layer['cornea']['returnSignedSamples'],lashRootErrorMetres=layer['lashes']['lashRootErrorMetres'])
    open_=times['1:0']
    assert [open_[mode]['cornea'].get('return',0) for mode in ('baseline','arc','rolled')]==[0,1361,1711]
    for row in finite['results'].values():
        witness=row['witness']
        assert min(witness['vertexSignedMetres'])>0 and witness['faceCentreSignedMetres']<0 and witness['axisProjectionMetres']<0
    stats=dict(read(BASELINE/'reopen-verification.json')['stats'])
    walls=contacts['poses']['1:0']
    triangle_delta=walls['arc']['wallTriangleCount']-walls['baseline']['wallTriangleCount']
    stats['triangles']+=triangle_delta
    stats['morphs']+=sum(len(items) for items in proof['variants'].values())
    review=dict(
        round='r0502',
        decision='REJECT_FULL_RETURN_KEEP_R500',
        preferredResearch='r0500 B',
        productionAccepted=False,
        defaultVisibleVariant='arc',
        source=proof['source'],
        parent=proof['parent'],
        topology=proof['topology'],
        sceneStatsDerivedFromR500AndMeasuredWallDelta=stats,
        neutralWallTriangles={mode:row['wallTriangleCount'] for mode,row in walls.items()},
        reopenedOperation=contacts['operation'],
        lashRootsExactInEvaluatedWorld=contacts['preservedLashRoots'],
        ocularLayerHashesExact=contacts['preservedLayerHashes'],
        testedHeldPoses=times,
        poseScope=contacts['scope'],
        finiteFaceWitnesses={mode:row['witness'] for mode,row in finite['results'].items()},
        narrowerLashScopeReprobe=finite['lashOrderAudit'],
        lashAssessment=('The original r501 window reproduces zero exposed shaft pairs at frame 1 open in both BVH query directions. '
                        'The expanded r502 adjacency scope contains additional inherited shaft overlap candidates. '
                        'A broader clearance claim does not follow from the original local audit.'),
        boards=boards,
        matchedViews=10,
        freshCandidateRenders=20,
        visualAssessment=('Both candidates retain the pronounced angular crease, the late blink silhouette and mostly the same eyelid relief. '
                          'The upper margin changes subtly in the fixed macros, with insufficient improvement in complete front, oblique or profile views.'),
        categoryReview=dict(
            anatomy='Reconstructed eye return only. Rest body comparison is present. No body anatomy or motion improvement.',
            face='The angular outer closed fold remains. No credible head-scale gain.',
            eyes='Both designs intersect the cornea at open and closing poses.',
            skin='Same shaders and exposure. Two eyes have new joined interior topology, with thin-face and self-intersection issues.',
            hair='Verified original strand coordinates. Broad sheet-like groups remain visible, especially at the crown and temple.',
            clothing='Outside this round. No layering or simulation approval.',
            motion='Two native lid controls switch and restore. No swept motion certification.',
            collision='The finite face tests reject both. The old 12 boundary/nonmanifold edges remain. A total of 137 preserved IDs have no face in the rebuilt wall.',
            performance='Only local Blender resources and render time. Engine budget and tests remain open.'),
        scoreIncrease=False,
        resources=dict(
            startTaipei='2026-11-11T14:32:09+08:00',
            supportDeadlineTaipei='2026-11-11T14:42:09+08:00',
            firstPreviewDeadlineTaipei='2026-11-11T15:02:09+08:00',
            completePreviewTaipei='2026-11-11T14:46:36+08:00',
            resourceCheckpointTaipei='2026-11-11T15:17:09+08:00',
            workers=1, blenderThreads=4,
            probePeakPrivateBytes=1891196928, authorPeakPrivateBytes=2365505536,
            contactPeakPrivateBytes=2447675392, finiteWitnessPeakPrivateBytes=2214100992,
            firstPreviewPeakPrivateBytes=3359584256, resumedPreviewPeakPrivateBytes=3791761408,
            previewInterruption='System commit guard stopped the first Blender renderer before any image finished. The first retry did not start. Twenty views finished in a single resumed job after headroom returned.',
            engineCPUSeconds=None,engineGPUSeconds=None,engineMemoryBytes=None),
        nextAction=('Keep r500 B. Retire wholesale spherical inner-wall strips between widely spaced support rows. '
                    'Use the original contact-cleared posterior wall and replace the front margin locally with a conforming patch '
                    'that follows the measured mesh and limits each triangle span. Test actual cornea/skin triangles at open, .75, '
                    'and turned-closed poses before attempting a larger visible contour change. Carry the broad hair form as a major unresolved defect.'))
    (ROOT/'r0502-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
    note=(
        '# Female character r0502\n\n'
        'Rejected offline Blender research. The working comparison remains r0500 B.\n\n'
        'Open the included Blender file and select AFN138_ACTUAL_CURRENT_GAZE_RIG. R502_Inner_Return 1 selects the arc strip, 2 selects the rolled strip, and 0 shows the inherited donor motion on the new mesh. '
        'R448_Blink is the held blink. The source opens in variant A, frame 1, eyes open.\n\n'
        'Two annular walls were rebuilt as fixed triangulated strips with two intermediate rows. The original seams, all five body UV layers and live lash binding are retained. '
        'Return interior vertex IDs were reused and 137 unreferenced source IDs remain for compatibility. Both candidates were evaluated in eight held poses and rendered from ten matched camera/pose combinations.\n\n'
        'At frame 1 with eyes open, the baseline has zero return/cornea polygon pairs. A and B have 1361 and 1711. '
        'Each confirmed witness triangle has positive signed vertex distances and a negative signed face-centre distance. '
        'The face centres sit 0.741 mm and 0.488 mm inside the cornea. The actual triangle pair also has no separating axis. The figure gives the section through each witness.\n\n'
        'The external lid contour and fold remain visually close to the baseline. The full-scene render recovered after a system commit guard interruption. '
        'Continuous clearance and Aevrynd engine performance have not been verified. The inherited attribution and license notices apply.\n')
    (ROOT/'README-r0502.md').write_text(note,encoding='utf-8',newline='\n')
    print('r502 evidence verified',len(preview['renders']),len(contacts['poses']),len(boards),stats)


if __name__=='__main__':
    main()

