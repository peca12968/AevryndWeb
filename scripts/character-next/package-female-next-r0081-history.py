"""Exact unaccepted curly-study archive, including reproducible original input."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0081-editable-curly-groom';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
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
 audit=read(E/'female-next-r0081.visual-audit.json')
 for row in audit['prototypeSources'].values():
  src=Path(row['source']);assert sha(src)==row['sha256'];archive(src,M/src.name)
 for name in ('aevrynd-female-next-r0081-authoring.json','aevrynd-female-next-r0081.LICENSE-SOURCE.txt'):archive(S/name,M/name)
 for p in sorted(E.rglob('*')):
  if not p.is_file() or p.suffix not in ('.json','.png','.gif','.log','.txt','.npz') or p.name in ('history-bundle.json','history-allowlist.json','github-receipt.json','history-copy-integrity.json','local-commit.json','staged-verification.json'):continue
  assert p.parent==E;archive(p,M/('r0081-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0081*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 ref=read(E/'original-curly-evaluation.json');raw=Path(ref['source']);assert sha(raw)==ref['sha256'];rawDest=M/'source-inputs/r0081-publisher-guide-demo'/raw.name;archive(raw,rawDest);archive(E/'publisher-input.NOTICE.txt',rawDest.with_name('NOTICE.txt'))
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(E/'b-independent-readback.json')['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 reused=[]
 for name in ('aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend','aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend'):
  assert sha(S/name)==sha(M/name);reused.append({'file':(M/name).relative_to(REPO).as_posix(),'sha256':sha(M/name)})
 attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');marker='# Exact r81 attributed editable curly research; contact remains failed.'
 if marker not in text:
  text=text.rstrip()+'\n'+marker+'\nr0081-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0081* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0081-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nsource-inputs/r0081-publisher-guide-demo/* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n';attr.write_text(text,encoding='utf-8',newline='\n')
 text=attr.read_text(encoding='utf-8')
 # Preserve original embedded author notice bytes, including its whitespace.
 for pattern in ('r0081-publisher-input.NOTICE.txt','source-inputs/r0081-publisher-guide-demo/NOTICE.txt'):
  rule=pattern+' -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol'
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n')
 allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0081*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'PASS_EXACT_ARCHIVE_RELATIVE_TEXTURES_AND_ORIGINAL_INPUT','files':files,'savedSourceReadback':'r0081-b-independent-readback.json','sourceAndArchiveBytesEqual':True,'all15SharedRelativeTexturesVerifiedWithoutRecopy':True,'workingFormalRuntimeAndWebsiteNotPromoted':True};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0081-history-copy-integrity.json')
 bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactSources':reused,'originalPublisherInput':{'archive':rawDest.relative_to(REPO).as_posix(),'sha256':ref['sha256'],'notice':'source-inputs/r0081-publisher-guide-demo/NOTICE.txt','restoreForReconstructionTo':str(raw),'rights':'Daniel Bystedt CC BY-SA, version unspecified; not CC0 or exclusive ownership.'},'retainedUnacceptedStudy':audit['prototypeSources']['b'],'registeredWorkingSourceStillR76':True,'wholeCharacterStagnationReset':False,'fullContactNaturalMotionOrRuntimeWebsitePromoted':False};save(E/'history-bundle.json',bundle);save(M/'r0081-history-bundle.json',bundle);allow.append((M/'r0081-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0081-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R81_EXACT_ATTRIBUTED_RESEARCH_ARCHIVE',len(record['files']),sum(x['bytes'] for x in files),'logical bytes; immutable inputs/sources hardlinked')
if __name__=='__main__':main()
