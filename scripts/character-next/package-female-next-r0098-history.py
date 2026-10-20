"""Exact immutable head-source history including the full original reference.
B's202MB saved source is preserved intact through normal exact-path Git LFS.
"""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0098-whole-head-foundation';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 staged=subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).splitlines()
 if staged:assert set(staged)<=set(read(E/'history-allowlist.json')['files']),'Preserve unrelated staged production blobs'
 allow=[];files=[];lfs=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<512*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.exr','.npy','.gif'];digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest,str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=50*1024*1024:assert src.suffix=='.blend';lfs.append(row)
 audit=read(E/'female-next-r0098.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for n in ['aevrynd-female-next-r0098-authoring.json','aevrynd-female-next-r0098.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.suffix in ['.json','.npz','.npy','.png','.gif','.log','.py','.txt'] and p.name not in skip:
   rel=p.relative_to(E);archive(p,M/(('r0098-'+rel.parts[0]) if len(rel.parts)==1 else str(Path('r0098-'+rel.parts[0]).joinpath(*rel.parts[1:]))))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0098*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 reference=read(E/'official-female-reference.json');original=Path(reference['source']);assert sha(original)==reference['sourceSha256'];archive(original,M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend')
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 textures=read(E/'minimum-saved-readback.json')['b']['externalTextures']
 for row in textures:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 refs=[(S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend',M/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend')]
 for view in ['face','profile','body-face']:
  src=E.parent/'r0097-scalp-ear-authored-controls'/('matched-neutral-bound-reference-'+view+'.png');refs.append((src,M/('r0097-'+src.name)))
 for src,dst in refs:assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r98 complete-head source history; B202MB preserved, no size trimming.','r0098-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0098-*/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0098* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0098-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','r0098-failed-source-visibility/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend -text']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0098*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_FAILED_COMPLETE_HEADS_AND_FULL_ORIGINAL_SOURCE','files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'shared15TexturesReusedUnchanged':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks; two new above50MiB .blend paths use exact-path normal Git LFS, including intact202102951-byte B. Original49420489-byte official bundle saved as a normal Git blob. No old history migration, hook bypass, incomplete push or trimming.','scope':'Both complete assemblies rejected; original fine artist head data only retained. No complete gain, natural motion, finite contact or runtime acceptance.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0098-history-copy-integrity.json')
 bundle={'schema':1,'decision':audit['decision'],'files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'threeRoundWholeReviewWindow':['r96','r97','r98'],'adoptedCompleteOperationNaturalMotionContactRuntimeWebsite':False,'rights':read(S/'aevrynd-female-next-r0098-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0098-history-bundle.json',bundle);allow.append((M/'r0098-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0098-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R98_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS sources')
if __name__=='__main__':main()
