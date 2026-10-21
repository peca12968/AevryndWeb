"""Exact one-source craniofacial volume trial history; reuse full original dependencies."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0125-craniofacial-rest-shape';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
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
 audit=read(E/'female-next-r0125.visual-audit.json');sources=[Path(row['source']) for row in audit['prototypeSources'].values()]
 for source in sources:archive(source,M/'r0125-source'/source.name)
 for name in ['aevrynd-female-next-r0125-authoring.json','aevrynd-female-next-r0125.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/'r0125-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0125*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 textures=set()
 for t in read(E/'minimum-saved-source-readback.json')['allReferencedExternalTextures']:
  src=Path(t['absolute']);rel=t['relative'].replace('\\','/');assert src.is_file() and sha(src)==t['sha256'];assert rel.startswith('//../');assert src.resolve().is_relative_to(S.resolve())
  if str(src.resolve()) in textures:continue
  textures.add(str(src.resolve()));reuse(src,M/rel[5:],'Exact complete shared original texture; same source-relative path and full bytes, no redundant copy.')
 w=Path(audit['workingCompleteWomanReference']['source']);reuse(w,M/w.relative_to(S),'Exact full r117 working woman and adopted static neck/brow rollback.')
 for n in ['build-female-next-r0116-native-eye-character.py','build-female-next-r0113-native-neck-character.py','build-female-next-r0104-native-head-union.py','finalize-female-next-r0121.py']:reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Existing exact source/geometry/render/sheet helper, not a new method.')
 for rev,names in [('r0117-native-fibre-brows',None),('r0099-continuous-head-neck',{'matched-c-continuous-artist-profile.png','matched-c-continuous-artist-face.png','matched-c-continuous-artist-body-face.png','matched-c-continuous-artist-oblique.png'})]:
  for row in read(E.parent/rev/'history-copy-integrity.json')['files']:
   src=Path(row['source'])
   wanted=src.parent==E.parent/rev and (src.name.startswith('matched-a-native-fibre-brows-') or src.name=='a-view-controls.json') if names is None else src.name in names
   if wanted:reuse(src,G/row['file'],'Exact prior actual complete baseline or attributed original3D shape-reference image, no new reference geometry transfer.')
 for rev,tag in [('r0123-current-scalp-growspace','a-current-scalp-growspace'),('r0123-current-scalp-growspace','b-source-atlas-flow'),('r0124-native-nasal-sculpt','a-live-native-nasal-sculpt')]:
  records=read(E.parent/rev/'history-copy-integrity.json')['files']
  for view in ['face','body-face']:
   src=E.parent/rev/('matched-'+tag+'-'+view+'.png');row=next(x for x in records if Path(x['source'])==src);reuse(src,G/row['file'],'Exact actual complete prior trial head/body for required three-round review123/124/125.')
 # Original MakeHuman input data/rights remain complete in previous history.
 old113=read(E.parent/'r0113-coherent-head-foundation/history-copy-integrity.json');nativeInputs=[row for key in ['files','reusedInputs'] for row in old113.get(key,[]) if 'r0113-makehuman-core' in row['file']];assert len(nativeInputs)>=19
 for row in nativeInputs:reuse(Path(row['source']),G/row['file'],'Unmodified complete native base/target/UV/asset-license input retained in prior history.')
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r125 rejected native craniofacial volume cage and saved live-source recovery.','r0125-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0125-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0125* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0125-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0125*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 previous=read(E.parent/'r0124-native-nasal-sculpt/history-copy-integrity.json');stable=[row for row in previous['files'] if row['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(row['source']))==sha(G/row['file'])==row['sha256'] for row in stable)
 rolling=next(row for row in previous['files'] if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256']==sha(M/'r0125-evidence/manifest-before.json');blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']]);assert hashlib.sha256(blob).hexdigest()==rolling['sha256']
 integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(p),'file':(M/'r0125-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0125','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':'D:/Download/Aevrynd/sites-engine-journey/.git/objects','allPriorR124StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One full rejected complete craniofacial volume cage source, exact matched eight views, actual source/edit/restore lineage and all289 prior sources preserved. Same r117 working woman remains; no appearance/new complete operation/contact/runtime acceptance. C live Git objects and normal complete LFS are protected history. Mutable evidence copied; immutable media linked across separate C directories. No deletion/move/prune or hook bypass.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0125-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R125_EXACT_ONE_FULL_SOURCE_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),flush=True)
if __name__=='__main__':main()
