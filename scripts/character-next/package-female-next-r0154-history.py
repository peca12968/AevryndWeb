from pathlib import Path
import json,hashlib,os,shutil,zipfile
R=Path('D:/Download/Aevrynd');G=R/'sites-engine-journey';E=R/'Evidence/character-female-next/r0154-native-scalp-rest';S=R/'engine/assets/characters/female-next/source';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
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
 b=read(E/'rejected-component-source.json');cp(Path(b['source']),M/'r0154-source'/Path(b['source']).name,True)
 for name in ['aevrynd-female-next-r0154-authoring.json','LICENSE-female-next-r0154.txt']:cp(S/name,M/name)
 cp(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for p in sorted(E.iterdir()):
  if p.is_file() and p.name not in ['history-copy-integrity.json','history-allowlist.json','github-receipt.json','completion-resource-receipt.json']:cp(p,G/'evidence/character-female-next/r0154-native-scalp-rest'/p.name,p.suffix in ['.npz','.png'])
 for name in ['inspect-female-next-r0154-native-scalp-rest.py','author-female-next-r0154-native-scalp-patch.py','preserve-female-next-r0154-failed-component.py','verify-female-next-r0154-failed-component.py','verify-female-next-r0154-mirror-source.py','finalize-female-next-r0154.py','package-female-next-r0154-history.py']:cp(R/'scripts/character-next'/name,G/'scripts/character-next'/name)
 old=read(E.parent/'r0153-current-hairline/history-copy-integrity.json')['reusedInputs'];source153=read(E.parent/'r0153-current-hairline/a-build-summary.json');extra=[{'source':source153['output'],'file':'assets-source/aevrynd-character/female-next/r0153-source/'+Path(source153['output']).name,'sha256':source153['sha256'],'bytes':source153['bytes']}]
 ref=R/'Reference/character/makehuman-hair-editor-cc0'
 for name in ['haireditor.zip','PROVENANCE.json']:extra.append({'source':str(ref/name),'file':'assets-source/aevrynd-character/references/makehuman-hair-editor-cc0/'+name,'sha256':sha(ref/name),'bytes':(ref/name).stat().st_size})
 reused=old+extra
 for x in reused:assert sha(x['source'])==sha(G/x['file'])==x['sha256']
 with zipfile.ZipFile(ref/'haireditor.zip') as z:member=z.read('hair/haireditor/hair.blend');assert hashlib.sha256(member).hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5'
 attrs=G/'.gitattributes'
 if b'/r0154-source/' not in attrs.read_bytes():attrs.write_bytes(attrs.read_bytes()+b'assets-source/aevrynd-character/female-next/r0154-source/aevrynd-female-next-r0154-rejected-scalp-component.blend filter=lfs diff=lfs merge=lfs -text\nevidence/character-female-next/r0154-native-scalp-rest/** -filter -diff -merge -text\n')
 paths.append('.gitattributes');save(E/'history-copy-integrity.json',{'files':records,'reusedInputs':reused,'expectedCommitParent':'003f2f0cea307ecbd9190c7379b854e08b65d539','newSourceRole':'FAILED_BAKED_COMPONENT_DIAGNOSTIC_ZERO_COMPLETE_HAIRSTYLE_CANDIDATES','originalArtistBlendRecoverableFromPreservedFullZipMember':{'archive':str(ref/'haireditor.zip'),'member':'hair/haireditor/hair.blend','bytes':len(member),'sha256':hashlib.sha256(member).hexdigest()},'noRepeatOriginalAssetOrLibraryCopy':True});cp(E/'history-copy-integrity.json',G/'evidence/character-female-next/r0154-native-scalp-rest/history-copy-integrity.json');save(E/'history-allowlist.json',paths+['evidence/character-female-next/r0154-native-scalp-rest/history-allowlist.json']);cp(E/'history-allowlist.json',G/'evidence/character-female-next/r0154-native-scalp-rest/history-allowlist.json')
 cache=R/'.character-lfs-r0154/objects'/b['sha256'][:2]/b['sha256'][2:4]/b['sha256'];cache.parent.mkdir(parents=True,exist_ok=True)
 if not cache.exists():os.link(Path(b['source']),cache)
 assert sha(cache)==b['sha256'];print(json.dumps({'paths':len(paths),'reused':len(reused),'newCompleteCandidate':False,'diagnosticFullLFSBytes':b['bytes']}))
if __name__=='__main__':main()
