"""Exact archive of interrupted r76 dental scope and rejected r77 complete grooms."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';BASE=R/'Evidence/character-female-next';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next';E=BASE/'r0077-guided-tip-groom'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();files=[];allow=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ('.blend','.exr','.png','.gif','.npz')
  if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  digest=sha(src);assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable})
 for rev,folder in [('r0076','r0076-proximal-crowns'),('r0077','r0077-guided-tip-groom')]:
  evidence=BASE/folder;audit=read(evidence/('female-next-'+rev+'.visual-audit.json'))
  for row in audit['prototypeSources'].values():
   src=Path(row['source']);assert sha(src)==row['sha256'];archive(src,M/src.name)
  for name in ('aevrynd-female-next-'+rev+'-authoring.json','aevrynd-female-next-'+rev+'.LICENSE-SOURCE.txt'):archive(S/name,M/name)
  for p in sorted(evidence.rglob('*')):
   if not p.is_file() or p.suffix not in ('.json','.png','.gif','.log','.txt','.npz') or p.name in ('history-bundle.json','history-allowlist.json','github-receipt.json','history-copy-integrity.json','local-commit.json'):continue
   rel=p.relative_to(evidence);dst=M/((rev+'-'+p.name) if len(rel.parts)==1 else (rev+'-'+rel.parts[0]+'/'+p.name));archive(p,dst)
  for p in sorted((R/'scripts/character-next').glob('*female-next-'+rev+'*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(BASE/'r0076-proximal-crowns/a-independent-readback.json')['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 reused=[]
 for name in ('aevrynd-female-next-r0069-a-complete-controls-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend','aevrynd-female-next-r0075-c-coordinated-oral-arc-study.blend'):
  assert sha(S/name)==sha(M/name);reused.append({'file':(M/name).relative_to(REPO).as_posix(),'sha256':sha(M/name)})
 attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');marker='# Exact r76/r77 scoped source and rejected-groom evidence.'
 if marker not in text:
  text=text.rstrip()+'\n'+marker+'\n'
  for rev in ('r0076','r0077'):text+=rev+'-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-'+rev+'* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+rev+'-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'
  attr.write_text(text,encoding='utf-8',newline='\n')
 allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8')
 for rev in ('r0076','r0077'):
  rule='*female-next-'+rev+'*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'PASS_EXACT_ARCHIVE_AND_RELATIVE_TEXTURE_DEPENDENCIES','files':files,'savedReadbacksReused':['r0076-a-independent-readback.json','r0077-rejected-source-readback.json'],'sourceAndArchiveIdenticalBytesVerified':True,'formalRuntimeOrWebsitePromotion':False};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0077-history-copy-integrity.json')
 bundle={'schema':1,'decision':'Retain r76 rigid dental scope, reject all r77 groom methods, keep whole goal unaccepted.','files':files,'reusedExactSources':reused,'sharedTexturesVerifiedWithoutRecopy':15,'workingPrototype':'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend','r77SourcesVisuallyRejected':True,'cNoSavedModel':True,'fullContactOrRuntimeOrWebsitePromoted':False,'wholeCharacterStagnationReset':False,'sourceRightsNotices':['aevrynd-female-next-r0076.LICENSE-SOURCE.txt','aevrynd-female-next-r0077.LICENSE-SOURCE.txt']};save(E/'history-bundle.json',bundle);save(M/'r0077-history-bundle.json',bundle);allow.append((M/'r0077-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0077-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R76_R77_EXACT_ARCHIVE',len(record['files']),sum(x['bytes'] for x in files),'logical bytes; immutable source files hardlinked')
if __name__=='__main__':main()
