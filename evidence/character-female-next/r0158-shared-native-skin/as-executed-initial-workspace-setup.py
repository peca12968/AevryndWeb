from pathlib import Path
import os,subprocess,json,hashlib,shutil,re,datetime
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');Mrel=Path('assets-source/aevrynd-character/female-next');env=os.environ.copy()
for key in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(key,None)
env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GOMAXPROCS='4')
def run(args,cwd=None,data=None):return subprocess.check_output(args,cwd=cwd,env=env,input=data,stderr=subprocess.STDOUT)
def git(*a,cwd=G,data=None):return run(['git',*a],cwd,data)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
assert not C.exists();assert git('rev-parse','HEAD').decode().strip()=='4886210bae6a68da38da32e5e6348464adca6529';assert not git('diff','--cached','--name-only').strip()
q=json.loads((R/'Evidence/character-female-next/r0157-outer-lid-retopology/independent-source-archive-readback.json').read_text());deps=q['relativeLibrariesWithinArchive']+q['relativeTexturesWithinArchive'];total=sum(Path(x['file']).stat().st_size for x in deps);assert total==87409094;assert shutil.disk_usage('C:/').free>2*total+160000000
print(git('clone','--shared','--no-checkout',str(G),str(C)).decode(),flush=True)
git('remote','rename','origin','source_local',cwd=C);git('remote','add','github','https://github.com/peca12968/AevryndWeb.git',cwd=C)
for key in ['user.name','user.email']:
 val=git('config','--get',key).decode().strip();git('config',key,val,cwd=C)
helpers=git('config','--get-all','credential.https://github.com.helper').decode().splitlines()
for val in helpers:git('config','--add','credential.https://github.com.helper',val,cwd=C)
for key,val in [('credential.interactive','never'),('gc.auto','0'),('maintenance.auto','false'),('remote.pushDefault','github'),('branch.main.remote','github'),('branch.main.merge','refs/heads/character-history-v249'),('lfs.storage',str(C/'.git/lfs'))]:git('config',key,val,cwd=C)
for key in ['filter.lfs.process','filter.lfs.clean','filter.lfs.smudge','filter.lfs.required']:
 val=git('config','--get',key).decode().strip();git('config',key,val,cwd=C)
hook=G/'.git/hooks/pre-push';shutil.copyfile(hook,C/'.git/hooks/pre-push');assert sha(hook)==sha(C/'.git/hooks/pre-push')
paths=[];records=[];lfsBytes=0
for x in deps:
 src=Path(x['file']);rel=src.relative_to(G).as_posix();assert sha(src)==x['sha256'];paths.append(rel);size=int(git('cat-file','-s','HEAD:'+rel).decode().strip());isLFS=False
 if size<300:
  blob=git('show','HEAD:'+rel);match=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n',blob)
  if match:
   assert match[1].decode()==x['sha256'] and int(match[2])==src.stat().st_size;cache=C/'.git/lfs/objects'/x['sha256'][:2]/x['sha256'][2:4]/x['sha256'];cache.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,cache);assert sha(cache)==x['sha256'];lfsBytes+=src.stat().st_size;isLFS=True
 records.append({'original':str(src),'file':rel,'sha256':x['sha256'],'bytes':src.stat().st_size,'normalLFS':isLFS})
patterns=['/.gitattributes','/AGENTS.md','/docs/character-continuous-goal.md','/'+(Mrel/'female-next.asset.json').as_posix(),'/'+(Mrel/'r0158-source/**').as_posix(),'/'+(Mrel/'aevrynd-female-next-r0158-authoring.json').as_posix(),'/'+(Mrel/'LICENSE-female-next-r0158.txt').as_posix(),'/evidence/character-female-next/r0158-shared-native-skin/**','/scripts/character-next/*r0158*']+['/'+p for p in paths]
git('sparse-checkout','set','--no-cone','--stdin',cwd=C,data=('\n'.join(patterns)+'\n').encode())
for x in records:assert sha(C/x['file'])==x['sha256']
git('fetch','--no-tags','github','refs/heads/character-history-v249:refs/remotes/github/character-history-v249',cwd=C);assert git('rev-parse','HEAD',cwd=C).decode().strip()==git('rev-parse','refs/remotes/github/character-history-v249',cwd=C).decode().strip()
E=C/'evidence/character-female-next/r0158-shared-native-skin';E.mkdir(parents=True);S=C/Mrel/'r0158-source';S.mkdir(parents=True);(C/'scripts/character-next').mkdir(parents=True,exist_ok=True)
save(E/'before.json',{'startedUTC':'2026-10-22T09:51:48+00:00','supportDeadlineUTC':'2026-10-22T10:01:48+00:00','firstCompletePreviewDeadlineUTC':'2026-10-22T10:21:48+00:00','resourceCheckpointUTC':'2026-10-22T10:36:48+00:00','baseCommit':'4886210bae6a68da38da32e5e6348464adca6529','oneCandidate':True,'maxThreads':4,'sourceBudgetBytes':50000000,'evidenceBudgetBytes':12000000,'majorDefect':'536 duplicated eyelid boundaries and ignored ordinary Mesh editing block true continuous editable Skin; retain157 outer-lid appearance.','changedPremise':'Explicit known-boundary shared vertex indices in a single native Skin Mesh and actual input-position edit delta, not distance welding or hidden proxy editing.','previousGoalTurnClassification':'Progress:157 genuine outer-lid topology yields promising closed skin form; independent readback proves536 unwelded pairs, raw edit gap and19 retained Reflect contacts. One complete source and exact normal GitHub/LFS/default index history saved; no adoption. No-adopt31,cadence2,next whole156157158 due.'})
shutil.copyfile(R/'engine/assets/characters/female-next/female-next.asset.json',E/'manifest-before.json');save(E/'workspace-storage-provenance.json',{'createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceRepository':str(G),'activeArchiveCheckout':str(C),'sameBaseCommitAndGitHubBranch':True,'remote':'https://github.com/peca12968/AevryndWeb.git','remoteBranch':'character-history-v249','cloneMethod':'normal git clone --shared --no-checkout; immutable older Git objects read through original repository alternates, new objects/index/LFS/checkouts written on C','sparseCheckoutPatterns':patterns,'normalPrePushHookSha256':sha(hook),'dependencyFiles':records,'dependencyBytes':total,'fullNormalLFSCacheBytesCopied':lfsBytes,'existingSourceHistoryMovedDeletedOrRewritten':False,'oldDRepositoryHeadUnchanged':git('rev-parse','HEAD').decode().strip(),'currentFreeBytes':{d:shutil.disk_usage(d+':/').free for d in ['C','D']},'plannedSourceBudgetBytes':50000000,'plannedEvidenceBudgetBytes':12000000,'newCloneSharesOlderObjectsButDoesNotModifyOrPruneThem':True,'engineSourceAliasPlanned':str(R/'engine/assets/characters/female-next/source/r0158-source'),'actualNativeSourceDirectory':str(S)})
save(R/'Info/CharacterActiveArchiveWorkspace.json',{'activeArchiveCheckout':str(C),'originalDArchiveRetained':str(G),'sameRemote':'https://github.com/peca12968/AevryndWeb.git','branch':'character-history-v249','sinceRevision':'female-next-r0158','provenance':str(E/'workspace-storage-provenance.json'),'originalHistoryNotMovedOrDeleted':True})
print(json.dumps({'archive':str(C),'evidence':str(E),'source':str(S),'dependencyBytes':total,'Cfree':shutil.disk_usage('C:/').free,'normalHooksAndSharedOlderHistoryVerified':True}),flush=True)
