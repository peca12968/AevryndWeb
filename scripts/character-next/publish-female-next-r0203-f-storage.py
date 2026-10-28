"""Reject203 complete current-space Bezier form; preserve77 no-adopt and whole201202203 review."""
from pathlib import Path
import json,hashlib,datetime,os,subprocess,ctypes,struct,shutil
from ctypes import wintypes as w
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));R=Path(access['directProjectAccess']);C=Path(access['directCharacterArchiveAccess']);G=R/'sites-engine-journey';M=C/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=C/'evidence/character-female-next/r0203-current-space-bezier-groom';repo='//./'+str(C)[4:].replace('\\','/');F=Path('F:/AevryndStorage');hookPath=Path(access['temporaryWorkspace'])/'normal-git-hooks-f-access';publicationParent='cf07f73266339e5f86153a36d10356e7dbcd7495'
def read(f):return json.loads(Path(f).read_text('utf-8'))
def save(f,d):Path(f).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(f):
 p=Path(f);p=p if p.is_absolute() else R/p;return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
env=os.environ.copy()
for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_OPTIONAL_LOCKS='0',GOMAXPROCS='4')
def git(*args):
 r=subprocess.run(['git','--git-dir='+repo+'/.git','--work-tree='+repo,'-c','core.hooksPath='+str(hookPath),'-c','core.autocrlf=false','-c','pack.threads=4','-c','pack.windowMemory=32m','-c','lfs.concurrenttransfers=2',*args],cwd=str(F),env=env,capture_output=True)
 if r.returncode:raise RuntimeError(json.dumps({'args':args,'exit':r.returncode,'stdout':r.stdout.decode('utf-8','replace')[-2500:],'stderr':r.stderr.decode('utf-8','replace')[-2500:]}))
 return r.stdout

startTime=datetime.datetime.now(datetime.timezone.utc);t=read(E/'before.json');b=read(E/'a-build-summary.json');q=read(E/'independent-native-bezier-readback.json');audit=read(E/'continuation.json');integ=read(E/'history-copy-integrity.json');allow=read(E/'history-allowlist.json');assert git('rev-parse','HEAD').decode().strip()==publicationParent and set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
for row in integ['files']:assert sha(C/row['file'])==row['sha256'],row['file']
# Normalize only newly written203 authoring JSON, preserving content/old hash.
f=M/'aevrynd-female-next-r0203-authoring.json';raw=f.read_bytes();out=raw.replace(b'\r\n',b'\n');assert json.loads(raw)==json.loads(out)
for f in [M/'aevrynd-female-next-r0203-authoring.json',S/'aevrynd-female-next-r0203-authoring.json']:f.write_bytes(out)
save(E/'package-text-normalization.json',{'UTC':startTime.isoformat(),'file':'assets-source/aevrynd-character/female-next/aevrynd-female-next-r0203-authoring.json','originalCRLFSHA256':hashlib.sha256(raw).hexdigest(),'normalizedLFSHA256':hashlib.sha256(out).hexdigest(),'onlyLineEndingsChanged':True,'actualSourceGeometryEvidenceClocksAndCountersNotRewritten':True})
(E/'package-first-terminal.txt').write_bytes(Path('F:/AevryndEvidence/CharacterTemp/r203-finalize.log').read_bytes())
r202=read(E.parent/'r0202-independent-complete-groom/before.json');r202b=read(E.parent/'r0202-independent-complete-groom/diagnostic-build-summary.json');save(E/'previous-r202-resource-checkpoint.json',{'UTC':startTime.isoformat(),'originalStartedUTC':r202['startedUTC'],'originalCheckpointUTC':r202['resourceCheckpointUTC'],'originalSupportDeadlineUTC':r202['supportDeadlineUTC'],'originalPreviewDeadlineUTC':r202['firstCompletePreviewDeadlineUTC'],'original45MinuteCheckpointObservedLate':True,'notMeasuredAtDeadline':True,'actualSourceBytes':r202b['bytes'],'noNewCompleteGroomEmitted':True,'normalPushCompleteAndVerified':'cf07f73266339e5f86153a36d10356e7dbcd7495','shellContextFailureAndSameOriginalStagedBlobsRetained':True,'newClockOrBudgetNotCreated':True})
new=[E/'package-text-normalization.json',E/'package-first-terminal.txt',E/'previous-r202-resource-checkpoint.json',Path(__file__)];allow=sorted(set(allow+[f.relative_to(C).as_posix() for f in new]));integ['files']=[{'file':rel,'sha256':sha(C/rel),'bytes':(C/rel).stat().st_size} for rel in allow if rel not in [(E/'history-copy-integrity.json').relative_to(C).as_posix(),(E/'history-allowlist.json').relative_to(C).as_posix()]];save(E/'history-copy-integrity.json',integ);save(E/'history-allowlist.json',allow);git('add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
for rel in allow:
 data=git('show',':'+rel)
 if rel.endswith('.blend'):assert data==f'version https://git-lfs.github.com/spec/v1\noid sha256:{b["sha256"]}\nsize {b["bytes"]}\n'.encode()
 else:assert data==(C/rel).read_bytes(),rel
git('diff','--cached','--check');cache=Path(integ['normalFullLFS']['completeNormalObject']);assert sha(cache)==sha(b['output'])==b['sha256'] and os.path.samefile(cache,b['output']);assert sha(b['userReviewSource'])==b['sha256'];evidence=sum(f.stat().st_size for f in E.iterdir() if f.is_file());assert evidence+12000<t['evidenceBudgetBytes'] and b['bytes']<t['sourceBudgetBytes']
gitG='//./'+str(G)[4:].replace('\\','/');res=subprocess.run(['git','--git-dir='+gitG+'/.git','rev-parse','HEAD'],cwd=str(F),env=env,capture_output=True);assert res.returncode==0 and res.stdout.decode().strip()=='4886210bae6a68da38da32e5e6348464adca6529'
for original in (C/'.git/hooks').iterdir():
 if original.is_file():assert sha(original)==sha(hookPath/original.name)
remoteBefore=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remoteBefore==publicationParent;print('R203_EXACT_PACKAGE_VERIFIED',json.dumps({'stagedFiles':len(allow),'sourceBytes':b['bytes'],'evidenceBytes':evidence,'noAdopt':77,'cadence':0,'nextWholeAfter':3}),flush=True)
git('commit','-m','character: reject r203 Bezier shell form and review full woman');head=git('rev-parse','HEAD').decode().strip();assert git('rev-parse','HEAD^').decode().strip()==publicationParent;print('R203_LOCAL_COMMIT',head,flush=True)
receipt={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalProductionParent':t['originalProductionParent'],'commitParent':publicationParent,'localCommit':head,'remote':'https://github.com/peca12968/AevryndWeb.git','branch':'character-history-v249','fullNormalLFS':integ['normalFullLFS'],'normalOriginalByteIdenticalHooksUsed':True,'originalHookUnmodified':True,'normalHookAccessProof':str(E/'normal-hooks-f-access.json'),'pushed':False};save(E/'github-receipt.json',receipt)
try:
 push=git('push','github','HEAD:refs/heads/character-history-v249');remote=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remote==head;receipt.update(pushed=True,remoteCommit=remote,verifiedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),normalPushOutput=push.decode('utf-8','replace')[-2000:])
except Exception as error:receipt['error']=str(error);save(E/'github-receipt.json',receipt);raise
save(E/'github-receipt.json',receipt);assert not git('diff','--cached','--name-only') and not git('status','--short','--untracked-files=no')
save(E/'completion-resource-receipt.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartUTC':t['startedUTC'],'originalSupportDeadlineUTC':t['supportDeadlineUTC'],'originalPreviewDeadlineUTC':t['firstCompletePreviewDeadlineUTC'],'originalResourceCheckpointUTC':t['resourceCheckpointUTC'],'sourceBytes':b['bytes'],'evidenceBytes':evidence,'fullSaveLFSAndEstimatedPackBytes':b['bytes']+evidence+2000000,'originalSourceEvidencePackCapsPreserved':True,'actualPeakRAMAndNetworkPackBytesNotMeasured':True,'normalFullLFSObjectVerified':True,'normalRemoteCommit':head,'noAdopt':77,'cadence':0,'nextWholeAfter':3,'noCompleteAppearanceOrOperationGain':True,'actualNativeGuideEditRestorationM':q['actualEdit']['evaluatedCompleteRestoreM'],'goal':'active'})
print('R203_NORMAL_GITHUB_VERIFIED',head,flush=True)
