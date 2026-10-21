"""Exact complete r102 source, original failed premise and scoped evidence."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0102-facet-aware-lid-surface';OLD=E.parent/'r0101-articulated-eyelid-topology';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip(),'Protect staged production'
 allow=[];files=[];lfs=[];reused=[]
 def archive(src,dst):
  assert src.is_file() and src.stat().st_size<900*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ['.blend','.png','.npz','.npy','.gif'];digest=sha(src)
  if dst.exists() and immutable:assert sha(dst)==digest
  elif dst.exists():shutil.copyfile(src,dst)
  elif immutable:os.link(src,dst)
  else:shutil.copyfile(src,dst)
  assert sha(dst)==digest;rel=dst.relative_to(REPO).as_posix();allow.append(rel);row={'file':rel,'bytes':src.stat().st_size,'sha256':digest,'source':str(src),'immutableHardlink':immutable};files.append(row)
  if src.stat().st_size>=50*1024*1024:assert src.suffix.lower() in ['.blend','.npz'];lfs.append(row)
 audit=read(E/'female-next-r0102.visual-audit.json');source=audit['source'];p=Path(source['source']);assert sha(p)==source['sha256'];archive(p,M/p.name)
 for name in ['aevrynd-female-next-r0102-authoring.json','aevrynd-female-next-r0102.LICENSE-SOURCE.txt']:archive(S/name,M/name)
 skip={'history-allowlist.json','history-copy-integrity.json','history-bundle.json','github-receipt.json','staged-verification.json','lfs-progress.log'}
 for p in sorted(E.iterdir()):
  if p.is_file() and p.suffix in ['.json','.npz','.npy','.png','.gif','.log','.py','.txt'] and p.name not in skip:archive(p,M/('r0102-'+p.name))
 for p in sorted((R/'scripts/character-next').glob('*female-next-r0102*.py')):archive(p,REPO/'scripts/character-next'/p.name)
 archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
 for row in read(E/'minimum-saved-readback.json')['externalTextures']:
  rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256'];reused.append({'file':(M/rel).relative_to(REPO).as_posix(),'sha256':row['sha256']})
 refs=[(Path(read(E/'before.json')['source']['source']),M/Path(read(E/'before.json')['source']['source']).name)]
 for name in ['b-anatomical-lid-lineage.npz','b2-lash-root-bindings.json','evaluated-blink-and-contact.json','b-build-summary.json','b2-view-controls.json','b2-independent-view-controls.json','continuation.json','female-next-r0101.visual-audit.json']:refs.append((OLD/name,M/('r0101-'+name)))
 for name in ['build-female-next-r0098-native-head.py','render-female-next-r0091-matched.py','verify-female-next-r0099-saved-motion.py','verify-female-next-r0101-saved-lids.py','make-female-next-r0101-boards.py']:refs.append((R/'scripts/character-next'/name,REPO/'scripts/character-next'/name))
 for src,dst in refs:assert sha(src)==sha(dst),str(dst);reused.append({'file':dst.relative_to(REPO).as_posix(),'sha256':sha(src)})
 attr=M/'.gitattributes';text=attr.read_text('utf-8');rules=['# Exact r102 adaptive finite-lining history; no complete/runtime adoption.','r0102-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0102* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0102-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']+[Path(row['file']).name+' filter=lfs diff=lfs merge=lfs -text' for row in lfs]
 for rule in rules:
  if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text('utf-8');rule='*female-next-r0102*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
 if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
 attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
 integrity={'status':'EXACT_COMPLETE_SOURCE_AND_SCOPED_SAMPLED_FACET_EVIDENCE','files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'allSourceArchiveBytesEqual':True,'immutableSourcesHardlinkedAndMutableRecordsCopied':True,'completeSourcePerFileBudgetBytes':900*1024*1024,'scope':'One construction, failed initial static-optical premise preserved. Actual5 sampled skin/optical surface checks clear,31 interpolation criterion residual faces retained; no whole appearance/operation/global finite/self/continuous/runtime adoption.','normalFullLFSRequired':True};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0102-history-copy-integrity.json');bundle={'schema':1,'decision':audit['decision'],'files':files.copy(),'lfsSources':lfs,'reusedInputs':reused,'completeCharacterGain':False,'retainedWorkingSource':audit['workingCompleteWomanReference'],'adoptedCompleteOperationNaturalDynamicsContactsRuntimeOrWebsite':False,'rights':read(S/'aevrynd-female-next-r0102-authoring.json')['rights']};save(E/'history-bundle.json',bundle);save(M/'r0102-history-bundle.json',bundle);allow.append((M/'r0102-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0102-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow)),'lfsFiles':[row['file'] for row in lfs]};save(p,record);save(E/'history-allowlist.json',record);print('R102_EXACT_HISTORY',len(record['files']),'files',sum(row['bytes'] for row in files),'logical bytes;',len(lfs),'LFS blobs')
if __name__=='__main__':main()
