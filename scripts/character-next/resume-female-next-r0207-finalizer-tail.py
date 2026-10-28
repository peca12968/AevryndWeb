from pathlib import Path
import json,datetime
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));a=Path(access['directCharacterArchiveAccess']);e=a/'evidence/character-female-next/r0207-exact-surface-guide-deformation';f=a/'scripts/character-next/finalize-package-female-next-r0207.py';text=f.read_text('utf-8')
exec(text.split('now=datetime.datetime.now',1)[0])
assert git('rev-parse','HEAD').decode().strip()==publicationParent and not git('diff','--cached','--name-only')
t=read(E/'before.json');before=read(E/'manifest-before.json');prior=read(E.parent/'r0206-operative-guide-anatomical-map/continuation.json');working=prior['workingCompleteWomanReference'];builds={'a':read(E/'a-build-summary.json'),'b':read(E/'b-build-summary.json')};rights=read(E/'references-and-rights.json');audit=read(E/'continuation.json');assert audit['confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound']==81
manifest=read(R/'engine/assets/characters/female-next/female-next.asset.json');assert manifest['latestStudyRevision']=='female-next-r0207' and manifest['confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound']==81
for key in ['currentSourceRevision','currentSource','runtimeAsset','strictOverallScore','strictScoreAppliesTo','enginePromotionApproved','websitePromotionApproved','workingCompleteWomanReference']:assert manifest[key]==before[key]
assert not (E/'history-allowlist.json').exists()
(E/'finalizer-original-at-failure.py').write_bytes(f.read_bytes());(E/'finalizer-original-failure-terminal.txt').write_bytes(Path('F:/AevryndEvidence/CharacterTemp/r207-finalize.log').read_bytes())
save(E/'finalizer-resumption.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalTerminal':'finalizer process exited1; no live original job. Existing models, audit and manifest persisted before error.','failure':'Wrong preview lookup: F variable meant F:/AevryndStorage, previews are in F:/AevryndEvidence/r0207-exact-surface-guide-deformation.','resumption':'Execute original tail from times only using corrected reviewF path. No rebuild, recapture, recount, manifest rewrite, clock reset or source modification.','originalScriptSHA256':sha(f)})
reviewF=Path('F:/AevryndEvidence/r0207-exact-surface-guide-deformation');now=datetime.datetime.now(datetime.timezone.utc)
tail='times='+text.split('times=',1)[1];tail=tail.replace("(F/f'matched-", "(reviewF/f'matched-")
exec(compile(tail,str(f)+' [tail-only corrected review path]','exec'))