"""Exact single rejected r87 native optical archive; reuse pinned sources/textures."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0087-eye-solids';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
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
 audit=read(E/'female-next-r0087.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for name in ('aevrynd-female-next-r0087-authoring.json','aevrynd-female-next-r0087.LICENSE-SOURCE.txt'):archive(S/name,M/name)
 for p in sorted(E.iterdir()):
  if not p.is_file() or p.suffix not in ('.json','.png','.gif','.log','.txt','.npz') or p.name in ('history-bundle.json','history-allowlist.json','github-receipt.json','history-copy-integrity.json','local-commit.json','staged-verification.json'):continue
  archive(p,M/('r0087-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0087*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(E/'minimum-source-readback.json')['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 reused=[]
 for name in ('aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend','aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend','aevrynd-female-next-r0081-b-stable-frame-curly-study.blend'):
  assert sha(S/name)==sha(M/name);reused.append({'file':(M/name).relative_to(REPO).as_posix(),'sha256':sha(M/name)})
 lineage=R/'Evidence/character-female-next/r0081-editable-curly-groom/a-guide-and-render-lineage.npz';assert sha(lineage)==sha(M/'r0081-a-guide-and-render-lineage.npz');reused.append({'file':(M/'r0081-a-guide-and-render-lineage.npz').relative_to(REPO).as_posix(),'sha256':sha(lineage)})
 raw=M/'source-inputs/r0081-publisher-guide-demo/hair_nodes-female_hair_styles.blend';assert sha(raw)=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48';reused.append({'file':raw.relative_to(REPO).as_posix(),'sha256':sha(raw),'notice':'source-inputs/r0081-publisher-guide-demo/NOTICE.txt'})
 attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');marker='# Exact r87 rejected source-face native optical study.'
 if marker not in text:
  text=text.rstrip()+'\n'+marker+'\nr0087-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0087* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0087-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n';attr.write_text(text,encoding='utf-8',newline='\n')
 allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0087*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'PASS_EXACT_ARCHIVE_RELATIVE_TEXTURES_AND_REUSED_INPUTS','files':files,'sourceAndArchiveBytesEqual':True,'all15SharedTexturesVerifiedWithoutRecopy':True,'reusedInputs':reused,'formalWorkingResearchAndWebsitePromotion':False};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0087-history-copy-integrity.json')
 bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactInputs':reused,'registeredWorkingSourceStillR76':True,'retainedCompleteGroomStudyStillR81B':True,'allR87SourcesRejectedFailureEvidenceOnly':True,'wholeCharacterStagnationReset':False,'fullContactNaturalMotionRuntimeOrWebsitePromoted':False,'rights':'Inherited CC0 body/rig/morph; Daniel Bystedt hair CC BY-SA version unspecified, source input/notice reused from r81. No exclusive ownership claim.'};save(E/'history-bundle.json',bundle);save(M/'r0087-history-bundle.json',bundle);allow.append((M/'r0087-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0087-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R87_EXACT_FAILURE_ARCHIVE',len(record['files']),sum(x['bytes'] for x in files),'logical bytes; immutable files hardlinked')
if __name__=='__main__':main()
