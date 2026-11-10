"""Create an explicit r483 archive package without touching existing history."""
from pathlib import Path
from hashlib import file_digest
import shutil
import json

ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SOURCE=Path('assets-source/aevrynd-character/female-next/r0483-source')
EVIDENCE=Path('evidence/character-female-next/r0483-layered-bob-rest')
def digest(path):
    with path.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()
def write(path,text):path.write_bytes(text.encode('utf8'))
def main():
    assert not (REPO/SOURCE).exists() and not (REPO/EVIDENCE).exists()
    (REPO/SOURCE/'data').mkdir(parents=True)
    (REPO/SOURCE/'licenses').mkdir()
    (REPO/EVIDENCE/'camera-inputs').mkdir(parents=True)
    files=[*ROOT.glob('*.py'),ROOT/'run-r0483.ps1',ROOT/'make-comparison.ps1',ROOT/'work-card.txt',
        ROOT/'shape-receipt.json',ROOT/'draft-receipt.json',ROOT/'reopen-verification.json',ROOT/'r0483-review.json',
        ROOT/'replay-check-UNACCEPTED.replay.json',ROOT/'replay.log',
        ROOT/'author.log',ROOT/'author.err',ROOT/'preview.log',ROOT/'preview.err',ROOT/'verify.log',ROOT/'verify.err',
        ROOT/'r0483-comparison.png']
    for tag in ('base','A','B'):
        for view in ('posterior-detail','rear-oblique','face','opposite-profile','full-body'):
            files.append(ROOT/f'{tag}-{view}.png')
    assert all(p.is_file() for p in files)
    for path in files:shutil.copyfile(path,REPO/EVIDENCE/path.name)
    for name in ('female-next-r0483-native-shape-work-UNACCEPTED.blend','female-next-r0483-layered-bob-drafts-UNACCEPTED.blend'):
        shutil.copyfile(ROOT/name,REPO/SOURCE/name)
    for name in ('shape-base.npz','shape-A.npz','shape-B.npz','prepared-shape-A.npz','prepared-shape-B.npz'):
        shutil.copyfile(ROOT/name,REPO/SOURCE/'data'/name)
    parent=REPO/'assets-source/aevrynd-character/female-next/r0482-source/licenses'
    for name in ('aevrynd-female-next-r0126.LICENSE-SOURCE.txt','aevrynd-female-next-r0139.LICENSE-SOURCE.txt','LICENSE-female-next-r0220.txt','origin.json'):
        shutil.copyfile(parent/name,REPO/SOURCE/'licenses'/name)
    for view in ('posterior-detail','rear-oblique','face','opposite-profile','full-body'):
        name=f'shot-A-{view}.json'
        shutil.copyfile(ROOT.parent/'r0470-independent-posterior-locks'/name,REPO/EVIDENCE/'camera-inputs'/name)
    write(REPO/SOURCE/'README.md','''Aevrynd female-next r0483

Both graduated-cut and diagonal-crown-flow studies are rejected for character adoption. Complete neutral head views retain a rounded cap and a thick lower fringe. Local tip changes do not establish a believable full hairstyle. No score, formal character, website or runtime asset changes.

The authoritative final draft is female-next-r0483-layered-bob-drafts-UNACCEPTED.blend. It contains the r482 B control and two r483 candidates, each with 24,831 curves and 80 points per curve. The first native-shape-work file preserves the intermediate draft. prepared-shape-A/B.npz match final candidate positions. The earlier shape-A/B.npz preserve the initial intermediate state before exact restoration of unselected strands.

All roots, IDs, radii and physical scalp-binding fields remain identical to r482 B. The new triangle-island scalp UV atlas and surface_uv_coordinate fields were checked after reopening. Maximum UV surface-anchor float32 error is approximately 0.001034 mm. Native Curve Sculpt input was not performed because launch-server.exe displayed a Windows security permission dialog. Having UV attributes does not certify successful native brush operation.

Free-length changes invalidate the inherited collision and motion evidence. No zero-penetration claim is made for either candidate. Broad contact, motion and engine tests were skipped after visible rejection. This is a neutral unrigged skin-and-hair fixture. Eyes, facial controls, clothes and the complete working woman are absent. Full-body fixture images cannot establish complete-character acceptance.

The package retains unchanged upstream notices, embedded source credits, and r482 origin metadata. Angelica head artwork is attributed to DarkNik / original NikZava284 under CC BY 4.0. The body retains its inherited CC0 source chain. Historical notices include separate qualifications. No exclusive ownership or complete upstream rights qualification is asserted for third-party artwork.

From the repository root, reproduce the final geometry using the existing Blender installation and the archived r482 source. This replay was run and all three position hashes and native UV hashes matched exactly after reopening. File-byte equivalence is not claimed.

```powershell
& 'D:/SteamLibrary/steamapps/common/Blender/blender.exe' -b --factory-startup --disable-autoexec -t 4 --python-exit-code 17 --python 'evidence/character-female-next/r0483-layered-bob-rest/rebuild-r0483.py' -- --parent 'assets-source/aevrynd-character/female-next/r0482-source/female-next-r0482-global-groom-UNACCEPTED.blend' --out 'F:/AevryndEvidence/r0483-replay-UNACCEPTED.blend'
```

Original author/prepare/verify scripts retain their original F-side input paths and receipts. Five original fixed-camera inputs are also retained in the evidence package. The replay command above is independent of those local paths and needs no new software, online assets or paid platform.

The original VHDX project entry remained inaccessible in this session. r425 staging and earlier unpublished rounds are not resolved by this r483 archive. Pending user security handoff remains separate. The persistent female-first character goal is active.
''')
    manifest={}
    for base in (REPO/SOURCE,REPO/EVIDENCE):
        for path in sorted(base.rglob('*')):
            if path.is_file():manifest[path.relative_to(REPO).as_posix()]=dict(bytes=path.stat().st_size,sha256=digest(path))
    data=json.dumps(manifest,indent=2).encode('utf8')
    (ROOT/'archive-package-manifest.json').write_bytes(data)
    (REPO/EVIDENCE/'archive-package-manifest.json').write_bytes(data)
    print(json.dumps(dict(files=len(manifest)+1,bytes=sum(p['bytes'] for p in manifest.values()),source=str(REPO/SOURCE)),indent=2))

if __name__=='__main__':main()
