"""Collect the exact r0506 source, replay, image and contact evidence."""
from pathlib import Path
from hashlib import file_digest
from datetime import datetime
import json

ROOT=Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT/name).read_bytes())


def exact(path):
    with path.open('rb') as stream:
        return dict(path=str(path),bytes=path.stat().st_size,sha256=file_digest(stream,'sha256').hexdigest())


def main():
    source=read('construction-receipt.json')
    reopen=read('reopen-verification.json')
    preview=read('preview-receipt.json')
    contact=read('skin-contact.json')
    projection=read('projection-diagnostic.json')
    assert all(row['source']==source['source'] for row in (reopen,preview,contact,projection))
    assert exact(Path(source['source']['path']))==source['source']
    modes=('rigid','spring','rod')
    assert set(preview['renders'])=={f'{mode}:{view}' for mode in modes
        for view in (*preview['views'],*(f'f{f:02}' for f in preview['motionFrames']))}
    for view in (*preview['views'],*(f'f{f:02}' for f in preview['motionFrames'])):
        rows=[preview['renders'][f'{mode}:{view}'] for mode in modes]
        for key in ('frame','camera','lens','exposure','seed','samples','resolution'):
            assert all(row[key]==rows[0][key] for row in rows),(view,key)
    motion_cameras=[preview['renders'][f'rigid:f{frame:02}']['camera'] for frame in preview['motionFrames']]
    assert all(camera==motion_cameras[0] for camera in motion_cameras)
    for shot in preview['renders'].values():
        proof=exact(Path(shot['path']))
        assert proof['sha256']==shot['sha256']
        assert shot['sourceSha256']==source['source']['sha256']
    assert all(set(pose['results'])==set(modes) for pose in contact['frames'].values())
    assert projection['reproductionMaxErrorMetres']<5e-7
    assert reopen['modeToggleRestored'] and preview['sameCarrierAndMaterials']
    files={name:exact(ROOT/name) for name in ('r0506-head-comparison.png','r0506-body-comparison.png',
        'r0506-motion-comparison.png','r0506-hair-motion.gif','preview-receipt.json','reopen-verification.json',
        'projection-diagnostic.json','skin-contact.json')}
    contact_summary={}
    for frame,pose in contact['frames'].items():
        contact_summary[frame]={'yawDegrees':pose['yawDegrees'],'modes':{}}
        for mode,row in pose['results'].items():
            contact_summary[frame]['modes'][mode]=dict(curves=row['sampledCurves'],points=row['evaluatedPoints'],
                insideCentres=row['insideCentres'],crossingChords=row['centrelineCrossingSegments'],
                unresolvedRadiusSegments=row['unresolvedRadiusSegments'],failedCurves=len(row['failedCurveIds']),
                newFailedCurves=len(row.get('newFailedCurveIds',[])),seconds=row['elapsedSeconds'],
                closestWitness=row['minimumSample'])
    result=dict(round='r0506',decision='REJECT_R0506_MOTION_KEEP_R0505_HAIRSTYLE',source=source['source'],
        hairstyleResearchRollback=source['parent'],workingWoman=source['workingRollback'],
        scoreIncrease=False,runtimeOrWebsiteChanged=False,maleWorkStarted=False,
        resources=read('resources-r0506.json'),
        operation=dict(frames=[1,37],fps=source['motionFps'],controlModel=modes,
                       pinnedControlPointsPerCurve=reopen['pinnedControlCount'],curves=reopen['strands'],
                       matchedRenderCount=len(preview['renders']),motionSampleFrames=preview['motionFrames'],
                       independentReopen=True),
        visualFindings=[
            'The spring model barely changes the visible hair silhouette under the matched 32-degree test.',
            'The projected model yields an isolated displacement outlier rather than a legible improvement in whole-groom response.',
            'Front, oblique, profile, crown, rear and full-body shots preserve the prior hairstyle and expression. The crown still reads as broad smooth ribbons, the rear as a continuous sheet, and the temples as thin curtains.',
        ],
        keyframeMotionMm={key:row['tipMm'] for key,row in reopen['verified'].items()
                          if row['frame'] in (4,9,10,12,17,37)},
        projectionDiagnostic=projection['maximumStep'],
        skinContact=contact_summary,artifacts=files,
        limits=['Tested discrete posed skin against evaluated chords and interpolated radii of a selected strand population.',
                'Garment contact, inter-strand contact, continuous-time clearance, and engine playback were not verified.'],
        nextAction='Keep r0505 B as hairstyle research and r0500 B as the complete working woman. Change the broad crown and rear lock construction before another motion refinement. Retain the reproducible guide fixture and add a continuous, conservative skin-contact premise before approving live motion.',
        recordedAt=datetime.now().astimezone().isoformat())
    (ROOT/'r0506-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision=result['decision'],renders=len(preview['renders']),
        collision=contact_summary,projection=result['projectionDiagnostic']),indent=2))


if __name__=='__main__':
    main()

