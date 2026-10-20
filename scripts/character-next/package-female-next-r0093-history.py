"""Exact scoped rejected r93 sources/evidence, reusing existing inputs/textures."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0093-surface-bound-direct-rods';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.exr']
  if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  digest=sha(src);assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable})
 audit=read(E/'female-next-r0093.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for n in ['aevrynd-female-next-r0093-authoring.json','aevrynd-female-next-r0093.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.png','.log','.txt','.py'] and p.name not in skip:archive(p,M/('r0093-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0093*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 for n in ['groom_direct_chain_study.py','groom_contact_projected_chain_study.py']:archive(R/'engine/character/physics'/n,REPO/'engine/character/physics'/n)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 reused=[];check=read(E/'minimum-saved-readback.json')['a']
 for row in check['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 for src,dst in [(S/'aevrynd-female-next-r0092-a-native-Eve-groom.blend',M/'aevrynd-female-next-r0092-a-native-Eve-groom.blend'),(R/'Reference/character/charmorph-vitruvian-cc0/hair.blend',M/'source-inputs/r0092-native-vitruvian-groom/hair.blend')]:
  assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 for view in ['face','back','body-face']:
  src=E.parent/'r0092-native-compatible-groom'/('matched-a-native-Eve-'+view+'.png');dst=M/('r0092-'+src.name);assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 rules=[(M/'.gitattributes',['# Exact r93 rejected full-woman static chain studies.','r0093-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0093* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0093-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']), (REPO/'scripts/character-next/.gitattributes',['*female-next-r0093*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']), (REPO/'engine/character/physics/.gitattributes',['groom_direct_chain_study.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','groom_contact_projected_chain_study.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]
 for attr,add in rules:
  text=attr.read_text('utf-8') if attr.exists() else ''
  for row in add:
   if row not in text:text=text.rstrip()+'\n'+row+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_SCOPED_REJECTED_SOURCES_AND_EVIDENCE','files':files,'reusedInputs':reused,'shared15RelativeTexturesVerifiedNotCopied':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks; existing textures/source input/baseline reused. No source cache/model content omitted by acceptance filter.','scope':'Two static full-woman failures, same r93 production round; no natural motion/runtime or complete gain.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0093-history-copy-integrity.json')
 bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedInputs':reused,'completeCharacterGain':False,'adoptedAppearanceNewCompleteOperationContactMotionRuntimeWebsite':False,'rights':read(S/'aevrynd-female-next-r0093-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0093-history-bundle.json',bundle);allow.append((M/'r0093-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0093-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R93_EXACT_HISTORY',len(record['files']),sum(row['bytes'] for row in files),'logical bytes, immutable files linked')
if __name__=='__main__':main()
