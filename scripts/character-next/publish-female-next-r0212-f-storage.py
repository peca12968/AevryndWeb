"""Reject203 complete current-space Bezier form; preserve77 no-adopt and whole201202203 review."""
from pathlib import Path
import json,hashlib,datetime,os,subprocess,ctypes,struct,shutil
from ctypes import wintypes as w
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));R=Path(access['directProjectAccess']);C=Path(access['directCharacterArchiveAccess']);G=R/'sites-engine-journey';M=C/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=C/'evidence/character-female-next/r0212-complete-artist-volume-foundation';repo='//./'+str(C)[4:].replace('\\','/');F=Path('F:/AevryndStorage');hookPath=Path(access['temporaryWorkspace'])/'normal-git-hooks-f-access';publicationParent='4e2e9495dc48abe0c4ad6efbf97576ccdf9dde3c'
def read(f):return json.loads(Path(f).read_text('utf-8'))
def save(f,d):Path(f).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def sha(f):
 p=Path(f);p=p if p.is_absolute() else R/p;return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
env=os.environ.copy()
for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_OPTIONAL_LOCKS='0',GOMAXPROCS='4')
def git(*args):
 r=subprocess.run(['git','--git-dir='+repo+'/.git','--work-tree='+repo,'-c','core.hooksPath='+str(hookPath),'-c','core.autocrlf=false','-c','pack.threads=4','-c','pack.windowMemory=32m','-c','lfs.concurrenttransfers=2',*args],cwd=str(F),env=env,capture_output=True)
 globals()['lastGitStderr']=r.stderr.decode('utf-8','replace')
 if r.returncode:raise RuntimeError(json.dumps({'args':args,'exit':r.returncode,'stdout':r.stdout.decode('utf-8','replace')[-2500:],'stderr':r.stderr.decode('utf-8','replace')[-2500:]}))
 return r.stdout


t=read(E/'before.json');audit=read(E/'continuation.json');integ=read(E/'history-copy-integrity.json');allow=read(E/'history-allowlist.json');assert git('rev-parse','HEAD').decode().strip()==t['baseCommit']==publicationParent;assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
for row in integ['files']:assert sha(C/row['file'])==row['sha256'],row['file']
extra=[Path(__file__)];allow=sorted(set(allow+[f.relative_to(C).as_posix() for f in extra]));excluded=[(E/n).relative_to(C).as_posix() for n in ['history-copy-integrity.json','history-allowlist.json']];integ['files']=[{'file':rel,'sha256':sha(C/rel),'bytes':(C/rel).stat().st_size} for rel in allow if rel not in excluded];save(E/'history-copy-integrity.json',integ);save(E/'history-allowlist.json',allow);git('add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
lfs={r['file']:r for r in integ['normalFullLFSObjects']};assert len(lfs)==2
for rel in allow:
 data=git('show',':'+rel)
 if rel in lfs:
  row=lfs[rel];assert data==f'version https://git-lfs.github.com/spec/v1\noid sha256:{row["sha256"]}\nsize {row["bytes"]}\n'.encode();cache=Path(row['completeNormalObject']);assert sha(cache)==sha(C/rel)==row['sha256'] and cache.stat().st_size==row['bytes'] and os.path.samefile(cache,C/rel)
 else:assert data==(C/rel).read_bytes(),rel
for label in ['a']:
 b=read(E/('build-summary.json' if label=='a' else 'b-build-summary.json'));assert sha(b['userReviewSource'])==b['sha256']
git('diff','--cached','--check');assert not env.get('GIT_LFS_SKIP_PUSH');assert sum(f.stat().st_size for f in E.iterdir() if f.is_file())+12000<t['evidenceBudgetBytes'];assert sum(f.stat().st_size for f in E.iterdir() if f.is_file())+sum(r['bytes'] for r in lfs.values())+2000000<t['estimatedPackBudgetBytes'] and sum(r['bytes'] for r in lfs.values())<t['sourceBudgetBytes'];assert audit['confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound']==86 and audit['productionRoundsSinceLastWholeCharacterReview']==0
for original in (C/'.git/hooks').iterdir():
 if original.is_file():assert sha(original)==sha(hookPath/original.name)
assert git('remote','get-url','github').decode().strip()=='https://github.com/peca12968/AevryndWeb.git';remoteBefore=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remoteBefore==publicationParent;print('R212_EXACT_TWO_FULL_SAVES_PACKAGE_READY',json.dumps({'files':len(allow),'sourceTotalBytes':sum(r['bytes'] for r in lfs.values()),'noAdopt':86,'cadence':0}),flush=True)
git('commit','-m','character: preserve r212 rejected volume field and original CC0 source');head=git('rev-parse','HEAD').decode().strip();assert git('rev-parse','HEAD^').decode().strip()==publicationParent;print('R212_LOCAL_COMMIT',head,flush=True)
receipt={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'localCommit':head,'originalProductionParent':t['baseCommit'],'remote':'https://github.com/peca12968/AevryndWeb.git','branch':'character-history-v249','normalFullLFSObjects':list(lfs.values()),'normalByteIdenticalOriginalHooksUsed':True,'originalHookAndConfigUnmodified':True,'normalHookAccessProof':str(E/'normal-hooks-f-access.json'),'pushed':False};save(E/'github-receipt.json',receipt)
try:
 push=git('push','github','HEAD:refs/heads/character-history-v249');pushErr=lastGitStderr;remote=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remote==head;receipt.update(pushed=True,remoteCommit=remote,verifiedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),normalPushStdout=push.decode('utf-8','replace'),normalPushStderr=pushErr)
except Exception as error:receipt['error']=str(error);save(E/'github-receipt.json',receipt);raise
save(E/'github-receipt.json',receipt);assert not git('diff','--cached','--name-only') and not git('status','--short','--untracked-files=no');evidence=sum(f.stat().st_size for f in E.iterdir() if f.is_file());save(E/'completion-resource-receipt.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':t['startedUTC'],'originalSupportDeadlineUTC':t['supportDeadlineUTC'],'originalPreviewDeadlineUTC':t['firstCompletePreviewDeadlineUTC'],'originalResourceCheckpointUTC':t['resourceCheckpointUTC'],'sourceBytes':{r['file']:r['bytes'] for r in lfs.values()},'sourceTotalBytes':sum(r['bytes'] for r in lfs.values()),'evidenceBytes':evidence,'fullSaveLFSAndEstimatedPackBytes':sum(r['bytes'] for r in lfs.values())+evidence+2000000,'originalSourceEvidenceAndEstimatedPackCapsPreserved':True,'originalEvidenceBudgetExceeded':False,'originalEvidenceBudgetBytes':t['evidenceBudgetBytes'],'actualPeakRAMAndPackBytesNotMeasured':True,'actualPeakRAMAndNetworkPackBytesNotMeasured':True,'normalCompleteLFSObjectsVerified':2,'normalRemoteCommit':head,'newCompleteWomanCandidates':0,'actualRoundCount':1,'noAdopt':86,'cadence':0,'nextWholeAfter':3,'noCompleteAppearanceOrOperationGain':True,'goal':'active'});print('R212_NORMAL_TWO_FULL_SAVES_GITHUB_VERIFIED',head,flush=True)
