"""Exact r155 history, immutable full sources and dependency references."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';E=R/'Evidence/character-female-next/r0155-native-blink';S=R/'engine/assets/characters/female-next/source';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert not (E/'history-copy-integrity.json').exists(),'Reconcile existing archive before any repeat'
 paths=[];records=[];additional=[]
 def cp(src,dst,immutable=False):
  dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():
   if immutable:os.link(src,dst)
   else:shutil.copyfile(src,dst)
  elif not os.path.samefile(src,dst):shutil.copyfile(src,dst)
  assert sha(src)==sha(dst);rel=dst.relative_to(G).as_posix();paths.append(rel);records.append({'source':str(src),'file':rel,'sha256':sha(src),'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 def reuse(src,dst):
  assert src.is_file() and dst.is_file() and sha(src)==sha(dst),(str(src),str(dst))
  additional.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size})
 states=read(E/'continuation.json')['prototypeSources']
 for b in states.values():
  src=Path(b['source']);cp(src,M/'r0155-source'/src.name,True);cache=R/'.character-lfs-r0155/objects'/b['sha256'][:2]/b['sha256'][2:4]/b['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
  if not cache.exists():os.link(src,cache)
  assert sha(cache)==b['sha256']
 for n in ['aevrynd-female-next-r0155-authoring.json','LICENSE-female-next-r0155.txt']:cp(S/n,M/n)
 cp(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']:cp(p,G/'evidence/character-female-next/r0155-native-blink'/p.name,p.suffix in ['.png','.jpg','.npz'])
 for n in ['build-female-next-r0155-native-blink.py','build-female-next-r0155-margin-blink.py','inspect-female-next-r0155-field-driving.py','verify-female-next-r0155-render-evaluation.py','verify-female-next-r0155-current-blink.py','verify-female-next-r0155-fresh-closure.py','verify-female-next-r0155-mirror-source.py','finalize-female-next-r0155.py','package-female-next-r0155-history.py']:cp(R/'scripts/character-next'/n,G/'scripts/character-next'/n)
 prior=E.parent/'r0154-native-scalp-rest/history-copy-integrity.json';priorMirror=G/'evidence/character-female-next/r0154-native-scalp-rest/history-copy-integrity.json';assert sha(prior)==sha(priorMirror)
 inherited=read(prior)['reusedInputs']
 for x in inherited:assert sha(x['source'])==sha(G/x['file'])==x['sha256']
 for n in ['native-lid-follow-construction.json','native-current-lid-skinning.npz','matched-a-native-lid-follow-face.png','matched-a-native-lid-follow-body-face.png']:reuse(E.parent/'r0139-native-lid-follow'/n,M/'r0139-evidence'/n)
 for n in ['matched-a-current-hairline-face.png','matched-a-current-hairline-body-face.png']:reuse(E.parent/'r0153-current-hairline'/n,G/'evidence/character-female-next/r0153-current-hairline'/n)
 for n in ['matched-retained-woman-after-failed-component-face.png','matched-retained-woman-after-failed-component-body-face.png','r0154-root-binding-failure-witness.png']:reuse(E.parent/'r0154-native-scalp-rest'/n,G/'evidence/character-female-next/r0154-native-scalp-rest'/n)
 reuse(R/'scripts/character-next/build-female-next-r0138-native-sockets.py',G/'scripts/character-next/build-female-next-r0138-native-sockets.py')
 for x in read(E/'independent-mirror-source-readback.json')['results'][0]['relativeTexturesWithinArchive']:
  dst=Path(x['file']);src=S/dst.relative_to(M);reuse(src,dst)
 attrs=G/'.gitattributes';mark=b'assets-source/aevrynd-character/female-next/r0155-source/*.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0155-native-blink/** -filter -diff -merge -text\n'
 assert b'/r0155-source/' not in attrs.read_bytes();attrs.write_bytes(attrs.read_bytes()+mark);paths.append('.gitattributes')
 integrity={'files':records,'inheritedInputIntegrity':{'source':str(prior),'file':priorMirror.relative_to(G).as_posix(),'sha256':sha(prior),'verifiedInheritedReusedInputCount':len(inherited)},'additionalReusedInputs':additional,'expectedCommitParent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'newSourceRole':'TWO_COMPLETE_UNACCEPTED_BLINK_STATES_ONE_ACTUAL_ROUND_NO_WORKING_PROMOTION','all19RelatedFailuresAndOriginalContradictoryCapturesPreserved':True,'noRepeatLibraryTextureOrHistoricalSourceCopy':True}
 save(E/'history-copy-integrity.json',integrity);cp(E/'history-copy-integrity.json',G/'evidence/character-female-next/r0155-native-blink/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(paths+['evidence/character-female-next/r0155-native-blink/history-allowlist.json']));cp(E/'history-allowlist.json',G/'evidence/character-female-next/r0155-native-blink/history-allowlist.json')
 eb=sum(p.stat().st_size for p in E.iterdir() if p.is_file());assert eb<6700000,eb
 print(json.dumps({'paths':len(paths),'inherited':len(inherited),'additionalReused':len(additional),'evidenceBytes':eb,'fullSourceBytes':sum(b['bytes'] for b in states.values())}),flush=True)
if __name__=='__main__':main()
