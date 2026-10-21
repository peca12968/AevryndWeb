"""Exact two-source failed trials and protected C Git-object recovery history."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0123-current-scalp-growspace';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 existing=subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).decode().splitlines()
 if existing:assert sorted(existing)==sorted(read(E/'history-allowlist.json'))
 allow=[];files=[];reused=[]
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
 audit=read(E/'female-next-r0123.visual-audit.json');sources=[Path(r['source']) for r in audit['prototypeSources'].values()]
 for source in sources:archive(source,M/'r0123-source'/source.name)
 for name in ['bob01-undirected-strand-flow.png','PROVENANCE.json']:archive(S/'r0123-source/native-strand-flow'/name,M/'r0123-source/native-strand-flow'/name)
 for p in [S/'aevrynd-female-next-r0123-authoring.json',S/'aevrynd-female-next-r0123.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/'r0123-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0123*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 texturePaths=set()
 for candidate in read(E/'minimum-saved-source-readback.json')['sources'].values():
  for t in candidate['allReferencedExternalTextures']:
   src=Path(t['absolute'])
   if str(src) in texturePaths:continue
   texturePaths.add(str(src))
   rel=t['relative'].replace('\\','/')
   if rel.startswith('//native-strand-flow/'):
    assert src.resolve().is_relative_to((S/'r0123-source').resolve());continue
   assert rel.startswith('//../');reuse(src,M/rel[5:],'Exact full original shared texture or full original r122 bob01 RGBA, no duplicate copy.')
 w=audit['workingCompleteWomanReference'];p=Path(w['source']);reuse(p,M/p.relative_to(S),'Exact full r117 complete working woman and adopted neck/brow rollback.')
 for revision,names in [('r0122-native-swept-back-groom',{'native-back-groom-lineage.npz','source-reference.json','matched-c-native-alpha-cards-face.png','matched-c-native-alpha-cards-profile.png','c-view-controls.json'}),('r0092-native-compatible-groom',{'native-Eve-source.npz','hair.blend'})]:
  for row in read(E.parent/revision/'history-copy-integrity.json')['files']:
   if Path(row['source']).name in names:reuse(Path(row['source']),G/row['file'],'Exact original source guide/child/emitter/topology or actual source comparison input, fully retained earlier.')
 source=S/'r0122-source/aevrynd-female-next-r0122-c-native-alpha-cards.blend';reuse(source,M/source.relative_to(S),'Exact complete input to source-flow-only trial, full original cards/material/RGBA source retained.')
 for n in ['build-female-next-r0116-native-eye-character.py','build-female-next-r0113-native-neck-character.py','build-female-next-r0104-native-head-union.py','finalize-female-next-r0121.py']:reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Exact existing actual geometry/root-frame/render/sheet helper, not a new solver.')
 for row in read(E.parent/'r0117-native-fibre-brows/history-copy-integrity.json')['files']:
  src=Path(row['source'])
  if src.parent==E.parent/'r0117-native-fibre-brows' and (src.name.startswith('matched-a-native-fibre-brows-') or src.name=='a-view-controls.json'):reuse(src,G/row['file'],'Exact actual matched working baseline image/control record, no rerender or duplicate source copy.')
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r123 failed whole-groom/atlas-data sources and C Git-storage recovery.','r0123-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0123-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','r0123-source/native-strand-flow/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0123* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0123-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0123*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 previous=read(E.parent/'r0122-native-swept-back-groom/history-copy-integrity.json');stable=[r for r in previous['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable);rolling=next(r for r in previous['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256']==sha(M/'r0123-evidence/manifest-before.json');blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']]);assert hashlib.sha256(blob).hexdigest()==rolling['sha256']
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(source),'file':(M/'r0123-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size} for source in sources],'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0123','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':'D:/Download/Aevrynd/sites-engine-journey/.git/objects','allPriorR122StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'Two full rejected complete sources, all strands/root failures and original widths preserved. Deterministic source atlas DATA field leaves original RGBA/scalars/geometry exact. Current r117 woman and all286 prior complete sources retained. Normal live C Git-object store and normal C LFS storage, no old object/source/history deletion/move/prune. Evidence/archive separate C directories; mutable evidence metadata copied, immutable media linked. No appearance/complete-operation/contact/runtime adoption.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0123-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R123_EXACT_TWO_SOURCE_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),flush=True)
if __name__=='__main__':main()
