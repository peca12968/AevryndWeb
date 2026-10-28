"""Reject203 complete current-space Bezier form; preserve77 no-adopt and whole201202203 review."""
from pathlib import Path
import json,hashlib,datetime,os,subprocess,ctypes,struct,shutil
from ctypes import wintypes as w
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));R=Path(access['directProjectAccess']);C=Path(access['directCharacterArchiveAccess']);G=R/'sites-engine-journey';M=C/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=C/'evidence/character-female-next/r0213-anatomical-section-cage';repo='//./'+str(C)[4:].replace('\\','/');F=Path('F:/AevryndStorage');hookPath=Path(access['temporaryWorkspace'])/'normal-git-hooks-f-access';publicationParent='bd79f112180c011c5e2dc7b5e977743ce7e1acb4'
def read(f):return json.loads(Path(f).read_text('utf-8'))
def save(f,d):Path(f).write_bytes((json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def sha(f):
 p=Path(f);p=p if p.is_absolute() else R/p;return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
env=os.environ.copy()
for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_OPTIONAL_LOCKS='0',GOMAXPROCS='4')
def git(*args):
 r=subprocess.run(['git','--git-dir='+repo+'/.git','--work-tree='+repo,'-c','core.hooksPath='+str(hookPath),'-c','core.autocrlf=false','-c','pack.threads=4','-c','pack.windowMemory=32m','-c','lfs.concurrenttransfers=2',*args],cwd=str(F),env=env,capture_output=True)
 if r.returncode:raise RuntimeError(json.dumps({'args':args,'exit':r.returncode,'stdout':r.stdout.decode('utf-8','replace')[-2500:],'stderr':r.stderr.decode('utf-8','replace')[-2500:]}))
 return r.stdout





t=read(E/'before.json');audit=read(E/'continuation.json');b=read(E/'build-summary.json');bb=read(E/'b-build-summary.json');working=audit['workingCompleteWomanReference'];b['frozenEditorSource']={'file':bb['output'],'sha256':bb['sha256'],'bytes':bb['bytes']};sources=[{'file':b['output'],'sha256':b['sha256'],'bytes':b['bytes']},b['frozenEditorSource']];sourceTotal=sum(r['bytes'] for r in sources);assert git('rev-parse','HEAD').decode().strip()==t['baseCommit']==publicationParent;assert not git('diff','--cached','--name-only');assert audit['confirmedConsecutiveRoundsWithoutAdoptedCompleteAppearanceGainLowerBound']==87;assert read(R/'engine/assets/characters/female-next/female-next.asset.json')['latestStudyRevision']=='female-next-r0213';assert not (E/'history-copy-integrity.json').exists();assert sourceTotal<t['sourceBudgetBytes'];assert sum(x.stat().st_size for x in E.iterdir() if x.is_file())<t['evidenceBudgetBytes']
# Reuse only unchanged historical/dependency integrity checks from191.
shared=C/'scripts/character-next/finalize-package-female-next-r0191.py';assert sha(shared)=='d78ca974e1fbea7d5c6caeeb1b05ad26099816ca1a1e5f22fae05a5d608214dc';guardText="old=read(R/'Evidence"+shared.read_text('utf-8').split("old=read(R/'Evidence",1)[1].split('for link,target in [',1)[0];guardText=guardText.replace('range(152,192)','range(152,214)');exec(guardText)


attrs=C/'.gitattributes';raw=attrs.read_bytes().replace(b'\r\n',b'\n');assert b'/r0213-source/' not in raw;attrs.write_bytes(raw+b'assets-source/aevrynd-character/female-next/r0213-source/*.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0213-anatomical-section-cage/** -filter -diff -merge -text\n');lfs=[]
for row in sources:
 cache=C/'.git/lfs/objects'/row['sha256'][:2]/row['sha256'][2:4]/row['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():os.link(row['file'],cache)
 assert sha(cache)==row['sha256'] and os.path.samefile(cache,row['file']);lfs.append({'file':Path(row['file']).relative_to(C).as_posix(),'sha256':row['sha256'],'bytes':row['bytes'],'completeNormalObject':str(cache),'immutableSameFile':True})
files=[attrs,M/'female-next.asset.json',M/'aevrynd-female-next-r0213-authoring.json',M/'LICENSE-female-next-r0213.txt']+[Path(r['file']) for r in sources]+sorted((C/'scripts/character-next').glob('*r0213*.py'))+[f for f in sorted(E.iterdir()) if f.is_file() and f.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']];save(E/'history-copy-integrity.json',{'expectedCommitParent':t['baseCommit'],'originalProductionParent':t['baseCommit'],'files':[{'file':f.relative_to(C).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size} for f in files],'normalFullLFSObjects':lfs,'reusedDependencies':{'exactFullListSource':str(E.parent/'r0212-complete-artist-volume-foundation/history-copy-integrity.json'),'sourceSHA256':sha(E.parent/'r0212-complete-artist-volume-foundation/history-copy-integrity.json'),'dependencyCount':len(deps),'all17ActualFullInputsVerifiedUnchangedNow':True},'inheritedInputIntegrity':{'source':str(E.parent/'r0212-complete-artist-volume-foundation/history-copy-integrity.json'),'sha256':sha(E.parent/'r0212-complete-artist-volume-foundation/history-copy-integrity.json')},'old331NineUnrelatedWorking139Input212External117AndDependenciesVerified':True,'originalDHistoryObjectStoresRetained':str(G),'normalPrePushHookPreserved':True,'completeCandidateTrials':2,'fullSourceSaves':2,'actualRoundCount':1});files.extend([E/'history-copy-integrity.json',E/'history-allowlist.json']);allow=sorted(f.relative_to(C).as_posix() for f in files);assert len(allow)==len(set(allow));save(E/'history-allowlist.json',allow);git('add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow);byrel={r['file']:r for r in lfs}
for rel in allow:
 data=git('show',':'+rel)
 if rel in byrel:
  r=byrel[rel];assert data==f'version https://git-lfs.github.com/spec/v1\noid sha256:{r["sha256"]}\nsize {r["bytes"]}\n'.encode()
 else:assert data==(C/rel).read_bytes(),rel
git('diff','--cached','--check');evidence=sum(f.stat().st_size for f in E.iterdir() if f.is_file());assert evidence+5000<t['evidenceBudgetBytes'] and sourceTotal+evidence+2000000<t['estimatedPackBudgetBytes'];print('R213_EXACT_PACKAGE_STAGED',json.dumps({'stagedFiles':len(allow),'sourceBytes':sourceTotal,'evidenceBytes':evidence,'fullLFSObjects':2,'noAdopt':87,'cadence':1,'nextWholeAfter':2}),flush=True)
