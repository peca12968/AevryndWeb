"""Exact immutable full source and scoped evidence; normal LFS is mandatory."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0113-coherent-head-foundation';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO).strip();allow=[];files=[]
 def archive(src,dst):
  immutable=src.suffix in ['.blend','.png','.npz','.gif'];dst.parent.mkdir(parents=True,exist_ok=True);digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':digest,'bytes':src.stat().st_size,'immutableHardlink':immutable})
 sources=[Path(row['source']) for row in read(E/'female-next-r0113.visual-audit.json')['prototypeSources'].values()];source=sources[0]
 for p in sources+[S/'aevrynd-female-next-r0113-authoring.json',S/'aevrynd-female-next-r0113.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob("*")):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/('r0113-'+p.relative_to(E).as_posix().replace('/','__')))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0113*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 for item in read(E.parent/'r0110-ordered-lid-topology/minimum-saved-failure-readback.json')['baseline']['externalTextures']:
  rel=item['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==item['sha256'];reused.append({'file':(M/rel).relative_to(REPO).as_posix(),'sha256':item['sha256']})
 original=read(E/'before.json')['source'];assert sha(Path(original['source']))==sha(M/Path(original['source']).name)==original['sha256'];reused.append({'file':(M/Path(original['source']).name).relative_to(REPO).as_posix(),'sha256':original['sha256']})
 for src,dst in [(R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend',M/'source-inputs/r0091-ellie-native-groom/ellie.blend'),(R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend',M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend')]:
  assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':'Complete existing artist input reused; reference is not character adoption.'})
  for name in ['NOTICE.txt','PROVENANCE.json']:
   notice=dst.parent/name
   if notice.is_file():reused.append({'file':notice.relative_to(REPO).as_posix(),'sha256':sha(notice),'role':'Existing source attribution/provenance retained.'})
 src=E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json';dst=M/'r0100-native-eye-topology.json';assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src),'role':'Exact original eye-centre staging metadata, not globe-contact proof.'})
 core=R/'Reference/character/makehuman-core-cc0'
 keep=[core/'LICENSE.md',core/'LICENSE.ASSETS.md',core/'download-provenance.json',core/'mpfb2-source-tree.json']+list((core/'src/mpfb/data').rglob('*'))+list((core/'system-skin').rglob('*'))
 for p in sorted(set(keep)):
  if p.is_file():archive(p,M/'source-inputs/r0113-makehuman-core'/p.relative_to(core))
 archive(S/'makehuman-native-head-textures/young_lightskinned_female_diffuse.png',M/'makehuman-native-head-textures/young_lightskinned_female_diffuse.png')
 attr=M/'.gitattributes';text=attr.read_text('utf8');rules=['# Exact r113 coherent whole-head source, failed A and retained unaccepted B.','r0113-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0113* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',*[p.name+' filter=lfs diff=lfs merge=lfs -text' for p in sources],'r0113-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','source-inputs/r0113-makehuman-core/** -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','makehuman-native-head-textures/* -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf8');rule='*female-next-r0113*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(p),'file':(M/p.name).relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'scope':'Two complete full-source candidates in one actual production round: coherent CC0 adult whole head/native same-topology closure, then neck/native-UV/brow reconstruction. A rejected for collar/material failure; B retained as one explicit unaccepted working foundation, not complete appearance/operation adoption. Actual new skin/optics have capped intersection-or-touch witnesses, posterior neck ledge/crease, ear/hair and brow failures remain. Dependency-complete B source preserves identical pre/post separation displayed geometry; original full sources retained, no history deleted. Full pinned core mesh/targets/licenses and complete original selected system texture/MHMAT bytes and provenance archived; shared textures reused. No runtime promotion.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0113-history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R113_EXACT_ARCHIVE_READY',len(set(allow)),source.stat().st_size)
if __name__=='__main__':main()
