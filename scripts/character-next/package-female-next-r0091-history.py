"""Exact scoped r91 rejected-source history, reusing inherited textures/inputs."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0091-clump-cross-sections';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.exr']
  if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  digest=sha(src);assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable})
 audit=read(E/'female-next-r0091.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for name in ['aevrynd-female-next-r0091-authoring.json','aevrynd-female-next-r0091.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json','authored-fibre-lofts.npz','authored-studio-fibres.npz'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.png','.log','.txt'] and p.name not in skip:archive(p,M/('r0091-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0091*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');ref=R/'Reference/character/blender-studio-ellie-v1-cc-by4'
 for name in ['ellie.blend','NOTICE.txt','PROVENANCE.json']:archive(ref/name,M/'source-inputs/r0091-ellie-native-groom'/name)
 reused=[]
 for name in ['aevrynd-female-next-r0088-b-supported-lid-aperture.blend','aevrynd-female-next-r0090-b-rain-hair-shape-study.blend']:
  assert sha(S/name)==sha(M/name);reused.append({'file':(M/name).relative_to(REPO).as_posix(),'sha256':sha(S/name)})
 for row in read(E/'minimum-saved-readback.json')['sources'][0]['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 for name in ['a-guide-lineage.npz','actual-head-surface.npz','b-rain-hair-lineage.npz']:
  src=E.parent/'r0090-native-scalp-groom'/name;dst=M/('r0090-'+name);assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');rules=['# Exact r91 rejected complete fibre sources.','r0091-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0091* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0091-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','r0091-ellie-embedded-ReadMe.txt -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','source-inputs/r0091-ellie-native-groom/* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0091*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 save(E/'history-copy-integrity.json',{'status':'PASS_EXACT_ARCHIVE_SCOPED_INPUTS_AND15_RELATIVE_TEXTURES','files':files,'reusedInputs':reused,'allSourceArchiveBytesEqual':True,'skippedRegenerableIntermediates':['authored-fibre-lofts.npz','authored-studio-fibres.npz'],'regeneration':'Run respective author script from preserved extracted source data; both actual saved fibre lineages remain archived.','physicalCopies':'Immutable files same-volume hardlinks; existing texture files are verified/reused, not copied.'});archive(E/'history-copy-integrity.json',M/'r0091-history-copy-integrity.json')
 bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedInputs':reused,'completeCharacterGain':False,'adoptedAppearanceNewCompleteOperationContactMotionRuntimeWebsite':False,'rights':read(S/'aevrynd-female-next-r0091-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0091-history-bundle.json',bundle);allow.append((M/'r0091-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0091-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R91_EXACT_HISTORY',len(record['files']),sum(x['bytes'] for x in files),'logical bytes; immutable files linked')
if __name__=='__main__':main()
