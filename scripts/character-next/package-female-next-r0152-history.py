"""Exact two compact full states, one original round and reused full history."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0152-layered-groom';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0151-native-parent-groom'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']);allow=[];files=[];reused=[]
 def archive(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src);immutable=src.suffix in ['.blend','.glb','.png','.gif','.npz']
  if dst.exists() and os.path.samefile(src,dst):assert sha(dst)==h
  elif dst.exists() and immutable:assert sha(dst)==h
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable and src.stat().st_dev==dst.parent.stat().st_dev:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst,role):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst));reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size,'role':role})
 audit=read(E/'female-next-r0152.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==2;full=[]
 for key,row in audit['prototypeSources'].items():
  source=Path(row['source']);assert sha(source)==row['sha256'];archive(source,M/'r0152-source'/source.name);full.append({'source':str(source),'file':(M/'r0152-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':key+' unaccepted complete compact woman in one original round'})
 assert sum(x['bytes'] for x in full)==52901083
 for n in ['aevrynd-female-next-r0152-authoring.json','aevrynd-female-next-r0152.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0152-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0152*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact existing source/dependency/texture/rights/rollback; no duplicate.')
 reuse(R/'scripts/character-next/build-female-next-r0150-authored-locks.py',G/'scripts/character-next/build-female-next-r0150-authored-locks.py','Original generic mathematical curve sampler only; old33 form coordinates not used.')
 for r in read(E/'minimum-independent-current-only-source-readback.json')['results']:
  for t in r['allReferencedExternalTextures']:
   rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Current source relative texture dependency exactly preserved in mirror.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(r['source'])==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0152-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0152-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0152* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0152-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0152*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused}
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':full,'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0152'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR151StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'expectedCommitParent':'030b2d3a4458a70c6649c798c7a0aadb6162fde3','scope':'TWO complete compact152 A/B states,52901083B total, ONE original round. A new16-primary/144 layered guides; initial clustered root failure retained, actual triangle barycentric/UV root repair finite. B one coordinate-field falsification, root0/full paths change but no appearance rescue. Original planned one candidate and original start/deadlines/attempts/costs preserved. Both complete5 views rejected; whole150/151/152 reviewed including4 saved states and failures. Compact source only obsolete COPIED in-memory hidden data removed; all331 original files unchanged. Independent BOTH sources retain all49 original current gaze poses/seven meshes/UVs exactly; actual guide/Skin edits restore0. Full original139/117 rollback remains external and current old artist hair local hidden; no fake embedded117 claim. Current-only source qualified as construction support only, unique working139 unchanged. No-adopt26/cadence0/next3, no score or full operation adoption. No new third-party asset/node adopted, no source/history deletion or formal promotion. Actual render data recorded, no unverified denoise/material cause claim.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0152-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R152_EXACT_TWO_COMPACT_STATES_ONE_ROUND_HISTORY_READY',len(set(allow)),sum(x['bytes'] for x in full),len(unique))
if __name__=='__main__':main()
