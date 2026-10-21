"""Four complete native-head sources with exact failures and normal LFS."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip(),'Protect staged production'
 allow=[];files=[];lfs=[];reused=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<900*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.npy','.gif'];digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=50*1024*1024:assert src.suffix.lower() in ['.blend','.npz'];lfs.append(row)
 audit=read(E/'female-next-r0104.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for name in ['aevrynd-female-next-r0104-authoring.json','aevrynd-female-next-r0104.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.suffix in ['.json','.npz','.npy','.png','.gif','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0104-'+p.relative_to(E).as_posix().replace('/','-')))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0104*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(E/'minimum-saved-readback.json')['b2']['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256'];reused.append({'file':(M/rel).relative_to(REPO).as_posix(),'sha256':row['sha256']})
 refs=[(Path(read(E/'before.json')['source']['source']),M/Path(read(E/'before.json')['source']['source']).name)]
 for folder,prefix,names in [('r0100-native-eyelid-assembly','r0100-',['native-eye-topology.json']),('r0102-facet-aware-lid-surface','r0102-',['a-retained-lash-bindings.json','a-view-controls.json','matched-a-facet-lining-face.png','matched-a-facet-lining-body-face.png','matched-a-facet-lining-profile.png']),('r0103-anatomical-front-lid-bands','r0103-',['continuation.json','matched-a-anatomical-bands-face.png','matched-a-anatomical-bands-body-face.png'])]:
  for name in names:refs.append((E.parent/folder/name,M/(prefix+name)))
 for name in ['build-female-next-r0098-native-head.py','build-female-next-r0102-facet-lining.py','render-female-next-r0091-matched.py','verify-female-next-r0101-saved-lids.py','verify-female-next-r0099-saved-motion.py','make-female-next-r0101-boards.py']:refs.append((R/'scripts/character-next'/name,REPO/'scripts/character-next'/name))
 ref=read(E.parent/'r0098-whole-head-foundation/official-female-reference.json');refs.append((Path(ref['source']),M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend'))
 for src,dst in refs:assert sha(src)==sha(dst),str(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r104 native-head sources, diagnostics and scoped failures.','r0104-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0104* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0104-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0104*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_COMPLETE_NATIVE_HEAD_ART_SOURCES_WITH_ALL_HARD_FAILURES','files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'allSourceArchiveBytesEqual':True,'immutableSourcesHardlinkedMutableRecordsCopied':True,'fullPerSourceBudgetBytes':900*1024*1024,'normalFullLFSRequired':True,'cacheReusePolicy':'Normal clean filter first, then verify full source/archive/cache SHA and size; immutable identical source may back the full cache via a hardlink. Normal pre-push and complete uploads required. No partial/truncated object, history migration or hook bypass.','scope':'Two art constructions; B2/B3 are data repairs, all4 full sources retained. B2 only local complete static native-head art direction; mouth shading, new skin deformation and neutral optical intersections remain unaccepted. No whole appearance/operation/runtime/site/female acceptance.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0104-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'retainedWorkingSource':audit['workingCompleteWomanReference'],'adoptedCompleteOperationNaturalDynamicsContactsRuntimeOrWebsite':False,'rights':read(S/'aevrynd-female-next-r0104-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0104-history-bundle.json',bundle);allow.append((M/'r0104-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0104-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R104_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'full LFS blobs')
if __name__=='__main__':main()
