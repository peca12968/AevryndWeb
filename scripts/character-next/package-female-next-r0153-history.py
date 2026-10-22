from pathlib import Path
import json,hashlib,shutil,os
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';E=R/'Evidence/character-female-next/r0153-current-hairline';S=R/'engine/assets/characters/female-next/source';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 paths=[];records=[]
 def cp(src,dst,hard=False):
  dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():
   if hard:os.link(src,dst)
   else:shutil.copyfile(src,dst)
  elif not os.path.samefile(src,dst):shutil.copyfile(src,dst)
  assert sha(src)==sha(dst);rel=dst.relative_to(G).as_posix();paths.append(rel);records.append({'source':str(src),'file':rel,'sha256':sha(src),'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
 b=read(E/'a-build-summary.json');cp(Path(b['output']),M/'r0153-source'/Path(b['output']).name,True)
 for name in ['aevrynd-female-next-r0153-authoring.json','LICENSE-female-next-r0153.txt']:cp(S/name,M/name)
 cp(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']:cp(p,G/'evidence/character-female-next/r0153-current-hairline'/p.name,p.suffix in ['.png','.npz'])
 for name in ['author-female-next-r0153-current-hairline.py','build-female-next-r0153-current-hairline.py','verify-female-next-r0153-shared-current-source.py','verify-female-next-r0153-mirror-source.py','finalize-female-next-r0153.py','package-female-next-r0153-history.py']:cp(R/'scripts/character-next'/name,G/'scripts/character-next'/name)
 reused=read(E.parent/'r0152-layered-groom/history-copy-integrity.json')['reusedInputs'];extra={'source':b['source'],'file':'assets-source/aevrynd-character/female-next/r0152-source/'+Path(b['source']).name,'sha256':b['sourceSha256'],'bytes':Path(b['source']).stat().st_size};reused=list(reused)+[extra]
 for x in reused:assert sha(x['source'])==sha(G/x['file'])==x['sha256']
 attrs=G/'.gitattributes';line=b'assets-source/aevrynd-character/female-next/r0153-source/aevrynd-female-next-r0153-a-current-hairline.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0153-current-hairline/** -filter -diff -merge -text\n'
 if b'/r0153-source/' not in attrs.read_bytes():attrs.write_bytes(attrs.read_bytes()+line)
 paths.append('.gitattributes');save(E/'history-copy-integrity.json',{'files':records,'reusedInputs':reused,'expectedCommitParent':'fca309a04f9a3e7c9f89df16f01e0bfa18858e10','sharedLibrarySourcePreservedNotDuplicated':True,'newFullWomanSceneIsLibraryDependentNotStandaloneSingleBlob':True});cp(E/'history-copy-integrity.json',G/'evidence/character-female-next/r0153-current-hairline/history-copy-integrity.json');save(E/'history-allowlist.json',paths+['evidence/character-female-next/r0153-current-hairline/history-allowlist.json']);cp(E/'history-allowlist.json',G/'evidence/character-female-next/r0153-current-hairline/history-allowlist.json')
 cache=R/'.character-lfs-r0153/objects'/b['sha256'][:2]/b['sha256'][2:4]/b['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():os.link(Path(b['output']),cache)
 assert sha(cache)==b['sha256'];print(json.dumps({'paths':len(paths),'reused':len(reused),'newLFSBytes':cache.stat().st_size}))
if __name__=='__main__':main()
