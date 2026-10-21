"""Exact complete unaccepted r121 source and evidence, protected C-volume storage."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0121-native-skin-surface';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).strip();allow=[];files=[];reused=[]
 def archive(src,dst):
  immutable=src.suffix in ['.blend','.png','.npz','.gif'];dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src)
  if dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 a=read(E/'female-next-r0121.visual-audit.json');sources=[Path(x['source']) for x in a['prototypeSources'].values()]
 for source in sources:archive(source,M/'r0121-source'/source.name)
 for p in [S/'aevrynd-female-next-r0121-authoring.json',S/'aevrynd-female-next-r0121.LICENSE-SOURCE.txt']:archive(p,M/p.name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/'r0121-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0121*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 def reuse(src,dst,role):
  h=sha(src);assert dst.is_file() and sha(dst)==h;reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':h,'bytes':src.stat().st_size,'role':role})
 for t in read(E/'minimum-saved-skin-surface-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Full original shared texture bytes; unchanged color path and preserved source inputs. No redundant copy.')
 w=a['workingCompleteWomanReference'];p=Path(w['source']);reuse(p,M/p.relative_to(S),'Exact full r117 working woman and rollback, with r115 neck/brow gains.')
 for n in ['build-female-next-r0116-native-eye-character.py','build-female-next-r0113-native-neck-character.py']:
  reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Unmodified existing geometry/pose/render helper, archived full code remains in history.')
 previous117=read(E.parent/'r0117-native-fibre-brows/history-copy-integrity.json')
 for row in previous117['files']:
  src=Path(row['source'])
  if src.parent==E.parent/'r0117-native-fibre-brows' and (src.name.startswith('matched-a-native-fibre-brows-') or src.name=='a-view-controls.json'):
   reuse(src,G/row['file'],'Actual unchanged r117 matched complete baseline image/control record used by this comparison.')
 for row in read(E.parent/'r0113-coherent-head-foundation/history-copy-integrity.json')['files']:
  if row['file'].startswith('assets-source/aevrynd-character/female-next/source-inputs/r0113-makehuman-core/'):
   reuse(Path(row['source']),G/row['file'],'Full pinned native mesh/targets/source license/provenance already archived; preserved with the complete working source.')
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r121 native skin-surface research source and evidence; no appearance adoption.','r0121-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0121-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0121* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0121-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0121*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 previous=read(E.parent/'r0120-ocular-socket-construction/history-copy-integrity.json');stable=[row for row in previous['files'] if row['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(row['source']))==row['sha256'] and sha(G/row['file'])==row['sha256'] for row in stable)
 rolling=[row for row in previous['files'] if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert len(rolling)==1 and sha(E/'manifest-before.json')==rolling[0]['sha256']==sha(M/'r0121-evidence/manifest-before.json');blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling[0]['file']]);assert hashlib.sha256(blob).hexdigest()==rolling[0]['sha256']
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(source),'file':(M/'r0121-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size} for source in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0121','allPriorR120StableSourceAndArchiveRecordsStillExact':len(stable),'priorRollingManifestExactBeforeSnapshotAndCommittedBlobPreserved':True,'scope':'One complete r117-derived native skin-surface construction candidate with source-identical geometry/keys/UV/fibres/original diffuse and no clear complete appearance gain. Full source preserved, original r117 remains working. All282 old full sources and historical findings protected. C source/evidence/separate archive behind canonical D junctions; immutable media linked only, mutable metadata ordinary independent copies. All finite contact/runtime/performance/user acceptance gaps remain open; no incomplete LFS or history pruning.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0121-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R121_FULL_EXACT_ARCHIVE_READY',len(set(allow)),sources[0].stat().st_size,flush=True)
if __name__=='__main__':main()
