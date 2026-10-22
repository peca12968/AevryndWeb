"""Exact one-woman history; small native guide component is ordinary full Git data."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0148-native-groom-foundation';M=G/'assets-source/aevrynd-character/female-next';PRE=E.parent/'r0147-outer-lid-surface'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
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
 audit=read(E/'female-next-r0148.visual-audit.json');assert not audit['appearanceImprovement'] and len(audit['prototypeSources'])==1;source=Path(audit['prototypeSources']['a']['source']);assert source.stat().st_size==142073336;archive(source,M/'r0148-source'/source.name)
 for n in ['aevrynd-female-next-r0148-authoring.json','aevrynd-female-next-r0148.LICENSE-SOURCE.txt']:archive(S/n,M/n)
 skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log','full-lfs-storage-preparation.json'}
 for p in sorted(E.rglob('*')):
  if p.is_file() and p.name not in skip:archive(p,M/'r0148-evidence'/p.relative_to(E))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0148*.py')):archive(p,G/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json');old=read(PRE/'history-copy-integrity.json')
 for r in old['reusedInputs']:reuse(Path(r['source']),G/r['file'],'Exact inherited dependency/source/rights/texture/rollback already archived; no duplicate.')
 reuse(R/'scripts/character-next/build-female-next-r0138-native-current-gaze.py',G/'scripts/character-next/build-female-next-r0138-native-current-gaze.py','Exact actual working mesh/rig and matched-render helper, not a build rerun.')
 reuse(E.parent/'r0130-artist-native-groom/current-hair-native-triangle-charts.npz',M/'r0130-evidence/current-hair-native-triangle-charts.npz','Exact current artist hair geometry/UV/topology input; world/triangles independently checked against r139. Not a whole-source medial/isocontour recipe.')
 for t in read(E/'minimum-independent-local-tress-readback.json')['allReferencedExternalTextures']:
  rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Exact original texture, unchanged relative path.')
 stable=[r for r in old['files'] if r['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert all(sha(r['source'])==sha(G/r['file'])==r['sha256'] for r in stable)
 rolling=next(r for r in old['files'] if r['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json');assert sha(E/'manifest-before.json')==rolling['sha256'];assert hashlib.sha256(subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling['file']])).hexdigest()==rolling['sha256']
 for attr,rules in [(M/'.gitattributes',['r0148-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0148-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','aevrynd-female-next-r0148* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0148-source/*.blend filter=lfs diff=lfs merge=lfs -text']),(G/'scripts/character-next/.gitattributes',['*female-next-r0148*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'])]:
  text=attr.read_text('utf-8')
  for rule in rules:
   if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
  attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
 unique={r['file']:r for r in reused};component=E/'local-clump-guide-component.blend'
 integrity={'files':files,'reusedInputs':list(unique.values()),'fullSources':[{'source':str(source),'file':(M/'r0148-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size,'role':'One complete unaccepted local native tress woman'}],'smallNativeGuideComponent':{'source':str(component),'file':(M/'r0148-evidence'/component.name).relative_to(G).as_posix(),'sha256':sha(component),'bytes':component.stat().st_size,'ordinaryCompleteGitBinaryNotLFSRequired':True,'notASecondCompleteWoman':True},'normalFullLFSRequired':True,'perCommandLFSStorage':str(R/'.character-lfs-r0148'),'newProtectedNormalGitWriteObjects':str(R/'.character-git-r0145/objects'),'olderProtectedNormalGitObjectsOnC':'C:/Users/USER/AevryndCharacterGitObjects','originalGitReadObjects':str(G/'.git/objects'),'allPriorR147StableRecordsStillExact':len(stable),'priorRollingManifestExactSnapshotAndCommittedBlobPreserved':True,'scope':'One original r148 round and142073336B full woman; one170082B guide-only library is ordinary full Git binary, not another candidate. Complete local6-piece surface-to-native-fibre reconstruction rejected for crown joins/ribbon/back fragment. Actual strand edit/restore0 verified; construction guides not live/follicles. Original failed UV bounding-box attempt and79.798649s support overrun preserved; original preview deadline met. Bystedt role/right inspection reference-only, no unqualified external asset adopted. Original327 sources/nine unrelated files/V47/r139 working/development exact. No-adopt22/cadence2/next1; next whole review147/148/149 due, last144/145/146 unchanged. No variants/broad audits/runtime promotion after visual rejection.'}
 save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0148-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R148_EXACT_ONE_WOMAN_AND_SMALL_GUIDE_COMPONENT_HISTORY_READY',len(set(allow)),source.stat().st_size,len(unique))
if __name__=='__main__':main()
