from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import json
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def sha(path):
    with Path(path).open('rb') as f:return file_digest(f,'sha256').hexdigest()
source=read('volume-source-receipt.json');preview=read('final-preview-receipt.json');verify=read('final-reopen-verification.json')
assert source['source']==preview['source']==verify['source']
assert sha(source['source']['path'])==source['source']['sha256']
for view in ('face','rear-oblique','posterior-detail','opposite-profile','full-body'):
    base=preview['renders'][f'control:{view}']
    for tag in ('control','A','B'):
        entry=preview['renders'][f'{tag}:{view}'];assert sha(entry['path'])==entry['sha256']
        assert all(entry[k]==base[k] for k in ('camera','lens','exposure','frame','blink','samples','seed','skinHashes'))
assert not verify['externalDependencies']
record=dict(previousGoalTurn='PROGRESS: r483 authored, rejected, reproducibly reconstructed and published; no accepted appearance gain.',
    decision='REJECT_A_AND_B_FOR_CHARACTER_ADOPTION',
    visibleFindings=[
        'A changes the short cap into longer curls, but complete face, profile and rear views show sheet-like fibre groups and coarse ribbon-like ends.',
        'B gives the groups depth but retains thick curls, irregular crown flow and a broad veil over the side of the face.',
        'The original artist reference has coherent layered paths. Sampling those source strips and assigning current follicles by nearest prefix does not preserve that appearance.',
        'Neither candidate meets the requested human hair realism or proves collision-free use.'],
    retiredMethods=['Nearest source-strip-prefix mapping with transported planar offsets','The same source assignment with elliptical volume cross sections'],
    nextAction='Stop numerical retuning of these conversions. Establish artist-authored primary guide families with coherent scalp ownership and inspect full-root-to-tip shape on this complete woman before generating child fibres. Native brush operation is still pending the existing user security handoff.',
    durableConstructionProgress=['Recovered actual same-woman neutral skin and ocular components without loading unrelated historical grooms.',
        'Original reference mesh matches archived r126 world coordinates exactly and remains hidden from candidate renders.',
        'Final source contains control, A and B with all original roots, IDs, radii and physical bindings retained.',
        'Final source has packed images and no linked libraries or external image dependencies after reopening.'],
    source=source['source'],parent=source['parent'],verification=verify,
    completeWomanReview=dict(views=['face','rear-oblique','posterior-detail','opposite-profile','full-body'],
        actualNeutralSkinExactlyMatchesR480=True,actualSkinVsBindingFixtureMaxVertexErrorMm=0.,hairMotionNotReconnected=True),
    renderConditions='All final variants use the same packed source, camera, frame 1, blink 0, lighting, exposure, samples, seed, material and radius fields. Rear camera references originally used blink 1; this round explicitly captures neutral blink 0 for every paired view.',
    localizationComparison=read('localization-render-comparison.json'),
    renders=preview['renders'],comparisons=[dict(path=str(ROOT/name),sha256=sha(ROOT/name)) for name in ('r0484-head-comparison.png','r0484-profile-body-comparison.png')],
    score=dict(raised=False,formalOverall=None,face=None,eyes=None,skin=None,hair=None,anatomy=None,clothes=None,dynamics=None,collision=None,performance=None,
        reason='No new numerical scores awarded. Hair realism rejected; other global acceptance gates remain incomplete.'),
    collision=dict(tested=False,penetrationCount=None,minimumSignedClearanceMm=None,reason='Visual rejection ends refinement before broad contact audits. Inherited results do not cover the reconstructed strands.'),
    engine=dict(integrated=False,cpuMs=None,gpuMs=None,peakMemoryBytes=None),websiteChanged=False,femaleAccepted=False,maleStarted=False,
    nativeBrushOperationPerformed=False,originalWorkspaceR425StageStillUnverified=True,
    originalTimes=dict(startUTC='2026-11-10T23:21:20Z',supportDeadlineUTC='2026-11-10T23:31:20Z',firstPreviewDeadlineUTC='2026-11-10T23:51:20Z',resourceCheckpointUTC='2026-11-11T00:06:20Z'),
    resources=dict(threads=4,assemblyPeakPrivateBytes=1834967040,AauthorPeakPrivateBytes=1475330048,ApreviewPeakPrivateBytes=3057852416,
        BauthorPeakPrivateBytes=2252939264,finalPreviewPeakPrivateBytes=3744792576,finalReopenPeakPrivateBytes=2023510016),
    knownFailures=['Initial generic 6200 MiB headroom guard rejected the lightweight inventory before any Blender process launched; a scope-specific 3500 MiB inventory threshold was then used.',
        'Inspection accessed a module as a dictionary once; corrected before model authoring.',
        'Initial source guide derivation connected vertex IDs across UV seams; superseded by UV-corner-connected islands before any candidate was authored.',
        'Initial preview asserted the rear camera blink reference was zero; it was one. Failed before rendering. Final captures explicitly use current neutral blink zero.',
        'Initial volumetric authoring did not handle singleton root groups; corrected to a zero-radius singleton group before a B source was saved.'],
    rights='Existing Angelica head/hair by DarkNik / original NikZava284 under CC BY 4.0, inherited CC0 body chain and historical notices retained. Original asset rights are not exclusive Aevrynd ownership. No new paid platform, runtime or software installation.',
    history='Publish only the final packed source containing all three branch geometries, evidence, data, scripts and source notices. Intermediate linked .blend files remain on F. This round does not resolve older unpublished history.',
    recordedUTC=datetime.now(timezone.utc).isoformat())
with (ROOT/'r0484-review.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(decision=record['decision'],source=record['source'],externalDependencies=verify['externalDependencies'],comparisons=record['comparisons']),indent=2))
