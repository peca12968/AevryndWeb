from pathlib import Path
from hashlib import file_digest
import json
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
source=read(R/'construction-receipt.json');verification=read(R/'reopen-verification.json');preview=read(R/'preview-receipt.json')
assert len(preview['renders'])==10
assert sha(Path(source['source']['path']))==source['source']['sha256']
for row in preview['renders'].values():assert sha(Path(row['path']))==row['sha256']
record=dict(round='r0486',decision='REJECT_FOR_CHARACTER_ADOPTION',goalStatus='active',source=source['source'],parent=source['parent'],
    hypothesis='Replace failed inherited free lengths with sparse actual-scalp primary guides and explicit region ownership, improving complete root-to-tip flow.',
    previousTurnClassification='Progress: r485 established actual native editing and produced rejected A/B evidence, changing next action to a new guide foundation.',
    construction=dict(primaryGuides=126,regions=6,children=24831,pointsPerCurve=80,method='Deterministic actual-root spatial representatives per hemisphere and frontal/crown/occipital region. Scalp-BVH tangent integration then gravity fall; four nearby guide displacement fields interpolate each original follicle. Inherited free-length coordinates are not inputs.',
        nativeGuideObject=source['primaryGuideObject'],childObject=source['candidateObject'],ownership='primary-guide-construction.npz preserves source curve IDs, region, four primary guide IDs and weights; primary native Curve IDs also stored in .blend',
        limitation='Primary guides have source-root identity but have not been separately operated in native Sculpt or given a complete deforming surface attachment. Child root binding remains inherited and exact. Guide construction alone is not acceptance.'),
    visibleEvidence=dict(improvements=['The large lateral curls and crumpled rear ribbons are removed.','Front and profile have a coherent straight root-to-tip flow.'],
        rejectionReasons=['Ear visibly protrudes through the continuous hair layer in profile and rear oblique; contact is not acceptable.','Posterior close-up exposes a long central opening and a rigid left/right division.','Large smooth curtain surfaces, blunt lengths and insufficient middle-scale lock variation remain.','Frontal side hair lies too close to the face.'],
        examinedViews=['face','rear-oblique','opposite-profile','posterior-detail','full-body'],
        completeBody='Same neutral woman and pose preserved; body anatomy, rig, eyes and skin were not improved or newly accepted.'),
    technical=verification,preview=preview,
    quality=dict(scoreChanged=False,numericalScore=None,scorePolicy='No new numeric scores or quality adoption. Retain inherited scores and stagnation counters.',
        anatomy='Unchanged; full pose range unverified.',face='Unchanged.',eyes='Unchanged.',skin='Unchanged; fixed exposure.',hair='Reject: contact, central split and smooth curtain shape.',clothing='Not tested.',collision='Visible contact failure; finite penetration count and signed minimum remain null.',dynamics='Not tested.',performance='No Aevrynd engine timings.'),
    gates=dict(reopen='PASS scoped file/fields/finite and interpolation reproduction',visual='FAIL',finiteCollision='NOT_RUN_AFTER_VISIBLE_REJECTION',animation='NOT_TESTED',export='NOT_TESTED',engine='NOT_TESTED',femaleAcceptance=False),
    resources=dict(startTaipei='2026-11-11T08:58:37+08:00',supportDeadlineTaipei='2026-11-11T09:08:37+08:00',firstPreviewDeadlineTaipei='2026-11-11T09:28:37+08:00',resourceCheckpointTaipei='2026-11-11T09:43:37+08:00',completePreviewTaipei='2026-11-11T09:05:59+08:00',
        workers=1,blenderThreads=4,inspectionPeakPrivateBytes=818364416,authorPeakPrivateBytes=3400138752,previewPeakPrivateBytes=5159960576,
        initialAttempt='Inspection was refused before process launch by 6200 MiB free-commit guard. A bounded 3000 MiB inspection with 4500 MiB headroom then passed. Author used 3400 MiB limit; preview used 5000 MiB limit and 6200 MiB prelaunch guard. No hidden restart or overlapping heavy job.',
        engineCPUSeconds=None,engineGPUSeconds=None),
    provenance=dict(newExternalArt=False,inheritedLicenses='Exact r485 license folder retained. Angelica attribution DarkNik/original NikZava284, CC BY 4.0, inherited CC0 body lineage and older source qualifications. No new exclusive ownership or full rights-completion claim.',
        dependencies='Final fresh reopen reports no linked libraries or unpacked file images. The r485 historical embedded localization narrative remains superseded by r485 review; no new dependency-cause claim.'),
    retiredMethods='r483 shortening/lateral displacement, r484 source-strip/elliptical volume constructions and repeated dense-groom combing remain retired. No stagnation counter reset.',
    nextAction='Rebuild the relevant primary paths: an occipital region continuous across the midline, and temple/ear routes around the actual ear silhouette, with authored middle-scale sections. Do not preserve this failed curtain or globally inflate/shrink it to pass contact. First inspect primary paths on the complete woman before regenerating children.',
    websiteChanged=False,runtimeChanged=False,maleStarted=False)
(R/'r0486-review.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(dict(decision=record['decision'],source=source['source'],completeViews=len(preview['renders'])),indent=2))
