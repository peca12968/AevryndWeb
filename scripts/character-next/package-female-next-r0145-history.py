"""Preserve both r145 full states, original failures and native morph/topology evidence."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0145-aspherical-lid-wall';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0144-current-skin-blink'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode('utf-8'))
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only'])
 allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.glb','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable and src.stat().st_dev==dst.parent.stat().st_dev:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel)
  files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst))
  reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0145.visual-audit.json')
 assert audit['appearanceImprovement'] is False
 assert len(audit['prototypeSources'])==2
 sources=[Path(x['source']) for x in audit['prototypeSources'].values()];assert sum(p.stat().st_size for p in sources)==306930952
 for p in sources:archive(p,M/'r0145-source'/p.name)
 for name in ['aevrynd-female-next-r0145-authoring.json','aevrynd-female-next-r0145.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0145-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0145*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 old=read(PRE/'history-copy-integrity.json')
 reuse(R/'scripts/character-next/build-female-next-r0144-current-skin-blink.py',G/'scripts/character-next/build-female-next-r0144-current-skin-blink.py','Exact original actual angular closure builder/helper; not rerun.')
 originalSource=S/'r0144-source/aevrynd-female-next-r0144-a-current-skin-blink.blend';reuse(originalSource,M/'r0144-source'/originalSource.name,'Immutable r144 complete source used as original r145 authoring basis; original known failure retained, not adopted.')
 reuse(PRE/'current-skin-blink-construction.json',M/'r0144-evidence/current-skin-blink-construction.json','Original source margin/optical centres/axes/attachment construction data; no old failure claimed repaired.')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact existing source/rights/topology/chart/helper/texture or rollback input; no duplicate.')
 for name in ['build-female-next-r0139-native-lid-follow.py','build-female-next-r0140-native-rooted-groom.py','author-female-next-r0140-native-guides.py','build-female-next-r0141-authored-parting.py']:
  reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Existing source-native current gaze/control helper, not rerun as a build.')
 reuse(E.parent/'r0140-native-clump-roots/native-open-clump-guides.npz',M/'r0140-evidence/native-open-clump-guides.npz','Only actual current scalp triangle IDs reused; no old failed r140 guide or shape adopted.')
 reuse(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz',M/'r0133-evidence/target-scalp-chart.npz','Actual native current-head scalp chart coordinates/UV/topology mapped exactly to current displayed Skin; no old native Add/foreign hair/UV contour construction adopted.')
 working=Path(audit['workingCompleteWomanReference']['source'])
 reuse(working,M/'r0139-source'/working.name,'Exact unique complete working r139 woman; r145 A/B both remain unaccepted; r139 working woman retained.')
 for t in read(E/'b-minimum-saved-aspherical-lid-wall-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../')
  reuse(Path(t['absolute']),M/rel[5:],'Exact original texture at unchanged relative sibling path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json']
 assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json')
 assert sha(E/'manifest-before.json')==rolling['sha256']
 assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',[
  'r0145-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
  'r0145-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol',
  'aevrynd-female-next-r0145* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
  'r0145-source/*.blend filter=lfs diff=lfs merge=lfs -text']),
  (G/'scripts/character-next/.gitattributes',['*female-next-r0145*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(p),'file':(M/'r0145-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'role':'complete unaccepted r145 source with actual native topology/control state'} for i,p in enumerate(sources)],
  'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0145'),
  'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','verifiedStorageRelocationRecord':'normal-git-objects-relocation.json','originalGitReadObjects':str(G/'.git/objects'),
  'allPriorR144StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,
  'scope':'One original r145 production round, two full saved states A failed native ray field/fallback and B actual native16-key-per-layer lamellar morph on failed subdivided cavity topology. All original attempts, first authoring clock, evidence and cost estimate overrun retained. No appearance or complete operation adopted. Original323 sources/nine unrelated files/v46/r139 working/development exact. Appearance no-adopt19/cadence2/next whole review after1 including both states and all failed attempts. No third full candidate, pruning, installs, server or subagents.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0145-evidence/history-copy-integrity.json')
 save(E/'history-allowlist.json',sorted(set(allow)))
 print('R145_EXACT_TWO_STATE_LID_FOUNDATION_HISTORY_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
