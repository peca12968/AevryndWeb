"""Exact r95 rejected source/data archive, scoped Git LFS for three large blends."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0095-authored-layered-groom';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[];lfs=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<150*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.exr']
  if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  digest=sha(src);assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=100*1024*1024:assert src.suffix=='.blend';lfs.append(row)
 audit=read(E/'female-next-r0095.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for n in ['aevrynd-female-next-r0095-authoring.json','aevrynd-female-next-r0095.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.png','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0095-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0095*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 for row in read(E/'minimum-saved-readback.json')['a']['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 refs=[(S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend',M/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend'),(E.parent/'r0094-authored-growth-routing/a-growth-volume-lineage.npz',M/'r0094-a-growth-volume-lineage.npz'),(R/'Reference/character/charmorph-vitruvian-cc0/hair.blend',M/'source-inputs/r0092-native-vitruvian-groom/hair.blend')]
 for rev,folder,tag in [('r0093','r0093-surface-bound-direct-rods','b-bound-chain'),('r0094','r0094-authored-growth-routing','b-source-width')]:
  for view in ['face','back','body-face']:
   src=E.parent/folder/f'matched-{tag}-{view}.png';refs.append((src,M/(rev+'-'+src.name)))
 for src,dst in refs:assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r95 rejected complete guide studies and native source LFS.','r0095-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0095* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0095-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0095*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_SCOPED_REJECTED_SOURCES_AND_LOCAL_GUIDE_DATA','files':files,'lfsSources':lfs,'reusedInputs':reused,'shared15TexturesReusedUnchanged':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks; only three above100MiB .blend paths use existing normal Git LFS. No old history migration, hook bypass, incomplete push or size trimming.','scope':'Three complete-groom appearance failures plus B failed input trial and whole r93/r94/r95 review; local edit coupling only, no adopted complete gain.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0095-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files,'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'localGuideDataOnly':True,'adoptedCompleteOperationNaturalMotionContactRuntimeWebsite':False,'rights':read(S/'aevrynd-female-next-r0095-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0095-history-bundle.json',bundle);allow.append((M/'r0095-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0095-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R95_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS sources')
if __name__=='__main__':main()
