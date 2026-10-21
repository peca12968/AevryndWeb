"""Exact one complete rejected volume source; reuse existing original assets."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0133-anatomical-scalp-chart';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0132-anatomical-volume-groom'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']);allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable and src.stat().st_dev==dst.parent.stat().st_dev:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst));reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0133.visual-audit.json');sources=[Path(r['source']) for r in audit['prototypeSources'].values()]
 assert len(sources)==2
 for p in sources:archive(p,M/'r0133-source'/p.name)
 for name in ['aevrynd-female-next-r0133-authoring.json','aevrynd-female-next-r0133.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0133-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0133*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact existing original source/rights, native paths/topology, helper, baseline, texture or rollback input.')

 for name in ['build-female-next-r0132-anatomical-volume-groom.py','build-female-next-r0130-native-emitter-field.py']:reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Exact existing generic live-path/current-skin binding helper only; no failed old shape or source imported.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable)
 for t in read(E/'minimum-saved-chart-groom-readback.json')['sources']['a']['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture under unchanged source-relative sibling layout.')
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['r0133-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0133-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0133* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0133-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0133*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());unique={r['file']:r for r in reused};integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(p),'file':(M/'r0133-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0133','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR132StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One actual round, two complete native chart-rooted rest hair constructions. Both visibly rejected. Actual free-path/growth/current-skin edits recover and restore exactly; high local triangle-frame hair sensitivity remains. No appearance/complete operation/dynamics/contact/runtime adoption. All306 prior .blend metadata, nine unrelated files and v42 preserved; normal full source LFS, exact original dependencies reused, no history pruning/installation/server/subagents.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0133-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R133_EXACT_TWO_FULL_HAIR_SOURCES_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
