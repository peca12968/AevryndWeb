"""Exact one151 woman with all original native capability failures and dependencies."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0151-native-parent-groom';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0150-authored-rooted-locks'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']);allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.glb','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable and src.stat().st_dev==dst.parent.stat().st_dev:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst));reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0151.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==1;source=Path(audit['prototypeSources']['a']['source']);assert source.stat().st_size==137148362;archive(source,M/'r0151-source'/source.name)
 for n in ['aevrynd-female-next-r0151-authoring.json','aevrynd-female-next-r0151.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0151-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0151*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact inherited dependency/source/rights/texture/rollback already archived; no duplicate.')
 for name in ['actual-current-scalp.npz','authored-lock-construction-lineage.npz']:reuse(PRE/name,M/'r0150-evidence'/name,'Exact actual current Skin scalp and original33 rest-guide input; old child-owner recipe not reused.')
 for t in read(E/'minimum-independent-native-neighbour-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture, unchanged relative path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(r['source'])==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0151-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0151-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0151* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0151-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0151*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(source),'file':(M/'r0151-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':'One complete unaccepted native neighbouring-guide groom woman'}],'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0151'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR150StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'expectedCommitParent':'a998c602d6e1444959a6a84843d15c7f315bc4b9','scope':'One original151 round/137148362B full woman.3 native particle-key capability attempts produced no complete source and0 displayed parent/child movement; original metadata introspection error and false authoring label reconciled, not silently erased or credited. Actual native Interpolate Curves with33 live guides and26000 actual Skin roots produces1274000 evaluated points; base Hair raw points0. Independent actual guide edit affects2959 points, roots0/restoration0; local Skin root edit restores0. Complete5 views/A-B reject broad helmet/wig and profile eye occlusion. Original33 rest-form basis retired across150/151, native node retained as tool only. No appearance/complete operation/natural dynamics/contact/runtime adoption. Original330 sources/nine unrelated files/V48/working139/development exact. No-adopt25/cadence2/next1, next whole150/151/152 due. All previous rights/rollback preserved; no external asset/node library adopted. Original start/support/preview clocks and costs preserved. Low D free requires verified source/dependency reuse before another full clone; no deletions/history pruning.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0151-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R151_EXACT_ONE_COMPLETE_WOMAN_HISTORY_READY',len(set(allow)),source.stat().st_size,len(unique))
if __name__=='__main__':main()
