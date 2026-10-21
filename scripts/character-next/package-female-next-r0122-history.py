"""Exact complete native-groom/card trials, original inputs and whole-review history."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0122-native-swept-back-groom';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).strip();allow=[];files=[];reused=[]
 def archive(src,dst):
  immutable=src.suffix in ['.blend','.png','.npz','.gif'];dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src)
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  h=sha(src);assert dst.is_file() and sha(dst)==h;reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':h,'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0122.visual-audit.json');sources=[Path(row['source']) for row in audit['prototypeSources'].values()]
 for source in sources:archive(source,M/'r0122-source'/source.name)
 for name in ['bob01_diffuse.png','PROVENANCE.json']:archive(S/'r0122-source/native-bob-texture-input'/name,M/'r0122-source/native-bob-texture-input'/name)
 for p in [S/'aevrynd-female-next-r0122-authoring.json',S/'aevrynd-female-next-r0122.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/'r0122-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0122*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for t in read(E/'minimum-saved-groom-readback.json')['sources']['a']['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Complete original shared r117 texture; no duplicate texture copy.')
 w=audit['workingCompleteWomanReference'];p=Path(w['source']);reuse(p,M/p.relative_to(S),'Exact full r117 working woman/rollback with adopted neck/brow gains.')
 for name in ['build-female-next-r0116-native-eye-character.py','build-female-next-r0113-native-neck-character.py','finalize-female-next-r0121.py']:reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Unmodified existing source/render/pose/sheet helper, full history retained.')
 for revision,select in [('r0092-native-compatible-groom',lambda row:Path(row['source']).name=='hair.blend'),('r0118-native-bob-construction',lambda row:('/source-inputs/r0118-native-bob-geometry/' in row['file'] or Path(row['source']).name in ['native-bob-source-authoring.blend','native-bob-source-lineage.npz']))]:
  for row in read(E.parent/revision/'history-copy-integrity.json')['files']:
   if select(row):reuse(Path(row['source']),G/row['file'],'Full original artist groom or original native bob01 mesh/MHCLO/UV/source/provenance already retained, not recooked or redownloaded.')
 for name in ['config.yaml','Default.npy','README.md']:
  src=R/'Reference/character/charmorph-vitruvian-cc0'/name;matches=[p for p in (M/'source-inputs').rglob(name) if p.is_file() and sha(p)==sha(src)];assert matches,('Missing exact existing original input archive',name);reuse(src,matches[0],'Exact existing pinned original Vitruvian native/config/contributor reference, no duplicate input copy.')
 for row in read(E.parent/'r0117-native-fibre-brows/history-copy-integrity.json')['files']:
  src=Path(row['source'])
  if src.parent==E.parent/'r0117-native-fibre-brows' and (src.name.startswith('matched-a-native-fibre-brows-') or src.name=='a-view-controls.json'):reuse(src,G/row['file'],'Exact actual r117 matched baseline image/control used by comparison.')
 for revision,tag in [('r0120-ocular-socket-construction','a-coupled-ocular-skin'),('r0121-native-skin-surface','a-native-skin-surface')]:
  for row in read(E.parent/revision/'history-copy-integrity.json')['files']:
   if Path(row['source']).name in ['matched-'+tag+'-face.png','matched-'+tag+'-body-face.png']:reuse(Path(row['source']),G/row['file'],'Actual unchanged prior complete production view used by120/121/122 whole-woman review.')
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r122 native particle/alpha-card construction research, no appearance adoption.','r0122-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0122-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','r0122-source/native-bob-texture-input/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0122* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0122-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0122*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 previous=read(E.parent/'r0121-native-skin-surface/history-copy-integrity.json');stable=[row for row in previous['files'] if row['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(row['source']))==sha(G/row['file'])==row['sha256'] for row in stable);rolling=next(row for row in previous['files'] if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256']==sha(M/'r0122-evidence/manifest-before.json');blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']]);assert hashlib.sha256(blob).hexdigest()==rolling['sha256']
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(source),'file':(M/'r0122-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size} for source in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0122','allPriorR121StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'Three complete full source states of two constructions (native Back1 plus one measured alignment repair, original same-native alpha cards), all unaccepted. Current full original PNG/CRC provenance retained; complete original libraries/MHCLO/OBJ/UV/texture/rights inputs reused exactly. All283 prior full sources retained. Whole review120/121/122 resets cadence only, no-adopt lower5. Source/evidence/separate archive use protected C junctions; immutable media linked, mutable evidence metadata copied separately. No partial LFS or deleted history.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0122-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R122_FULL_EXACT_THREE_SOURCE_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),sum(row['bytes'] for row in files if not row['file'].endswith('.blend')),flush=True)
if __name__=='__main__':main()
