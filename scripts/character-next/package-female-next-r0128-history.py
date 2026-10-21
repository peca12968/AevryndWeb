"""Exact two finite-lid construction sources, failed evidence and original dependency history."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0127-native-lid-closure'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 existing=subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).decode().splitlines();assert not existing
 allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst);reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0128.visual-audit.json');sources=[Path(x['source']) for x in audit['prototypeSources'].values()]
 for p in sources:archive(p,M/'r0128-source'/p.name)
 for n in ['aevrynd-female-next-r0128-authoring.json','aevrynd-female-next-r0128.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0128-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0128*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 old=read(PRE/'history-copy-integrity.json')
 # Exact dependencies already published: no redundant full artist GLB, textures,
 # original licensed source metadata/index or old complete woman copies.
 for row in old['reusedInputs']:reuse(Path(row['source']),G/row['file'],'Exact existing complete original body/texture/helper/rollback dependency.')
 wanted=[row for row in old['files'] if row['file'].startswith('scripts/character-next/') or row['file'].endswith(('aevrynd-female-next-r0127-a-native-lid-articulation.blend','aevrynd-female-next-r0127-authoring.json','aevrynd-female-next-r0127.LICENSE-SOURCE.txt','/a-build-summary.json','/a-view-controls.json','/minimum-saved-native-lid-readback.json','/native-head-topology.npz','/native-lid-authoring-lineage.npz')) or '/r0127-evidence/matched-a-native-lid-' in row['file']]
 for row in wanted:reuse(Path(row['source']),G/row['file'],'Exact r127 failed source, actual native topology, control helper and diagnosis input; not working adoption.')
 for t in [t for row in read(E/'minimum-saved-finite-lid-readback.json')['sources'].values() for t in row['allReferencedExternalTextures']]:
  src=Path(t['absolute']);assert src.resolve().is_relative_to(S.resolve());relative=Path(os.path.relpath(src.resolve(),S.resolve())) if src.resolve().is_relative_to(S.resolve()) else None
  # Source files resolve through junctions; use the recorded canonical sibling
  # path to preserve the same relative layout in the archival source directory.
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(src,M/rel[5:],'Full external original texture preserved under exact source-relative sibling path.')
 # All stable previous production records remain exactly as archived.
 stable=[row for row in old['files'] if row['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(row['source']))==sha(G/row['file'])==row['sha256'] for row in stable)
 rolling=next(row for row in old['files'] if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']]);assert hashlib.sha256(blob).hexdigest()==rolling['sha256']
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# R127 full unaccepted native blink and exact failed evidence.','r0128-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0128-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0128* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0128-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0128*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={x['file']:x for x in reused};integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(p),'file':(M/'r0128-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0128','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':'D:/Download/Aevrynd/sites-engine-journey/.git/objects','allPriorR127StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'Two full stages of one finite-lid candidate; actual head/body and failed closure/restoration, independent full source/edit recovery, original path-repair failure and source face ownership evidence, nominal versus actual finite-layer offsets. R126 adopted static working woman unchanged. No complete gain/contact/runtime/female acceptance. Whole review126/127/128 performed, common rest-only analytical blink premise retired. All295 earlier .blend sources and C Git/full LFS objects retained. No deletion/move/prune or duplicate textures.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0128-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R128_EXACT_TWO_FULL_FINITE_LID_SOURCES_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
