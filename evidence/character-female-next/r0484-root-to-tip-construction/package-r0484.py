from pathlib import Path
from hashlib import file_digest
import shutil
import json
ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SRC=Path('assets-source/aevrynd-character/female-next/r0484-source')
EVID=Path('evidence/character-female-next/r0484-root-to-tip-construction')
def sha(path):
    with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    assert not (REPO/SRC).exists() and not (REPO/EVID).exists()
    (REPO/SRC/'data').mkdir(parents=True);(REPO/SRC/'licenses').mkdir();(REPO/EVID/'reference').mkdir(parents=True)
    source=json.loads((ROOT/'volume-source-receipt.json').read_text())['source']
    assert sha(Path(source['path']))==source['sha256']
    shutil.copyfile(source['path'],REPO/SRC/Path(source['path']).name)
    for path in ROOT.glob('*.npz'):shutil.copyfile(path,REPO/SRC/'data'/path.name)
    # Only explicit current-round file classes. No cache or unrelated installer output.
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.py','.ps1','.png','.json','.log','.err','.txt')]
    assert not any('archive-' in p.name or p.name=='continuation.json' for p in paths)
    for path in paths:shutil.copyfile(path,REPO/EVID/path.name)
    for path in (ROOT/'reference').iterdir():
        if path.suffix=='.npz':dest=REPO/SRC/'data'/path.name
        else:dest=REPO/EVID/'reference'/path.name
        shutil.copyfile(path,dest)
    previous=REPO/'assets-source/aevrynd-character/female-next/r0483-source/licenses'
    for name in ('aevrynd-female-next-r0126.LICENSE-SOURCE.txt','aevrynd-female-next-r0139.LICENSE-SOURCE.txt','LICENSE-female-next-r0220.txt','origin.json'):
        shutil.copyfile(previous/name,REPO/SRC/'licenses'/name)
    shutil.copyfile(ROOT/'reference/reference-and-rights.json',REPO/SRC/'licenses/reference-and-rights.json')
    text='''Aevrynd female-next r0484

Both hair reconstructions are rejected for character adoption. A maps actual follicles to sampled paths from the same artist's original hair strips; B replaces transported planar offsets with elliptical volume cross sections. Complete face, profile, rear and whole-woman views still show flat sheets, thick curls and unnatural root flow. No score or runtime asset changes.

The standalone female-next-r0484-volume-locks-UNACCEPTED.blend contains control, A and B, the actual same-woman neutral skin, ocular parts, source controls, materials and packed images. All 24,831 follicles, persistent curve/point IDs, radii and physical scalp-binding fields are retained. The canonical binding skin and actual evaluated neutral skin have exactly equal vertex coordinates. The original artist mesh is a hidden reference and is absent from candidate renders.

The final source was independently reopened and has no linked libraries or external image dependencies. It does not certify complete character function. Hair motion is not reconnected. Face expressions, clothing, finite contact, continuous motion, engine performance and user acceptance are incomplete. No zero-penetration claim is made for reconstructed hair; contact count and minimum clearance are explicitly null because visible rejection preceded broad contact audits.

The final packed file is the authority for the archived images. All final variants use the same source, lights, camera, exposure, frame, neutral blink, sample count, seed, shader and radii. Earlier and final raw pixel hashes differ for the same-position control and A after dependency localization/packing. The cause is unresolved. Pre/post localization appearance equivalence is not claimed. Earlier images and the contradiction are retained.

The original Angelica head/hair source is attributed to DarkNik / original NikZava284, https://sketchfab.com/3d-models/angelica-27f75fa94c384000bb6a79a3000f8e80, under CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Existing CC0 body lineage, historical notices and separate qualifications are preserved in licenses and embedded Blender texts. Original artwork is not exclusively owned by Aevrynd. No paid platform or runtime was installed or imported.

This archive retains the final source containing all three branch geometries, all round data, scripts, render sets, reference records and minimum reopening evidence. Intermediate linked assembly and A .blend files remain on F; their source hashes and images are retained here. Original scripts preserve their original F-side parent paths. Full reconstruction therefore still requires the original r480 source and the noted older offline dependencies. The final packed file itself can be opened directly in Blender without those dependencies. Older unpublished history and r425 staging remain separate unresolved work.

The persistent female-first goal remains active. Neither B's default visibility nor the existence of a complete neutral study constitutes appearance adoption or female acceptance.
'''
    (REPO/SRC/'README.md').write_bytes(text.encode('utf8'))
    manifest={}
    for base in (REPO/SRC,REPO/EVID):
        for path in sorted(base.rglob('*')):
            if path.is_file():manifest[path.relative_to(REPO).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    data=json.dumps(manifest,indent=2).encode('utf8')
    (ROOT/'archive-package-manifest.json').write_bytes(data)
    (REPO/EVID/'archive-package-manifest.json').write_bytes(data)
    print(json.dumps(dict(files=len(manifest)+1,bytes=sum(v['bytes'] for v in manifest.values()),source=source),indent=2))

if __name__=='__main__':main()
