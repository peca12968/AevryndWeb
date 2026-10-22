from pathlib import Path
import os,json,hashlib,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';E=R/'Evidence/character-female-next/r0156-anatomical-blink';S=R/'engine/assets/characters/female-next/source';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert not (E/'history-copy-integrity.json').exists();paths=[];records=[]
 def cp(src,dst,immutable=False):
  dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():
   if immutable:os.link(src,dst)
   else:shutil.copyfile(src,dst)
  elif not os.path.samefile(src,dst):shutil.copyfile(src,dst)
  assert sha(src)==sha(dst);rel=dst.relative_to(G).as_posix();paths.append(rel);records.append({'source':str(src),'file':rel,'sha256':sha(src),'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 b=read(E/'a-build-summary.json');src=Path(b['output']);cp(src,M/'r0156-source'/src.name,True)
 for n in ['aevrynd-female-next-r0156-authoring.json','LICENSE-female-next-r0156.txt']:cp(S/n,M/n)
 cp(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']:cp(p,G/'evidence/character-female-next/r0156-anatomical-blink'/p.name,True)
 for n in ['inspect-female-next-r0156-crossing-lineage.py','inspect-female-next-r0156-visible-lid.py','build-female-next-r0156-anatomical-blink.py','verify-female-next-r0156-minimum-readback.py','finalize-female-next-r0156.py','package-female-next-r0156-history.py']:cp(R/'scripts/character-next'/n,G/'scripts/character-next'/n)
 prev=E.parent/'r0155-native-blink/history-copy-integrity.json';pm=G/'evidence/character-female-next/r0155-native-blink/history-copy-integrity.json';assert sha(prev)==sha(pm);old=read(prev);ancestor=old['inheritedInputIntegrity'];assert sha(ancestor['source'])==sha(G/ancestor['file'])==ancestor['sha256'];inherited=read(ancestor['source'])['reusedInputs']+old['additionalReusedInputs']
 for x in inherited:assert sha(x['source'])==sha(G/x['file'])==x['sha256']
 extras=[]
 for src,dst in [(Path(b['source']),M/'r0155-source'/Path(b['source']).name),(E.parent/'r0155-native-blink/b-build-summary.json',G/'evidence/character-female-next/r0155-native-blink/b-build-summary.json'),(E.parent/'r0155-native-blink/b-independent-crossing-location-witness.json',G/'evidence/character-female-next/r0155-native-blink/b-independent-crossing-location-witness.json'),(E.parent/'r0155-native-blink/b-independently-evaluated-closed-face.png',G/'evidence/character-female-next/r0155-native-blink/b-independently-evaluated-closed-face.png'),(R/'scripts/character-next/build-female-next-r0155-margin-blink.py',G/'scripts/character-next/build-female-next-r0155-margin-blink.py')]:
  assert sha(src)==sha(dst);extras.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size})
 attrs=G/'.gitattributes';assert b'/r0156-source/' not in attrs.read_bytes();attrs.write_bytes(attrs.read_bytes()+b'assets-source/aevrynd-character/female-next/r0156-source/*.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0156-anatomical-blink/** -filter -diff -merge -text\n');paths.append('.gitattributes');save(E/'history-copy-integrity.json',{'files':records,'inheritedInputIntegrity':{'source':str(prev),'file':pm.relative_to(G).as_posix(),'sha256':sha(prev),'inheritedInputReferences':len(inherited),'interpretation':'Reuse only155 inheritedInputIntegrity input list plus155 additionalReusedInputs, not mutable historical file records.'},'additionalReusedInputs':extras,'expectedCommitParent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'newSourceRole':'ONE_UNACCEPTED_COUPLED_LID_FULL_SOURCE_NO_WORKING_PROMOTION','allEvidenceFrozenBeforeHardlinking':True,'noLibraryTextureOrHistoricalSourceDuplicated':True});cp(E/'history-copy-integrity.json',G/'evidence/character-female-next/r0156-anatomical-blink/history-copy-integrity.json',True);save(E/'history-allowlist.json',sorted(paths+['evidence/character-female-next/r0156-anatomical-blink/history-allowlist.json']));cp(E/'history-allowlist.json',G/'evidence/character-female-next/r0156-anatomical-blink/history-allowlist.json',True)
 cache=R/'.character-lfs-r0156/objects'/b['sha256'][:2]/b['sha256'][2:4]/b['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():os.link(Path(b['output']),cache)
 assert sha(cache)==b['sha256'];eb=sum(p.stat().st_size for p in E.iterdir() if p.is_file());assert eb<2300000,eb;print(json.dumps({'paths':len(paths),'inherited':len(inherited),'additional':len(extras),'evidenceBytes':eb,'fullSourceBytes':b['bytes']}),flush=True)
if __name__=='__main__':main()
