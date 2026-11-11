from pathlib import Path
from hashlib import file_digest
import shutil,json
ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SRC=Path('assets-source/aevrynd-character/female-next/r0485-source')
EVID=Path('evidence/character-female-next/r0485-native-root-to-tip')
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    assert not (REPO/SRC).exists() and not (REPO/EVID).exists()
    (REPO/SRC/'data').mkdir(parents=True);(REPO/SRC/'licenses').mkdir();(REPO/EVID).mkdir(parents=True)
    receipt=json.loads((ROOT/'sealed-source-receipt.json').read_text())
    source=Path(receipt['source']['path']);assert sha(source)==receipt['source']['sha256']
    shutil.copyfile(source,REPO/SRC/source.name)
    for path in ROOT.glob('*.npz'):shutil.copyfile(path,REPO/SRC/'data'/path.name)
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.py','.ps1','.png','.json','.log','.err','.txt')]
    assert not any('archive-' in p.name or p.name=='continuation.json' for p in paths)
    for path in paths:shutil.copyfile(path,REPO/EVID/path.name)
    prev=REPO/'assets-source/aevrynd-character/female-next/r0484-source/licenses'
    for path in prev.iterdir():
        if path.is_file():shutil.copyfile(path,REPO/SRC/'licenses'/path.name)
    readme='''Aevrynd female-next r0485

Both actual native Curve Sculpt studies are rejected for character adoption. A uses four spherical Comb strokes; B continues A with eight projected strokes over front and back regions. Exact input coordinates, observed UI settings, save behavior and scope are recorded in native-actions.json. No new primary-guide hierarchy was created. The existing dense failed construction was sculpted directly.

The final female-next-r0485-native-groom-portable-UNACCEPTED.blend contains control, A, B and inherited rollback data, the actual same woman, ocular parts, controls, materials and packed images. Native A changed 776 curves. Native B changed 23,780 curves and 1,240,521 points. All 24,831 follicles remain bit-identical to the input, with persistent curve/point IDs, radii, actual scalp attachment and physical binding fields preserved. Independent final-source evaluation reproduces the r480 neutral skin vertex and triangle hashes exactly.

All five final views render every position bank through one persistent curve object and data block in one scene. Only point positions change between modes, retaining the same material, radii, object identity, camera, lights, exposure, frame, samples and seed. The source file is not saved after render switching.

The final source independently reopens without external libraries or unpacked file images. An earlier in-process seal assertion about an external reference failed without capturing its list. A later independent fresh read of that exact earlier seal also had no external references. The condition was not reproduced and its cause is unknown. The earlier assertion that the brush caused a dependency, or that localization demonstrably fixed one, is not established. The historical embedded Editor_Dependency_Note is superseded by this correction and the r0485-review/source-state records. No causal inference is required for the verified final file state.

Native surface collision was enabled at a displayed 0.005 m setting. This does not certify whole-span finite hair/body or hair/hair clearance. Collision count and minimum signed gap are null because visible rejection preceded broad audits. Hair dynamics, expressions, clothing, engine timing and user acceptance remain unverified. No score was increased and no website or formal runtime asset changed.

The original Angelica head/hair source retains DarkNik / original NikZava284 attribution under CC BY 4.0, with inherited CC0 body lineage and historical source qualifications preserved in licenses and Blender text blocks. Existing Blender Comb is an authoring tool, not an Aevrynd runtime dependency or exclusively owned artwork. No new software or paid platform was installed.

The complete native point banks and all relevant fields are retained in data. Exact separate A/B .blend checkpoints, the superseded initial seal and the mutable UI working file remain on F; their hashes and receipts are retained here. The final source preserves their exact native geometries. The original prepared .blend was overwritten by ordinary GUI save; its source hash, preparation script, parent and complete initial positions remain retained. Original scripts retain local parent paths. Older unpublished history and r425 staging remain unresolved.

Native input is now operational and the prior security handoff is resolved. Future work must construct coherent sparse primary guides and scalp ownership before child fibres, rather than repeat full-groom combing of the failed dense bank. This study is not female acceptance or completion of the persistent goal.
'''
    (REPO/SRC/'README.md').write_bytes(readme.encode('utf8'))
    manifest={}
    for base in (REPO/SRC,REPO/EVID):
        for path in sorted(base.rglob('*')):
            if path.is_file():manifest[path.relative_to(REPO).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    blob=json.dumps(manifest,indent=2).encode('utf8')
    (ROOT/'archive-package-manifest.json').write_bytes(blob);(REPO/EVID/'archive-package-manifest.json').write_bytes(blob)
    print(json.dumps(dict(files=len(manifest)+1,bytes=sum(v['bytes'] for v in manifest.values()),source=receipt['source']),indent=2))
if __name__=='__main__':main()
