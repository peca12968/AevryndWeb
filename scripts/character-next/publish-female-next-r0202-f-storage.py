"""Finish existing r202 staged package using F-hosted cwd and normal Git/LFS."""
from pathlib import Path
import json,hashlib,os,subprocess,datetime,time
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);R=Path(p['directProjectAccess']);E=A/'evidence/character-female-next/r0202-independent-complete-groom';start=time.time();base='83c6a2909fb07e7bf5b2ec74ac2ae53b765469e0'
def read(f):return json.loads(Path(f).read_text('utf-8'))
def save(f,d):Path(f).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
env=os.environ.copy()
for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GOMAXPROCS='4')
def git(*args):
 r=subprocess.run(['git','-c','core.autocrlf=false','-c','pack.threads=4','-c','pack.windowMemory=32m','-c','lfs.concurrenttransfers=2',*args],cwd=str(A),env=env,capture_output=True)
 if r.returncode:raise RuntimeError(json.dumps({'args':args,'exit':r.returncode,'stdout':r.stdout.decode('utf-8','replace')[-5000:],'stderr':r.stderr.decode('utf-8','replace')[-5000:]}))
 return r.stdout
assert git('rev-parse','HEAD').decode().strip()==base
assert git('remote','get-url','github').decode().strip()=='https://github.com/peca12968/AevryndWeb.git'
assert git('branch','--show-current').decode().strip()=='main'
allow=read(E/'history-allowlist.json');staged=set(git('diff','--cached','--name-only').decode().splitlines());assert staged==set(allow)
integ=read(E/'history-copy-integrity.json')
for f in integ['files']:assert sha(A/f['file'])==f['sha256'],f['file']
# CRLF is preserved in original execution archives; normalize only new Python
# source line endings for standard repository whitespace checks.
normalized=[]
for f in sorted((A/'scripts/character-next').glob('*r0202*.py')):
 raw=f.read_bytes();out=raw.replace(b'\r\n',b'\n')
 if out!=raw:
  oldhash=hashlib.sha256(raw).hexdigest();f.write_bytes(out);normalized.append({'file':f.relative_to(A).as_posix(),'executedOriginalSHA256':oldhash,'normalizedLFSourceSHA256':sha(f),'onlyCRLFToLF':True})
save(E/'source-line-ending-normalization.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only new202 Python source CRLF to LF; original failed executable text archives and production geometry unchanged.','files':normalized})
(E/'package-third-terminal.txt').write_text(Path('F:/AevryndEvidence/CharacterTemp/r202-package-resume-final.log').read_text('utf-8'),encoding='utf-8')
extra=[E/'source-line-ending-normalization.json',E/'package-third-terminal.txt',Path(__file__)]
allow=sorted(set(allow+[f.relative_to(A).as_posix() for f in extra]));assert len(allow)==len(set(allow))
integ['files']=[{'file':rel,'sha256':sha(A/rel),'bytes':(A/rel).stat().st_size} for rel in allow if rel not in [(E/'history-copy-integrity.json').relative_to(A).as_posix(),(E/'history-allowlist.json').relative_to(A).as_posix()]]
integ['FStorageWritePolicy']='All project/archive writes through direct F-hosted NTFS GUID; temporary/review/log files literal F paths. Original C source/dependency paths read only.';integ['newlineNormalizationEvidence']=str(E/'source-line-ending-normalization.json');save(E/'history-copy-integrity.json',integ);save(E/'history-allowlist.json',allow)
git('add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
b=read(E/'diagnostic-build-summary.json');cache=Path(integ['normalFullLFS']['completeNormalObject']);assert sha(cache)==sha(b['output'])==b['sha256'] and cache.stat().st_size==b['bytes'] and os.path.samefile(cache,b['output']);assert sha(b['userReviewSource'])==b['sha256']
for rel in allow:
 actual=git('show',':'+rel)
 if rel.endswith('.blend'):assert actual==f'version https://git-lfs.github.com/spec/v1\noid sha256:{b["sha256"]}\nsize {b["bytes"]}\n'.encode()
 else:assert actual==(A/rel).read_bytes(),rel
git('diff','--cached','--check');caps=read(E/'before.json');evidence=sum(f.stat().st_size for f in E.iterdir() if f.is_file());assert evidence+15000<caps['evidenceBudgetBytes'] and b['bytes']<caps['sourceBudgetBytes'];remoteBefore=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remoteBefore==base
print('R202_EXACT_PACKAGE_READY',json.dumps({'files':len(allow),'sourceBytes':b['bytes'],'evidenceBytes':evidence,'fullLFS':True}),flush=True)
commitOut=git('commit','-m','character: preserve r202 rejected groom correspondence and F-storage diagnostic');head=git('rev-parse','HEAD').decode().strip();assert git('rev-parse','HEAD^').decode().strip()==base
print('R202_LOCAL_COMMIT',head,flush=True)
receipt={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalProductionParent':base,'localCommit':head,'branch':'character-history-v249','remote':'https://github.com/peca12968/AevryndWeb.git','normalHooksAndLFSUsed':True,'files':len(allow),'normalFullLFSObject':integ['normalFullLFS'],'remoteBefore':remoteBefore,'pushed':False}
save(E/'github-receipt.json',receipt)
try:
 out=git('push','github','HEAD:refs/heads/character-history-v249');remote=git('ls-remote','github','refs/heads/character-history-v249').decode().split()[0];assert remote==head;receipt.update(pushed=True,remoteCommit=remote,verifiedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),normalPushOutput=out.decode('utf-8','replace')[-2000:])
except Exception as error:
 receipt.update(pushError=str(error));save(E/'github-receipt.json',receipt);raise
save(E/'github-receipt.json',receipt)
q=read(E/'independent-diagnostic-readback.json');save(E/'completion-resource-receipt.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBytes':b['bytes'],'evidenceBytes':evidence,'originalCapsRetained':caps,'sourceLFSComplete':True,'sameWorking139Unchanged':True,'newCompleteHairstyleCandidates':0,'newHairCurvesEmitted':0,'referenceEditRestoreOnly':q['evaluatedReferenceRestorationMaximumM'],'noAdopt':76,'cadence':2,'nextWholeAfter':1,'allGatesUnaccepted':True,'historyPublishElapsedSeconds':time.time()-start,'normalPushRemoteSHA':head,'literalFReviewSource':b['userReviewSource'],'goal':'active'})
assert not git('diff','--cached','--name-only') and not git('status','--short','--untracked-files=no')
print('R202_NORMAL_GITHUB_VERIFIED',head,flush=True)