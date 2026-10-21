"""Exact immutable full source and scoped evidence; normal LFS is mandatory."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
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
 sources=[Path(row['source']) for row in read(E/'female-next-r0111.visual-audit.json')['prototypeSources'].values()];source=sources[0]
 for p in sources+[S/'aevrynd-female-next-r0111-authoring.json',S/'aevrynd-female-next-r0111.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob("*")):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/('r0111-'+p.relative_to(E).as_posix().replace('/','__')))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0111*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 for item in read(E.parent/'r0110-ordered-lid-topology/minimum-saved-failure-readback.json')['baseline']['externalTextures']:
  rel=item['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==item['sha256'];reused.append({'file':(M/rel).relative_to(REPO).as_posix(),'sha256':item['sha256']})
 original=read(E/'before.json')['source'];assert sha(Path(original['source']))==sha(M/Path(original['source']).name)==original['sha256'];reused.append({'file':(M/Path(original['source']).name).relative_to(REPO).as_posix(),'sha256':original['sha256']})
 for src,dst in [(R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend',M/'source-inputs/r0091-ellie-native-groom/ellie.blend'),(R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend',M/'source-inputs/r0098-official-human-bases/human_base_meshes_bundle.blend')]:
  assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':'Complete existing artist input reused; reference is not character adoption.'})
  for name in ['NOTICE.txt','PROVENANCE.json']:
   notice=dst.parent/name
   if notice.is_file():reused.append({'file':notice.relative_to(REPO).as_posix(),'sha256':sha(notice),'role':'Existing source attribution/provenance retained.'})
 for folder,name in [('r0107-native-coarse-lid-cage','native-coarse-lid-poses-pinned.npz'),('r0104-native-artist-ocular-foundation','animation-actual-source-geometry.npz'),('r0100-native-eyelid-assembly','native-eye-topology.json')]:
  src=E.parent/folder/name;dst=M/(folder.split('-')[0]+'-'+name);assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':'Exact existing source/staging input reused.'})
 rain=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain-v3.3.zip';rainArchive=M/'source-inputs/r0090-rain-rig/Rain-v3.3.zip';assert sha(rain)==sha(rainArchive)=='80217f163f6392dc829233d63c2cfb5e1376775bc34101ad14f39631fea70d24';reused.append({'file':rainArchive.relative_to(REPO).as_posix(),'sha256':sha(rain),'bytes':rain.stat().st_size,'role':'Complete original Rain source zip includes head, ocular materials/UV, source rig data and required eye PNG; no source script execution.'})
 for name in ['NOTICE.txt','PROVENANCE.json']:
  p=rainArchive.parent/name;reused.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'role':'Original R90 source attribution retained; R111 adds explicit geometry/texture reuse notice.'})
 import zipfile
 blend=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend'
 with zipfile.ZipFile(rain) as z:originalBlend=z.read('Rain v3.3/rain_v3.2.blend')
 assert hashlib.sha256(originalBlend).hexdigest()==sha(blend);reused.append({'file':rainArchive.relative_to(REPO).as_posix(),'zipEntry':'Rain v3.3/rain_v3.2.blend','entrySha256':sha(blend),'entryBytes':len(originalBlend),'role':'Verified complete exact source Blender entry; reused full archive, no duplicate input blob.'})
 texture=read(E/'restored-source-eye-texture.json');archive(Path(texture['restoredFile']),M/'source-inputs/r0111-rain-eye-texture/TEX-rain_eyes.png');archive(E/'new-eye-texture-NOTICE.txt',M/'source-inputs/r0111-rain-eye-texture/NOTICE.txt')
 attr=M/'.gitattributes';text=attr.read_text('utf8');rules=['# Exact r108 rejected fine anterior lip trial and retained failures.','r0111-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0111* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',*[p.name+' filter=lfs diff=lfs merge=lfs -text' for p in sources],'r0111-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf8');rule='*female-next-r0111*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(p),'file':(M/p.name).relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'scope':'One actual source-topology mobile ocular graft, body cut ports and paired new eyes, rejected for visible seams/extra surface/spikes. Surviving body data/groom preserved; original whole skin/optics retained. Same blend with restored original eye PNG, first failed texture views and source-ID finite-wall causal diagnostic preserved. Rain CC-BY4.0 full original zip/entry/texture/rights and recovery layout verified; no appearance/complete-operation/contact/runtime adoption.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0111-history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R111_EXACT_ARCHIVE_READY',len(set(allow)),source.stat().st_size)
if __name__=='__main__':main()
