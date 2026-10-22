from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';E=R/'Evidence/character-female-next/r0157-outer-lid-retopology';S=R/'engine/assets/characters/female-next/source';M=G/'assets-source/aevrynd-character/female-next'
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
 b=read(E/'a-build-summary.json');cp(Path(b['output']),M/'r0157-source'/Path(b['output']).name,True)
 for n in ['aevrynd-female-next-r0157-authoring.json','LICENSE-female-next-r0157.txt']:cp(S/n,M/n,True)
 cp(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']:cp(p,G/'evidence/character-female-next/r0157-outer-lid-retopology'/p.name,True)
 for n in ['inspect-female-next-r0157-outer-lid-boundaries.py','author-female-next-r0157-outer-lid-patch.py','build-female-next-r0157-outer-lid-retopology.py','verify-female-next-r0157-current-source.py','finalize-female-next-r0157.py','package-female-next-r0157-history.py']:cp(R/'scripts/character-next'/n,G/'scripts/character-next'/n,True)
 prev=E.parent/'r0156-anatomical-blink/history-copy-integrity.json';pm=G/'evidence/character-female-next/r0156-anatomical-blink/history-copy-integrity.json';assert sha(prev)==sha(pm);x=read(prev);p155=x['inheritedInputIntegrity'];assert sha(p155['source'])==sha(G/p155['file'])==p155['sha256'];old=read(p155['source']);p154=old['inheritedInputIntegrity'];assert sha(p154['source'])==sha(G/p154['file'])==p154['sha256'];reused=read(p154['source'])['reusedInputs']+old['additionalReusedInputs']+x['additionalReusedInputs'];assert len(reused)==205
 for row in reused:assert sha(row['source'])==sha(G/row['file'])==row['sha256']
 src=R/'scripts/character-next/build-female-next-r0156-anatomical-blink.py';dst=G/'scripts/character-next/build-female-next-r0156-anatomical-blink.py';assert sha(src)==sha(dst);extras=[{'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':sha(src),'bytes':src.stat().st_size}]
 attrs=G/'.gitattributes';assert b'/r0157-source/' not in attrs.read_bytes();attrs.write_bytes(attrs.read_bytes()+b'assets-source/aevrynd-character/female-next/r0157-source/*.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0157-outer-lid-retopology/** -filter -diff -merge -text\n');paths.append('.gitattributes');save(E/'history-copy-integrity.json',{'files':records,'inheritedInputIntegrity':{'source':str(prev),'file':pm.relative_to(G).as_posix(),'sha256':sha(prev),'inheritedInputReferences':205,'interpretation':'Recursive immutable dependency lists only; never mutable historical manifest file records.'},'additionalReusedInputs':extras,'expectedCommitParent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'newSourceRole':'PROMISING_UNACCEPTED_OUTER_LID_FORM_WELD_EDIT_AND_CONTACT_FAILURES_RETAINED','allEvidenceAndNewScriptsFrozenBeforeHardlinking':True,'normalCIndexAndLFSStorageReference':str(E/'storage-and-budget-plan.json')});cp(E/'history-copy-integrity.json',G/'evidence/character-female-next/r0157-outer-lid-retopology/history-copy-integrity.json',True);save(E/'history-allowlist.json',sorted(paths+['evidence/character-female-next/r0157-outer-lid-retopology/history-allowlist.json']));cp(E/'history-allowlist.json',G/'evidence/character-female-next/r0157-outer-lid-retopology/history-allowlist.json',True)
 storage=Path(read(E/'storage-and-budget-plan.json')['normalLFSStorage']);cache=storage/'objects'/b['sha256'][:2]/b['sha256'][2:4]/b['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():shutil.copyfile(Path(b['output']),cache)
 assert sha(cache)==b['sha256'];eb=sum(p.stat().st_size for p in E.iterdir() if p.is_file());assert eb<1600000,eb;print(json.dumps({'paths':len(paths),'inherited':205,'additional':1,'evidenceBytes':eb,'fullSourceBytes':b['bytes'],'normalFullLFSObjectOnC':str(cache),'freeD':shutil.disk_usage('D:/').free}),flush=True)
if __name__=='__main__':main()
