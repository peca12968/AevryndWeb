"""Bounded CC0 artist-asset inspection; no full pack download or code import."""
import importlib.util, json, zipfile, hashlib
from pathlib import Path
R=Path('D:/Download/Aevrynd'); E=R/'Evidence/character-female-next/r0036-data-informed-brows'
S=R/'engine/assets/characters/female-next/source'; E.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('fetch11',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def main():
    source=S/'aevrynd-female-next-r0035-b-neutral-rest-review.blend'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='e522f587e7f9d5e5df7564b1ff0c38f75575dda3e6e6b1806ae2eee662b0c168'
    contract={'revision':'r0036','previousGoalTurnClassification':'progress: v8 execution contract saved and GitHub verified; prompt maintenance only, not a model iteration',
      'source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'majorDefects':['Absent brows/lashes and synthetic eyes','Artificial full scalp hair, rejected groom','Incomplete skin and oral structure'],
      'selectedDefect':'Absent eyebrows; produce a complete independent brow layer on the retained full head.',
      'expectedVisibleDifference':'Readable, tapered eyebrows framing both eyes at full-head viewing distance without changing skin or eye state.',
      'pilot':'Inspect licensed existing photographic/artist data. Reject invalid silhouette/direction donor before geometry expansion. Small mapped full-head brow first.',
      'stoppedDonorRoute':'Existing young_lightskinned_female_diffuse3 CC0 image inspected at original resolution and upright head crop; eyebrows too faint/blurred to recover fibre flow. No skin darkness transfer.',
      'newArchitecture':'Inspect an explicitly CC0 existing artist-authored eyebrow alpha/mesh before inventing another random local follicle field. Use actual source data for silhouette and directions where valid; separate editable surface attachment and resulting geometry.',
      'notAllowed':'No r31 short-upright/random or greedy fixed-follicle lift/density sweep; no changing body/nativeUV, lid rest, eye positions, skin/exposure or scalp-hair STRIP0.',
      'decisionGates':['Multi-angle actual full-head improvement, no sticker/coarse wire morphology','All affected actual-radius body/eye/scalp-hair and self interfaces checked in explicitly stated neutral scope','Source geometry/material/skin/lighting exact; root bindings reproducible'],
      'resources':{'threads':4,'heavyJobs':1,'candidateCount':1,'maximumDifferentBasisCandidates':3,'checkpointMinutes':45,'firstDiagnosticMinutes':10,'scalpHairNotRegenerated':True},
      'references':[{'url':'https://rcst.or.th/ejournal/files/Vol25_No2_47.PDF','use':'Primary observational anatomy, p49 results: small medial upright hairs, directed body and tapered tail; anatomical modeling reference, no clinical procedure implemented.'},
      {'url':'https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/hair/generation/interpolate_hair_curves.html','use':'Search-visible official interpolation/attachment overview only; full web open inaccessible. No node code copied.'}],
      'scope':'Neutral brows on the integrated r35 head. No blink/gaze/rig/dynamics/runtime or full-character score acceptance.'}
    (E/'round-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    remote=f.RemoteZip(f.URL)
    with zipfile.ZipFile(remote) as z:
        rows=[{'name':i.filename,'bytes':i.file_size,'compressed':i.compress_size} for i in z.infolist() if 'eyebrow' in i.filename.lower() and not i.is_dir()]
    result={'url':f.URL,'archiveBytes':remote.size,'etag':remote.etag,'entries':rows,'transferredBytes':sum(x['bytes'] for x in remote.requests)}
    (E/'cc0-eyebrow-index.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8'); print(json.dumps(result),flush=True)
if __name__=='__main__':main()
