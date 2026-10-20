"""Exact immutable r99 construction history, not a replacement runtime."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0099-continuous-head-neck';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 staged=subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).splitlines()
 if staged:assert set(staged)<=set(read(E/'history-allowlist.json')['files']),'Protect unrelated staged production blobs'
 allow=[];files=[];lfs=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<512*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.npy','.gif'];digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest,str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=50*1024*1024:assert src.suffix.lower() in ['.blend','.npz'];lfs.append(row)
 audit=read(E/'female-next-r0099.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for n in ['aevrynd-female-next-r0099-authoring.json','aevrynd-female-next-r0099.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.npy','.png','.gif','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0099-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0099*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 textures=read(E/'minimum-saved-readback.json')['c']['externalTextures']
 for row in textures:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 refs=[(S/'aevrynd-female-next-r0098-b-native-artist-head.blend',M/'aevrynd-female-next-r0098-b-native-artist-head.blend')]
 old=E.parent/'r0098-whole-head-foundation'
 for n in ['b-native-head-lineage.npz','official-female-reference.json','a-head-envelope-plan.json']:refs.append((old/n,M/('r0098-'+n)))
 ref=read(old/'official-female-reference.json');refs.append((Path(ref['source']),M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend'))
 for view in ['face','profile','body-face']:
  for folder,tag in [('r0097-scalp-ear-authored-controls','neutral-bound-reference'),('r0098-whole-head-foundation','b-native-head')]:
   src=E.parent/folder/('matched-'+tag+'-'+view+'.png');prefix='r0097-' if folder.startswith('r0097') else 'r0098-';refs.append((src,M/(prefix+src.name)))
 for src,dst in refs:assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r99 complete construction/source history; no trimming or old LFS migration.','r0099-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0099* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0099-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0099*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_COMPLETE_CONSTRUCTIONS_AND_SEPARATE_FAILED_FIXTURE','files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'shared15TexturesAndFullOriginalBundleReusedUnchanged':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks; every new above50MiB model/numeric blob uses exact-path normal Git LFS. Four complete .blend files retained, including the failed white-material fixture. No trimming, hook bypass, incomplete LFS or old history migration.','scope':'Three art constructions, one material repair of A, actual short affected controls and retained continuous artist-body reference. No complete-character, natural-physics, finite-contact or runtime acceptance.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0099-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'retainedLocalNeckContinuityOnly':True,'adoptedCompleteOperationNaturalDynamicsContactsRuntimeOrWebsite':False,'rights':read(S/'aevrynd-female-next-r0099-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0099-history-bundle.json',bundle);allow.append((M/'r0099-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0099-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R99_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS blobs')
if __name__=='__main__':main()
