from pathlib import Path
from hashlib import file_digest
import shutil,json
R=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SRC=Path('assets-source/aevrynd-character/female-next/r0486-source')
EVID=Path('evidence/character-female-next/r0486-primary-guide-foundation')
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
receipt=json.loads((R/'construction-receipt.json').read_text())
assert not (REPO/SRC).exists() and not (REPO/EVID).exists()
(REPO/SRC/'data').mkdir(parents=True);(REPO/SRC/'licenses').mkdir();(REPO/EVID).mkdir(parents=True)
source=Path(receipt['source']['path']);assert sha(source)==receipt['source']['sha256']
shutil.copyfile(source,REPO/SRC/source.name)
shutil.copyfile(R/'primary-guide-construction.npz',REPO/SRC/'data/primary-guide-construction.npz')
names=['author-r0486.py','inspect-r0486.py','preview-r0486.py','review-r0486.py','package-r0486.py','run-r0486.ps1','make-review-r0486.ps1','work-card.txt','construction-receipt.json','reopen-verification.json','preview-receipt.json','r0486-review.json','author.log','author.err','inspect.log','inspect.err','preview.log','preview.err','r0486-head-comparison.png','r0486-profile-body-comparison.png']
names.extend(f'{tag}-{view}.png' for tag in ('control','candidate') for view in ('face','rear-oblique','opposite-profile','posterior-detail','full-body'))
for name in names:shutil.copyfile(R/name,REPO/EVID/name)
for p in (REPO/'assets-source/aevrynd-character/female-next/r0485-source/licenses').iterdir():
    if p.is_file():shutil.copyfile(p,REPO/SRC/'licenses'/p.name)
readme='''Aevrynd female-next r0486 — unaccepted primary-guide foundation

Rejected for character adoption. The new foundation removes the large failed curls and establishes coherent straight root-to-tip flow, but profile/rear views show ear protrusion through the hair, a long posterior central opening, smooth curtain surfaces and blunt lengths. No score, quality acceptance, website or formal runtime asset changed. Female acceptance and male development remain pending.

The packed Blender source preserves the same complete woman, ocular parts, controls, inherited materials/images, r485/r484 rollback branches, one new complete child groom and 126 editable native primary curves. Six scalp domains select representative actual follicles. Each primary path follows the actual neutral skin tangent and then gravity; four nearby primary displacements drive every child. This replaces the failed inherited free lengths rather than combing them again. All 24,831 original roots, persistent curve/point IDs, physical scalp binding fields and radii are unchanged. The sidecar stores guide source IDs, regions, child ownership/weights and full candidate positions. Fresh reopening reproduces the stored guide interpolation exactly and finds no external linked libraries or unpacked file images.

Primary paths have source-follicle IDs but have not been independently operated in native Sculpt or given a complete deforming surface attachment. Native guide editing, full finite hair/body and self-contact, motion, clothing, export and Aevrynd CPU/GPU timings remain unverified. Penetration count and minimum signed gap are null because the visible failure stopped broad audits; this is not a zero-penetration claim. Scene statistics include hidden rollback/neutral fixture meshes. Rendering uses the same persistent carrier object/data, shader, radii, cameras, lights, exposure, sample counts and seed for control and candidate; only positions switch in memory. The source is not saved after render switching.

The inherited Angelica source retains DarkNik / original NikZava284 attribution under CC BY 4.0, inherited CC0 body lineage, and historical qualifications in licenses and Blender text blocks. No new external art, software or paid runtime dependency was introduced. No exclusive ownership or completed provenance audit is claimed. The historical r485 embedded localization narrative remains superseded by its review: an earlier assertion was not reproduced and its cause is unknown.

Next work must author continuous occipital paths across the midline and temple/ear routes around the actual ear silhouette, with middle-scale section variation, before regenerating children. Preserve the useful guide/ownership data without accepting this failed appearance. r483/r484 retired methods and repeated dense combing remain retired; no stagnation counter resets. Original project VHDX/r425 staging and older unpublished history remain unverified. All working files and evidence are on F; existing Blender executable on D is unchanged.
'''
(REPO/SRC/'README.md').write_bytes(readme.encode('utf8'))
manifest={}
for base in (REPO/SRC,REPO/EVID):
    for p in sorted(base.rglob('*')):
        if p.is_file():manifest[p.relative_to(REPO).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
blob=json.dumps(manifest,indent=2).encode('utf8');(R/'archive-package-manifest.json').write_bytes(blob);(REPO/EVID/'archive-package-manifest.json').write_bytes(blob)
print(json.dumps(dict(files=len(manifest)+1,rawBytes=sum(x['bytes'] for x in manifest.values()),source=receipt['source']),indent=2))
