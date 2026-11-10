from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import json

ROOT=Path(__file__).resolve().parent
def sha(path):
    with Path(path).open('rb') as f:return file_digest(f,'sha256').hexdigest()
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))

draft=read('draft-receipt.json');verified=read('reopen-verification.json')
assert sha(draft['source']['path'])==draft['source']['sha256']==verified['source']['sha256']
for view in ('posterior-detail','rear-oblique','face','opposite-profile','full-body'):
    base=draft['renders'][f'base:{view}']
    for tag in ('base','A','B'):
        entry=draft['renders'][f'{tag}:{view}']
        assert sha(entry['file'])==entry['sha256']
        assert all(entry[k]==base[k] for k in ('camera','lens','exposure'))
record=dict(decision='REJECT_A_AND_B_FOR_CHARACTER_ADOPTION',
    reviewedViews=['posterior-detail','rear-oblique','face','opposite-profile','full-body'],
    appearanceFindings=[
        'Posterior and rear oblique retain a continuous rounded canopy and a thick dark lower fringe.',
        'Graduating the ends changes local tip height but does not establish a believable root-to-tip hairstyle.',
        'Adding lateral crown flow produces insufficient visible change in the matched complete head views.',
        'The front, opposite profile and neutral body views do not establish an accepted character appearance gain.'],
    methodDecision='Stop retuning this graduated-cut/lateral-field construction. A next round must change the root-to-tip construction premise on the same actual scalp and review the complete working woman.',
    source=draft['source'],parent=draft['parent'],variants=draft['variants'],
    comparison=dict(path=str(ROOT/'r0483-comparison.png'),sha256=sha(ROOT/'r0483-comparison.png')),
    renders=draft['renders'],reopenVerification=verified,
    rootPreservation='All 24,831 roots remain bit-identical to r482 B. IDs, radii and physical binding fields match the r482 B hashes.',
    uvScope='Triangle-island UV anchor mapping verified after reopen. Maximum surface-anchor float32 error is approximately 0.001034 mm. Actual native brush operation remains unverified.',
    contactStatus='NOT_EVALUATED. Rebuilt lengths invalidate inherited rest and motion contact results. No zero-penetration claim.',
    skippedChecksReason='Visible rejection precedes broad collision, motion and engine audits under repository instructions.',
    sourceScope='Standalone neutral hair and skin fixture. No eyes, rig, facial controls or clothing. Full-body fixture images are not proof of the complete working woman.',
    strictScoreChanged=False,appearanceAdopted=False,engineIntegrated=False,websiteChanged=False,
    nativeBrushOperationPerformed=False,
    pendingUI='Observed launch-server.exe Windows security permission dialog blocks Blender. User handoff remains pending. No security setting or dialog was automated.',
    originalWorkspace='Original C:/AevryndVolume junction is present but its Aevrynd directory is inaccessible. No r425 staging or archive claim can be verified there. F-side independent archive is available.',
    resources=dict(workerThreads=4,previewPeakPrivateBytes=2501095424,reopenPeakPrivateBytes=1574313984,
        originalStartUTC='2026-11-10T22:54:54Z',firstCompleteSetFinishedTaipei='2026-11-11T07:06:16+08:00',
        previewDeadlineUTC='2026-11-10T23:24:54Z',resourceCheckpointUTC='2026-11-10T23:39:54Z'),
    recordedAtUTC=datetime.now(timezone.utc).isoformat(),
    history='Transport receipt follows separately. This round does not establish the archival status of older unpublished rounds.')
with (ROOT/'r0483-review.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(decision=record['decision'],source=draft['source'],image=record['comparison']),indent=2))
