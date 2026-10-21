"""Exact immutable full source and scoped evidence; normal LFS is mandatory."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0106-native-head-operation';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO).strip();allow=[];files=[]
 def archive(src,dst):
  immutable=src.suffix in ['.blend','.png','.npz'];dst.parent.mkdir(parents=True,exist_ok=True);digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':digest,'bytes':src.stat().st_size,'immutableHardlink':immutable})
 source=Path(read(E/'female-next-r0106.visual-audit.json')['prototypeSources']['a']['source'])
 for p in [source,S/'aevrynd-female-next-r0106-authoring.json',S/'aevrynd-female-next-r0106.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','lfs-progress.log'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.log']:archive(p,M/('r0106-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0106*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 for item in read(E/'independent-saved-operation-failure.json')['candidate']['externalTextures']:
  rel=item['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==item['sha256'];reused.append({'file':(M/rel).relative_to(REPO).as_posix(),'sha256':item['sha256']})
 original=read(E/'before.json')['source'];assert sha(Path(original['source']))==sha(M/Path(original['source']).name)==original['sha256'];reused.append({'file':(M/Path(original['source']).name).relative_to(REPO).as_posix(),'sha256':original['sha256']})
 attr=M/'.gitattributes';text=attr.read_text('utf8');rules=['# Exact r106 rejected native lid/control construction and full failure scope.','r0106-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0106* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',source.name+' filter=lfs diff=lfs merge=lfs -text','r0106-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf8');rule='*female-next-r0106*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'files':files,'reusedInputs':reused,'fullSource':{'source':str(source),'file':(M/source.name).relative_to(REPO).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size},'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'scope':'One complete rejected native operation source. Actual blink suppressed, raw closed shape folded,195 lash frames reversed. R105 working woman retained; no complete adoption or unrelated work.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0106-history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R106_EXACT_ARCHIVE_READY',len(set(allow)),source.stat().st_size)
if __name__=='__main__':main()
