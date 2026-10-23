"""Preserve and correct initial confusion between a candidate and an actual failed trial."""
from pathlib import Path
import json,hashlib,subprocess,os,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');M=C/'assets-source/aevrynd-character/female-next';E=C/'evidence/character-female-next/r0181-inner-lid-follicle-domain'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=read(E/'continuation.json');assert not audit['actualProductionRoundCountedOnce'];assert not audit['pureStartupError'];before=read(E/'manifest-before.json');assert before['confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound']==54
initial={'continuation':audit,'initialResource':read(E/'attempt-resource-summary.json'),'initialManifest':read(M/'female-next.asset.json'),'reasonForPreserving':'Initial accounting incorrectly conflated no saved candidate with no actual round. Actual metric-domain construction executed and failed spatial qualification at first root; it is not a pure startup error.'};save(E/'initial-counter-classification-preserved.json',initial)
correction={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalClassificationPreserved':str(E/'initial-counter-classification-preserved.json'),'evidence':['Original builder actually loaded actual Skin, established source ancestry, constructed a geodesic surface graph and attempted inverse root construction before spatial AssertionError.','Original record already states pureStartupError=false; actual failed/unregistered trials count under current project instructions.','Candidate generation and complete-character improvement remain false; a failed actual support trial is counted once, not relabeled completed geometry.'],'counterBaseCopiedFromBefore':54,'newFailedActualRoundCount':55,'previousCadence':1,'newCadence':2,'nextWholeReviewAfterFurtherActualRounds':1,'noClockAttemptCostFailureOrSourceChanged':True};save(E/'failed-round-accounting-correction.json',correction)
audit.update(actualProductionRoundCountedOnce=True,actualRoundKind='FAILED_ACTUAL_SURFACE_CONSTRUCTION_SUPPORT_ROUND',confirmedConsecutiveRoundsWithoutAdoptedCompleteGainLowerBound=55,confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound=55,productionRoundsSinceLastWholeCharacterReview=2,nextWholeReviewAfterFurtherProductionRounds=1,actualCharacterCandidateProduced=False,actualCompleteCharacterImprovement=False,counterClassificationCorrection=str(E/'failed-round-accounting-correction.json'))
audit['nextAction']=audit['nextAction'].replace('no completed actual production round or adopted gain, counters remain54/cadence1,next whole after2','failed actual support round counted once with no candidate or adopted gain, counters55/cadence2,next whole after1')
audit['lastGoalTurnClassification']=audit['lastGoalTurnClassification'].replace('no model/improvement or completed production-round recount.','no model/improvement; actual failed support trial counted once, candidate absence does not exempt the failed round.')
for p in [E/'continuation.json',E/'female-next-r0181.visual-audit.json']:save(p,audit)
resource=read(E/'attempt-resource-summary.json');resource.update(actualFailedSupportRoundCountedOnce=True,completedCharacterCandidateCount=0,failedRoundAccountingCorrection=str(E/'failed-round-accounting-correction.json'));save(E/'attempt-resource-summary.json',resource)
manifest=read(M/'female-next.asset.json');manifest.update(confirmedConsecutiveRoundsWithoutAdoptedCompleteGainLowerBound=55,confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound=55,nextRequiredWork=audit['nextAction']);manifest['terminalPreCandidateAttemptR181'].update(completedProductionRound=False,actualFailedProductionTrialCountedOnce=True,counterClassificationCorrection=str(E/'failed-round-accounting-correction.json'))
blob=(json.dumps(manifest,separators=(',',':'))+'\n').encode()
for p in [M/'female-next.asset.json',R/'engine/assets/characters/female-next/female-next.asset.json']:p.write_bytes(blob)
allow=read(E/'history-allowlist.json');inte=read(E/'history-copy-integrity.json');new=[E/'initial-counter-classification-preserved.json',E/'failed-round-accounting-correction.json',Path(__file__)]
for p in new:
 rel=p.relative_to(C).as_posix();allow.append(rel);inte['files'].append({'file':rel,'sha256':sha(p),'bytes':p.stat().st_size})
for x in inte['files']:
 p=C/x['file'];x.update(sha256=sha(p),bytes=p.stat().st_size)
inte['initialAccountingPreservedAndCorrectedByActualFailedTrialEvidence']=True;save(E/'history-copy-integrity.json',inte);allow=sorted(set(allow));save(E/'history-allowlist.json',allow)
env=os.environ.copy()
for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
def git(*a):return subprocess.check_output(['git','-C',str(C),'-c','core.autocrlf=false',*a],env=env)
git('add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
for rel in allow:assert git('show',':'+rel)==(C/rel).read_bytes()
git('diff','--cached','--check');print(json.dumps({'failedActualRoundCountedOnce':True,'candidateCount':0,'noAdopt':55,'cadence':2,'nextWholeAfter':1,'exactStagedFiles':len(allow)}))
