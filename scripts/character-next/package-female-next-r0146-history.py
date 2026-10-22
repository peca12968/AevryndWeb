"""Exact one-source history with immutable media links and reused dependency closure."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0146-connected-palpebral-lining';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0145-aspherical-lid-wall'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
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
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst))
  reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0146.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==1
 source=Path(audit['prototypeSources']['a']['source']);assert source.stat().st_size==168081860
 archive(source,M/'r0146-source'/source.name)
 for name in ['aevrynd-female-next-r0146-authoring.json','aevrynd-female-next-r0146.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0146-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0146*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact inherited dependency/rights/texture/rollback; no duplicate.')
 for name in ['build-female-next-r0145-native-lamellar-morph.py','build-female-next-r0145-aspherical-lid-wall.py','build-female-next-r0131-native-hair-material.py']:reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Actual radial-surface/native helper or material signature dependency; main not executed.')
 for t in read(E/'minimum-independent-connected-lining-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Original texture, same unchanged relative sibling path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json']
 assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0146-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0146-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0146* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0146-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0146*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(source),'file':(M/'r0146-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':'One complete unaccepted connected-lining candidate, native controls and full original dependency closure'}],'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0146'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR145StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One original r146 round, one complete168081860B unaccepted candidate, two pre-save full-builder failures, actual explicit patch/native morph17-pose controls/restore verification and sampled coverage diagnosis. Visible closed lid unconvincing, no appearance or complete usable operation adopted. r139 working/development unchanged. Whole review144/145/146 complete, appearance no-adopt20/cadence0/next3. Original clocks/budgets preserved including separate user-authorized v47 prompt maintenance. Old325 source metadata/nine unrelated files preserved. No new variants, broad contact/second light/export after visible failure.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0146-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)))
 print('R146_EXACT_ONE_SOURCE_HISTORY_READY',len(set(allow)),source.stat().st_size,len(unique))
if __name__=='__main__':main()
