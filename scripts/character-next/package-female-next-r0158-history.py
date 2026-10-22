"""Exact normal C archive/LFS; retain D history and source aliases."""
from pathlib import Path
import json,hashlib,subprocess,os,shutil
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0158-shared-native-skin';M=C/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source'
env=os.environ.copy()
for k in ('GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES'):env.pop(k,None)
env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GOMAXPROCS='4')
def git(*a):return subprocess.check_output(['git','-C',str(C),*a],env=env)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (E/'history-copy-integrity.json').exists();assert git('diff','--cached','--name-only')==b''
base=git('rev-parse','HEAD').decode().strip();assert base=='178d3210e8674b3b094913b83b50ecf93ee058b6'
assert git('remote','get-url','github').decode().strip()=='https://github.com/peca12968/AevryndWeb.git'
assert sha(C/'.git/hooks/pre-push')==sha(G/'.git/hooks/pre-push')=='a52d0510d0f8c75e27852156ec6f7791f0d8ed65fc58fcc368dd1de0a60a1d74'
old=read(R/'Evidence/character-female-next/r0152-layered-groom/before.json')
rows=sorted([p.relative_to(S).as_posix(),p.stat().st_size,p.stat().st_mtime_ns] for p in S.rglob('*.blend') if not any(f'r{i:04d}-source' in p.parts for i in range(152,159)))
assert len(rows)==old['sourceBlendCount']==331 and hashlib.sha256(json.dumps(rows).encode()).hexdigest()==old['sourceInventoryMetadataDigest']
for p,v in old['protectedUnrelatedHashes'].items():assert sha(p)==v,p
provenance=read(E/'workspace-storage-provenance.json');deps=[]
for row in provenance['dependencyFiles']:
 p=C/row['file'];assert sha(p)==sha(row['source'])==row['sha256'] and p.stat().st_size==row['bytes'];deps.append(row)
reused=[]
for p in [R/'scripts/character-next/build-female-next-r0157-outer-lid-retopology.py',R/'scripts/character-next/contact-female-next-r0138-ocular-surfaces.py',R/'scripts/character-next/build-female-next-r0138-native-sockets.py',S/'aevrynd-female-next-r0126.LICENSE-SOURCE.txt',S/'aevrynd-female-next-r0126-authoring.json']:
 rel=('scripts/character-next/'+p.name) if p.suffix=='.py' else ('assets-source/aevrynd-character/female-next/'+p.name);arch=G/rel;assert sha(p)==sha(arch);reused.append({'source':str(p),'archiveFile':rel,'sha256':sha(p)})
for p,expected in [(S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend','5128a461a011899c77b275055ea3a8a94ca278873665dd08f72a6003d4a37bb9'),(S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend','09da2122d16f80cbcff6f535dbfc35540df27131dc323450d2a4c41293446db9')]:assert sha(p)==expected
v51=read(R/'Info/CharacterGoalPrompt-v51-update.json')
for p,v in v51['protectedProductionContentBefore'].items():
 if Path(p)==S.parent/'female-next.asset.json':continue
 assert sha(p)==v['sha256'] and Path(p).stat().st_size==v['bytes'],p
attrs=C/'.gitattributes';raw=attrs.read_bytes().replace(b'\r\n',b'\n');assert b'/r0158-source/' not in raw
attrs.write_bytes(raw+b'assets-source/aevrynd-character/female-next/r0158-source/*.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0158-shared-native-skin/** -filter -diff -merge -text\n')
files=[attrs,M/'female-next.asset.json',M/'aevrynd-female-next-r0158-authoring.json',M/'LICENSE-female-next-r0158.txt']+sorted((M/'r0158-source').glob('*.blend'))+sorted((C/'scripts/character-next').glob('*r0158*.py'))+[p for p in sorted(E.iterdir()) if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']]
assert sha(M/'female-next.asset.json')==sha(S.parent/'female-next.asset.json');lfs=[]
for p in (M/'r0158-source').glob('*.blend'):
 key=sha(p);cache=C/'.git/lfs/objects'/key[:2]/key[2:4]/key;cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():os.link(p,cache)
 assert sha(cache)==key;lfs.append({'file':p.relative_to(C).as_posix(),'sha256':key,'bytes':p.stat().st_size,'completeNormalLFSObject':str(cache),'immutableSameFile':os.path.samefile(p,cache)})
assert sum(x['bytes'] for x in lfs)==35826571
records=[{'file':p.relative_to(C).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
integrity={'expectedCommitParent':base,'activeArchiveCheckout':str(C),'originalDArchiveHead':subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],env=env).decode().strip(),'newFiles':records,'normalFullLFSSources':lfs,'reusedDependencies':deps,'additionalVerifiedSourceAndRightsReferences':reused,'inheritedInputIntegrity':{'source':str(R/'Evidence/character-female-next/r0157-outer-lid-retopology/history-copy-integrity.json'),'sha256':sha(R/'Evidence/character-female-next/r0157-outer-lid-retopology/history-copy-integrity.json'),'interpretation':'Prior immutable source/input references remain in original D archive/object store; mutable old manifest snapshots are historical, not current.'},'old331SourceMetadataAndNineUnrelatedHashesUnchanged':True,'v51ProtectedPendingInputsExceptIntentionallyUpdatedManifestUnchanged':True,'working139AndExternal117HashesUnchanged':True,'noHistoryMovedDeletedPruned':True,'normalPrePushHookPreserved':True,'ordinaryFilesMustMatchRawSourceBytes':True,'noIncompleteLFSOrHookBypass':True}
save(E/'history-copy-integrity.json',integrity);files.append(E/'history-copy-integrity.json');files.append(E/'history-allowlist.json');allow=sorted(p.relative_to(C).as_posix() for p in files);save(E/'history-allowlist.json',allow);assert len(set(allow))==len(allow)
git('-c','core.autocrlf=false','add','--sparse','--',*allow);assert set(git('diff','--cached','--name-only').decode().splitlines())==set(allow)
sourceRecords={x['file']:x for x in lfs}
for rel in allow:
 blob=git('show',':'+rel);p=C/rel
 if rel in sourceRecords:
  x=sourceRecords[rel];expected=f'version https://git-lfs.github.com/spec/v1\noid sha256:{x["sha256"]}\nsize {x["bytes"]}\n'.encode();assert blob==expected
 else:assert blob==p.read_bytes(),rel
git('diff','--cached','--check');assert sum(p.stat().st_size for p in E.iterdir() if p.is_file())<12000000
print(json.dumps({'stagedExactFiles':len(allow),'fullLFSBytes':sum(x['bytes'] for x in lfs),'evidenceBytes':sum(p.stat().st_size for p in E.iterdir() if p.is_file()),'reusedDependencyBytes':sum(x['bytes'] for x in deps),'allRawSourceAndIndexBytesMatch':True,'freeC':shutil.disk_usage('C:/').free,'freeD':shutil.disk_usage('D:/').free}),flush=True)
