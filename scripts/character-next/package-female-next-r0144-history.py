"""Preserve one actual current-skin blink candidate and all original attempt evidence."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0144-current-skin-blink';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0143-authored-section-volumes'
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
 audit=read(E/'female-next-r0144.visual-audit.json')
 assert audit['appearanceImprovement'] is False
 assert len(audit['prototypeSources'])==1
 sources=[Path(audit['prototypeSources']['a']['source'])]
 for p in sources:archive(p,M/'r0144-source'/p.name)
 for name in ['aevrynd-female-next-r0144-authoring.json','aevrynd-female-next-r0144.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0144-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0144*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact existing source/rights/topology/chart/helper/texture or rollback input; no duplicate.')
 for name in ['build-female-next-r0139-native-lid-follow.py','build-female-next-r0140-native-rooted-groom.py','author-female-next-r0140-native-guides.py','build-female-next-r0141-authored-parting.py']:
  reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Existing source-native current gaze/control helper, not rerun as a build.')
 reuse(E.parent/'r0140-native-clump-roots/native-open-clump-guides.npz',M/'r0140-evidence/native-open-clump-guides.npz','Only actual current scalp triangle IDs reused; no old failed r140 guide or shape adopted.')
 reuse(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz',M/'r0133-evidence/target-scalp-chart.npz','Actual native current-head scalp chart coordinates/UV/topology mapped exactly to current displayed Skin; no old native Add/foreign hair/UV contour construction adopted.')
 working=Path(audit['workingCompleteWomanReference']['source'])
 reuse(working,M/'r0139-source'/working.name,'Exact unique complete working r139 woman; r144 acceptance remains scoped by its actual continuation.')
 for t in read(E/'minimum-saved-current-skin-blink-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../')
  reuse(Path(t['absolute']),M/rel[5:],'Exact original texture at unchanged relative sibling path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json']
 assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json')
 assert sha(E/'manifest-before.json')==rolling['sha256']
 assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',[
  'r0144-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
  'r0144-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol',
  'aevrynd-female-next-r0144* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
  'r0144-source/*.blend filter=lfs diff=lfs merge=lfs -text']),
  (G/'scripts/character-next/.gitattributes',['*female-next-r0144*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(p),'file':(M/'r0144-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'role':'complete current-skin blink candidate with actual native geometry and controllers'} for i,p in enumerate(sources)],
  'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0144'),
  'newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),
  'allPriorR143StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,
  'scope':'One original r144 current displayed skin blink candidate. Keep all failed pre-save authoring/verifier attempts, original clocks and the prompt-only v46 interruption separately. See actual continuation for adoption and four-gate decision; no complete-character, hair, finite/self/continuous or runtime inflation. Protected old322 sources, nine unrelated files, v46 prompt and prior working/development source remain exact. No duplicate reference assets, pruning, install, server or subagent.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0144-evidence/history-copy-integrity.json')
 save(E/'history-allowlist.json',sorted(set(allow)))
 print('R144_EXACT_CURRENT_SKIN_BLINK_HISTORY_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
