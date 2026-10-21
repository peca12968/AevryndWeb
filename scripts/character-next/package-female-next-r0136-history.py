"""Exact one complete rejected volume source; reuse existing original assets."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0136-native-curve-combing';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0135-source-shape-fibres'
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
  elif immutable and src.stat().st_dev==dst.parent.stat().st_dev:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst));reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0136.visual-audit.json');sources=[Path(r['source']) for r in audit['prototypeSources'].values()]
 assert len(sources)==1
 for p in sources:archive(p,M/'r0136-source'/p.name)
 for name in ['aevrynd-female-next-r0136-authoring.json','aevrynd-female-next-r0136.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0136-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0136*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact existing original source/rights, native paths/topology, helper, baseline, texture or rollback input.')

 for name in ['build-female-next-r0130-native-emitter-field.py','build-female-next-r0131-native-hair-material.py','finalize-female-next-r0121.py']:reuse(R/'scripts/character-next'/name,G/'scripts/character-next'/name,'Exact existing material graph/value inspection helper only; no rejected geometry or shader build executed.')
 reuse(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz',M/'r0133-evidence/target-scalp-chart.npz','Exact current native scalp chart, original rights inherited, actual native Add surface input.')
 for name in ['current-hair-native-triangle-charts.npz','current-hair-chart-inspection.json','current-hair-original-texture-0.png','current-hair-original-texture-1.png']:
  reuse(E.parent/'r0130-artist-native-groom'/name,M/'r0130-evidence'/name,'Exact existing actual source Hair geometry/UV/packed-image inspection input; not duplicated.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(Path(r['source']))==sha(G/r['file'])==r['sha256'] for r in stable)
 for t in read(E/'minimum-saved-native-curve-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture under unchanged source-relative sibling layout.')
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['r0136-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0136-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0136* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0136-source/*.blend filter=lfs diff=lfs merge=lfs -text']
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0136*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());unique={r['file']:r for r in reused};integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(p),'file':(M/'r0136-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0136','newProtectedNormalGitWriteObjects':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR135StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One actual native Add/Comb construction with retained original job recovery; giant radial fan visibly rejected. Native point/current-skin root translation edits independently restore, no complete operation. Three unexpected8-knot curves retained; native event replay not reliable. No appearance/natural dynamics/finite/self/continuous contacts/runtime acceptance. All311 prior source metadata, nine unrelated files, working r126 and v43 preserved. Normal full LFS, exact existing input/rights reuse, no pruning/install/server/subagents.'};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0136-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R136_EXACT_ONE_COMPLETE_NATIVE_GROOM_SOURCE_ARCHIVE_READY',len(set(allow)),sum(p.stat().st_size for p in sources),len(unique),flush=True)
if __name__=='__main__':main()
