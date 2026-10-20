"""Exact r96 woman/source-reference archive; four new exact-path LFS blobs."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0096-artist-bob-foundation';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
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
  if src.stat().st_size>=50*1024*1024:assert src.suffix=='.blend';lfs.append(row)
 audit=read(E/'female-next-r0096.visual-audit.json')
 for row in audit['prototypeSources'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/p.name)
 for row in audit['sourceReferenceSavesSeparateFromProductionCandidates'].values():
  p=Path(row['source']);assert sha(p)==row['sha256'];archive(p,M/(p.name if p.parent==S else 'r0096-'+p.name))
 for n in ['aevrynd-female-next-r0096-authoring.json','aevrynd-female-next-r0096.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.png','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0096-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0096*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');reused=[]
 for row in read(E/'minimum-saved-readback.json')['a']['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
 refs=[(S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend',M/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend'),(E.parent/'r0092-native-compatible-groom/native-Eve-source.npz',M/'r0092-native-Eve-source.npz'),(E.parent/'r0094-authored-growth-routing/b-source-width-lineage.npz',M/'r0094-b-source-width-lineage.npz'),(E.parent/'r0057-coherent-foundation/canonical-mesh-data.npz',M/'r0057-canonical-mesh-data.npz'),(R/'Reference/character/charmorph-vitruvian-cc0/hair.blend',M/'source-inputs/r0092-native-vitruvian-groom/hair.blend')]
 for view in ['face','back','body-face']:
  src=E.parent/'r0094-authored-growth-routing'/('matched-b-source-width-'+view+'.png');refs.append((src,M/('r0094-'+src.name)))
 for src,dst in refs:assert sha(src)==sha(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r96 complete woman and separately labelled source references.','r0096-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0096* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0096-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0096*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_SCOPED_COMPLETE_WOMAN_DIRECTION_AND_SEPARATE_SOURCE_REFERENCES','files':files,'lfsSources':lfs,'reusedInputs':reused,'shared15TexturesReusedUnchanged':True,'allSourceArchiveBytesEqual':True,'physicalCopies':'Immutable same-volume hardlinks; four new above50MiB .blend paths use exact-path normal Git LFS to bound pack memory. No old history migration, hook bypass, incomplete push or size trimming.','scope':'One actual artist-spatial complete woman direction, three separately labelled derived source reference saves and preserved support/save failures. Static contact/control scope only; no adopted complete gain.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0096-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files,'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'staticArtistSourceDataOnly':True,'adoptedCompleteOperationNaturalMotionContactRuntimeWebsite':False,'rights':read(S/'aevrynd-female-next-r0096-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0096-history-bundle.json',bundle);allow.append((M/'r0096-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0096-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R96_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS sources')
if __name__=='__main__':main()
