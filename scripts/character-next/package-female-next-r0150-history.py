"""Exact150 history; one full woman and a small original native lock component."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0150-authored-rooted-locks';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0149-native-scalp-sculpt'
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
 audit=read(E/'female-next-r0150.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==1;source=Path(audit['prototypeSources']['a']['source']);assert source.stat().st_size==178896809;archive(source,M/'r0150-source'/source.name)
 for n in ['aevrynd-female-next-r0150-authoring.json','aevrynd-female-next-r0150.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0150-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0150*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact inherited dependency/source/rights/texture/rollback already archived; no duplicate.')
 for n in ['build-female-next-r0138-native-current-gaze.py','build-female-next-r0149-native-physical-groom.py']:reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Existing actual native point/root-frame and matched-render helpers only, not a rerun of rejected physical style.')
 for t in read(E/'minimum-independent-authored-locks-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture, unchanged relative path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(r['source'])==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0150-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0150-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0150* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0150-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0150*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused};component=E/'first-rooted-lock-component.blend';assert component.stat().st_size==138709
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(source),'file':(M/'r0150-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':'One complete unaccepted authored rooted-lock woman'}],'smallNativeLockComponent':{'source':str(component),'file':(M/'r0150-evidence'/component.name).relative_to(G).as_posix(),'sha256':sha(component),'bytes':component.stat().st_size,'ordinaryCompleteGitBinaryNotLFSRequired':True,'notASecondCompleteWoman':True},'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0150'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR149StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'productionOriginalBaseCommit':read(E/'before.json')['baseCommit'],'expectedCommitParent':'e3cb968dfe0e7a9808ce6367e9a080807a78cdd1','scope':'One original150 round,178896809B complete woman plus138709B9-point component. Direct actual root-first authoring within2m32.700733, complete5 views well before original30min deadline.33 explicit independently authored3D rest strokes and26000 native strands with live native guide editing. Matched complete head/body/profile/back/oblique rejects flat separated sheets/spiky ends; no appearance or complete usable operation adoption. Independent actual guide edit1mm affects1385 displayed points, roots0, restore0; actual strand and local Skin-root-frame restore0. No natural hair dynamics/finite+self+continuous/runtime acceptance, no broad audits/variants after visible failure. No new third-party assets adopted/distributed. Original329 sources/nine unrelated files/V48/working139/development protected. No-adopt24/cadence1/next2, last whole147/148/149 unchanged. Native first lock library not extra woman/round. Stop hard single-guide child construction; change actual neighbouring child/guide volume before another full candidate.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0150-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R150_EXACT_ONE_WOMAN_AND_SMALL_NATIVE_LOCK_HISTORY_READY',len(set(allow)),source.stat().st_size,len(unique))
if __name__=='__main__':main()
