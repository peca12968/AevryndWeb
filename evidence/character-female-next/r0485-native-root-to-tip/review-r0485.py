from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import json
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def sha(path):
    with Path(path).open('rb') as f:return file_digest(f,'sha256').hexdigest()
source=read('sealed-source-receipt.json');preview=read('preview-receipt.json');state=read('source-state-receipt.json')
assert source['source']==preview['source']==state['source']
assert sha(source['source']['path'])==source['source']['sha256']
for view in ('face','rear-oblique','posterior-detail','opposite-profile','full-body'):
    base=preview['renders'][f'control:{view}']
    for tag in ('control','A','B'):
        row=preview['renders'][f'{tag}:{view}'];assert sha(row['path'])==row['sha256']
        assert all(row[k]==base[k] for k in ('camera','lens','exposure','frame','blink','samples','seed','carrierObject','carrierData'))
assert preview['sameObjectAndDataForAllModes'] and preview['storedSourceUnchanged']
record=dict(decision='REJECT_A_AND_B_FOR_CHARACTER_ADOPTION',
    previousGoalTurnClassification='The prior blocked turn revalidated the same security dialog. The user has now handled it and explicitly reactivated the existing goal; blocker audit is reset.',
    handoffResolved=True,nativeOperationPerformed=True,
    actualNativeScope='Twelve sky.drag strokes in native Blender Curve Sculpt, recorded in native-actions.json. A has four spherical strokes; B continues A with eight projected strokes from front and back. This round sculpts existing dense curves and does not create primary guide hierarchy.',
    visibleFindings=[
        'A affects 776 strands and has no convincing complete hairstyle improvement in the matched views.',
        'B affects 23,780 strands and changes the full side/rear fall and tip outline, but broad sheet-like regions, coarse folded curls, facial veils and irregular ends remain.',
        'The two studies remain below the requested human hair realism. Native tool operation is proven; no appearance improvement is adopted.'],
    methodDecision='Retire further whole-groom combing of this rejected derived dense bank. Build coherent artist-authored sparse primary guides and actual scalp ownership before child fibres; do not preserve the failed free-length construction as a constraint.',
    source=source['source'],nativeCheckpoints={t:read(f'native-{t}-receipt.json') for t in ('A','B')},
    nativeActions=read('native-actions.json'),sourceState=state,
    rootIdentityEvidence='Both native checkpoints and sealed branches retain all 24,831 root coordinates exactly, with matching curve IDs, point IDs, radii, surface attachments and physical binding hashes.',
    sourceScope='Same actual neutral woman with ocular parts, rig/control data, materials and packed textures. Hair motion is not connected. Expressions, clothing and complete runtime acceptance remain unverified.',
    bodyUnchangedEvidence='Independent final-source evaluation reproduces both r480 neutral skin vertex and triangle hashes exactly.',
    renderer='Every position bank renders through the same curve object and data block in one loaded scene, with identical optical settings. Only its point positions change in memory; saved source bytes remain unchanged.',
    renders=preview['renders'],comparisons=[dict(path=str(ROOT/n),sha256=sha(ROOT/n)) for n in ('r0485-head-comparison.png','r0485-profile-body-comparison.png')],
    collision=dict(nativeSurfaceCollisionEnabled=True,nativeDistanceM=.005,independentlyTested=False,penetrationCount=None,minimumSignedClearanceMm=None,
        reason='Authoring collision settings do not certify full finite hair/body or hair/hair clearance. Broad audits stop after visible rejection.'),
    materialAndDependencyContradiction='The initial in-process seal asserted an external reference remained but did not capture its list. A later independent fresh open of that exact saved seal showed no libraries, unlinked images or linked IDs. The failed condition was not reproduced. The subsequent portable copy also has no external dependencies. The cause is unknown; the earlier brush-causation/localization narrative, including its historical embedded editor note, is not established and is superseded by this record.',
    technicalCorrections=['The initial prepared camera type was not set, so the native camera view was too close. Frame Selected established the observed complete-hair working view before any stroke; final fixed renders copy the original camera type as well as lens and matrix.',
        'Initial size text entry briefly appended digits. It was corrected and observed as 230 px before any stroke.',
        'Control+Shift+S performed ordinary save to the working copy; separate exact A/B checkpoints were copied immediately after their observed saves. The r484 parent and complete before-native position bank were retained.',
        'Minimum-source settings inspection initially assumed EnumProperty.is_array existed; corrected to a guarded property read. No model change occurred.'],
    originalTimes=dict(startUTC='2026-11-11T00:17:12Z',supportDeadlineUTC='2026-11-11T00:27:12Z',firstPreviewDeadlineUTC='2026-11-11T00:47:12Z',resourceCheckpointUTC='2026-11-11T01:02:12Z'),
    resourcePeaksPrivateBytes=dict(prepare=2210598912,captureA=2314113024,captureB=2302746624,initialSeal=3257303040,portable=3274444800,preview=4778274816,sourceState=3335430144),
    scoreRaised=False,appearanceAdopted=False,femaleAccepted=False,maleStarted=False,engineIntegrated=False,websiteChanged=False,
    engineCPUTimeMs=None,engineGPUTimeMs=None,enginePeakMemoryBytes=None,
    rights='All inherited Angelica / DarkNik-original NikZava284 CC BY4.0, body CC0 lineage and historical notices retained. Existing Blender Comb is an authoring tool, not an Aevrynd runtime dependency or exclusively owned artwork. No new software or paid platform installed.',
    history='Final source preserves control/A/B native geometries plus inherited rollback branches. Exact native A/B checkpoint files and the superseded seal remain on F. Archive only the final source, captured data, scripts, views and honest decision; older history and r425 staging remain unresolved.',
    recordedAtUTC=datetime.now(timezone.utc).isoformat())
with (ROOT/'r0485-review.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(decision=record['decision'],source=record['source'],nativeOperationPerformed=True,rootIdentityPreserved=True,comparisons=record['comparisons']),indent=2))
