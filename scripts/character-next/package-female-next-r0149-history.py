"""Exact149 history, immutable full source and reused existing dependencies."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0149-native-scalp-sculpt';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0148-native-groom-foundation'
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
 audit=read(E/'female-next-r0149.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==1;source=Path(audit['prototypeSources']['a']['source']);assert source.stat().st_size==157978870;archive(source,M/'r0149-source'/source.name)
 for n in ['aevrynd-female-next-r0149-authoring.json','aevrynd-female-next-r0149.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:
   assert 'native-process-temp' not in p.parts,'Do not archive generated recovery cache';archive(p,M/'r0149-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0149*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact inherited dependency/source/rights/texture/rollback already archived; no duplicate.')
 reuse(R/'scripts/character-next/build-female-next-r0138-native-current-gaze.py',G/'scripts/character-next/build-female-next-r0138-native-current-gaze.py','Exact working woman and matched-render helper, not a build rerun.')
 reuse(E.parent/'r0140-native-clump-roots/native-open-clump-guides.npz',M/'r0140-evidence/native-open-clump-guides.npz','Exact previously recorded current Skin scalp-face indices only, not rejected guide hair paths.')
 for t in read(E/'minimum-independent-native-physical-groom-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture, unchanged relative path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(r['source'])==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0149-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0149-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0149* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0149-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0149*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(source),'file':(M/'r0149-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':'One complete unaccepted native physical groom woman'}],'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0149'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR148StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'productionOriginalBaseCommit':read(E/'before.json')['baseCommit'],'expectedCommitParentAfterSeparatePromptMaintenance':'049d241a5abd609f9a6d478187b934b3eeacec04','scope':'ONE original149 round and157978870B complete woman. Empty native probes and native sphere fixture are not additional candidates or character authoring success. Original23m39.143352 support elapsed/13m39.143352 support overrun preserved, five views before original deadline but entire hair framing unaccepted. Actual current root-first physical authoring rejected for giant radial halo. Independent actual displayed point/root-frame edit and restore0 are component only, not natural dynamics. No second light/broad contact/runtime after visible failure. No new third-party assets adopted/distributed. Original328 sources/nine unrelated files/working139/development and separateV48 prompts protected. Whole147/148/149 actually reviewed, no-adopt23/cadence0/next3. Original failed code/errors/recovery cleanup SHA and transient evidence budget overrun retained. No tolerance/material/count/radius/stiffness rescue, no history pruning or formal promotion.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0149-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R149_EXACT_ONE_COMPLETE_WOMAN_HISTORY_READY',len(set(allow)),source.stat().st_size,len(unique))
if __name__=='__main__':main()
