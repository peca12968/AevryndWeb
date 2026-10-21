"""Exact complete sources, sampled contacts and local B2 working shape; normal LFS only."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0101-articulated-eyelid-topology';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip(),'Protect existing staged production'
 allow=[];files=[];lfs=[];reused=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<800*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.npy','.gif'];digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=50*1024*1024:assert src.suffix.lower() in ['.blend','.npz'];lfs.append(row)
 audit=read(E/'female-next-r0101.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for n in ['aevrynd-female-next-r0101-authoring.json','aevrynd-female-next-r0101.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json','lfs-progress.log'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.npy','.png','.gif','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0101-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0101*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(E/'minimum-saved-readback.json')['b2']['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 before=read(E/'before.json');refs=[(Path(before['source']['source']),M/Path(before['source']['source']).name)]
 for name in ['aevrynd-female-next-r0097-neutral-scalp-control-reference.blend']:
  src=S/name;dst=M/name
  if dst.exists():refs.append((src,dst))
  else:archive(src,dst)
 for name in ['a-actual-native-rim-selection.json','native-eye-topology.json','native-eye-topology.npz']:
  src=E.parent/'r0100-native-eyelid-assembly'/name;dst=M/('r0100-'+name);assert dst.exists();refs.append((src,dst))
 ref=read(E.parent/'r0098-whole-head-foundation/official-female-reference.json');refs.append((Path(ref['source']),M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend'))
 for name in ['build-female-next-r0098-native-head.py','render-female-next-r0091-matched.py','verify-female-next-r0099-saved-motion.py','verify-female-next-r0090-rain-and-flow.py']:
  refs.append((R/'scripts/character-next'/name,REPO/'scripts/character-next'/name))
 for src,dst in refs:assert sha(src)==sha(dst),str(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r101 complete orbital-lid history; no runtime promotion.','r0101-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0101* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0101-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0101*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_COMPLETE_ORBITAL_LID_CONSTRUCTIONS_AND_LOCAL_B2_REFERENCE','files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'shared15TexturesAndFullOriginalBundleReusedUnchanged':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks. All above50MiB complete sources use exact-path normal LFS, intact. Full verified immutable same-volume content may also back the LFS cache through hardlinks after the normal clean filter; cache/object/source bytes and index pointers must remain exact. No trimming, hook bypass, incomplete LFS or old-history migration.','scope':'Two art constructions with UV/attachment/compaction repairs; B2 retained as local complete working woman. Half-blink triangle-surface failure prevents whole appearance, complete operation or contact adoption. No runtime promotion.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0101-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'retainedWorkingSource':audit['retainedArticulatedOrbitalWomanReference'],'adoptedCompleteOperationNaturalDynamicsContactsRuntimeOrWebsite':False,'rights':read(S/'aevrynd-female-next-r0101-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0101-history-bundle.json',bundle);allow.append((M/'r0101-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0101-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R101_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS blobs')
if __name__=='__main__':main()
