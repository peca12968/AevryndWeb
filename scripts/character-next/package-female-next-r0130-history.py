"""Preserve both complete failed sources and two distinct source references exactly."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0130-artist-native-groom';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']);allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst));reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0130.visual-audit.json');sources=[Path(x['source']) for x in audit['prototypeSources'].values()]+[Path(x['source']) for x in audit['researchReferenceSources'].values()]
 for p in sources:archive(p,M/'r0130-source'/p.name)
 for name in ['aevrynd-female-next-r0130-authoring.json','aevrynd-female-next-r0130.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'};unpublished=[]
 for p in sorted(E.rglob('*')):
  if not p.is_file() or p.name in skip:continue
  if p.name.startswith(('original-text-','publisher-')) or p.name in ['hair-bsdf-source-links.json','ellie-original-rigged-particle-hair-readonly.txt']:
   unpublished.append({'localReference':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'reason':'Original publisher HTML/text or redundant embedded source script retained locally; no new redistribution of unversioned source contents. Original licensed studio .blend/script and notices already retained in full existing input.'});continue
  archive(p,M/'r0130-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0130*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 prior=read(E.parent/'r0129-native-authored-bob/history-copy-integrity.json')
 for row in prior['reusedInputs']:reuse(Path(row['source']),G/row['file'],'Exact existing helper/body/face/texture/rollback dependency.')
 for row in prior['files']:
  if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json':continue
  assert sha(Path(row['source']))==sha(G/row['file'])==row['sha256']
  if row['file'].endswith(('authored-native-scalp-domain.npz','authored-native-guide-lineage.npz')):reuse(Path(row['source']),G/row['file'],'Exact existing actual current-head scalp topology/bind correspondence input.')
 lookup={}
 for dirname in ['r0057-coherent-foundation','r0091-clump-cross-sections','r0092-native-compatible-groom','r0127-native-lid-closure']:
  p=E.parent/dirname/'history-copy-integrity.json'
  if p.exists():
   old=read(p)
   for row in old.get('files',[])+old.get('reusedInputs',[]):
    if row.get('source') and row.get('file'):lookup[Path(row['source']).as_posix()]=row
 wanted=[R/'Reference/character/charmorph-vitruvian-cc0/hair.blend',R/'Reference/character/charmorph-vitruvian-cc0/r0092-native-Eve/PROVENANCE.json',R/'Reference/character/charmorph-vitruvian-cc0/config.yaml',E.parent/'r0092-native-compatible-groom/native-Eve-source.npz',E.parent/'r0092-native-compatible-groom/native-Eve-actual-children.npz',E.parent/'r0092-native-compatible-groom/native-source-verification.json',E.parent/'r0057-coherent-foundation/canonical-mesh-data.npz',E.parent/'r0127-native-lid-closure/native-head-topology.npz',R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend',R/'Reference/character/blender-studio-ellie-v1-cc-by4/NOTICE.txt',R/'Reference/character/blender-studio-ellie-v1-cc-by4/PROVENANCE.json']
 for src in wanted:
  row=lookup.get(src.as_posix())
  if row is None:
   choices=[]
   if src.name=='config.yaml':choices=list((M/'source-inputs').rglob('config.yaml'))
   elif src.is_relative_to(E.parent):choices=[M/(src.parent.name.split('-')[0]+'-evidence')/src.name,M/(src.parent.name.split('-')[0]+'-'+src.name)]
   matches=[p for p in choices if p.is_file() and sha(p)==sha(src)];assert matches,(str(src),'Missing exact existing input mapping');row={'file':matches[0].relative_to(G).as_posix()}
  reuse(src,G/row['file'],'Complete original licensed source/rights or actual immutable native topology/cache input, reused without duplicate copies.')
 for t in [t for row in read(E/'minimum-saved-emitter-field-readback.json')['sources'].values() for t in row['allReferencedExternalTextures']]:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture under same source-relative sibling path.')
 rolling=next(r for r in prior['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];blob=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']]);assert hashlib.sha256(blob).hexdigest()==rolling['sha256']
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['r0130-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0130-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0130* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0130-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0130*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());unique={r['file']:r for r in reused};integrity={'files':files,'reusedInputs':list(unique.values()),'localReferencesNotNewlyRedistributed':unpublished,'fullSources':[{'source':str(p),'file':(M/'r0130-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'fullCompleteCharacterSources':2,'fullSourceReferenceBlends':2,'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0130','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':'D:/Download/Aevrynd/sites-engine-journey/.git/objects','allPriorR129StableRecordsStillExact':len(prior['files'])-1,'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One actual complete r130 round, A/B source-scalp field constructions both rejected, separate source-reference recovery only. R126 working woman unchanged; all299 prior complete source files and two new research+two complete failed sources retained. No appearance/complete-operation/natural dynamics/finite contact/runtime/female acceptance. No history deletion/prune, new services/install/subagents or duplicated original inputs.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0130-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R130_EXACT_FOUR_FULL_SOURCES_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
