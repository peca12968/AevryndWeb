"""Archive the unaccepted coupled skin support and explicit open gates on protected C storage."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0120-ocular-socket-construction';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).strip();allow=[];files=[];reused=[]
    def archive(src,dst):
        immutable=src.suffix in ['.blend','.png','.npz','.gif'];dst.parent.mkdir(parents=True,exist_ok=True);digest=sha(src)
        if dst.exists() and immutable:assert sha(dst)==digest
        elif dst.exists():shutil.copyfile(src,dst)
        elif immutable:os.link(src,dst)
        else:shutil.copyfile(src,dst)
        assert sha(dst)==digest;rel=dst.relative_to(G).as_posix();allow.append(rel);files.append({'source':str(src),'file':rel,'sha256':digest,'bytes':src.stat().st_size,'immutableSameFile':os.path.samefile(src,dst)})
    a=read(E/'female-next-r0120.visual-audit.json');sources=[Path(x['source']) for x in a['prototypeSources'].values()]
    for source in sources:archive(source,M/'r0120-source'/source.name)
    for p in [S/'aevrynd-female-next-r0120-authoring.json',S/'aevrynd-female-next-r0120.LICENSE-SOURCE.txt']:archive(p,M/p.name)
    skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
    for p in sorted(E.rglob('*')):
        if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/'r0120-evidence'/p.relative_to(E))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0120*.py')):archive(p,G/'scripts/character-next'/p.name)
    archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    def reuse(src,dst,role):
        h=sha(src);assert dst.is_file() and sha(dst)==h;reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':h,'bytes':src.stat().st_size,'role':role})
    for t in read(E/'minimum-saved-ocular-unit-readback.json')['allReferencedExternalTextures']:
        rel=t['relative'].replace('\\','/');assert rel.startswith('//../');reuse(Path(t['absolute']),M/rel[5:],'Complete shared texture, original bytes; no redundant local texture copy.')
    w=a['workingCompleteWomanReference'];p=Path(w['source']);reuse(p,M/p.relative_to(S),'Unchanged r117 working woman with adopted static neck/brow gains.')
    for row in read(E.parent/'r0113-coherent-head-foundation/history-copy-integrity.json')['files']:
        if row['file'].startswith('assets-source/aevrynd-character/female-next/source-inputs/r0113-makehuman-core/'):
            reuse(Path(row['source']),G/row['file'],'Full pinned native body/targets/license/provenance used, already archived.')
    p=E.parent/'r0113-coherent-head-foundation/coherent-native-head-b.json';reuse(p,M/'r0113-coherent-native-head-b.json','Exact existing native morphology/world staging metadata.')
    for n in ['build-female-next-r0119-anatomical-eyes.py','build-female-next-r0116-native-eye-character.py','build-female-next-r0113-native-neck-character.py','finalize-female-next-r0111.py','verify-female-next-r0037-eye-margin.py']:reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Exact existing direct rendering or unchanged intersection routine.')
    for row in read(E.parent/'r0116-native-compatible-eyes/history-copy-integrity.json')['files']:
        if row['file'].startswith('assets-source/aevrynd-character/female-next/source-inputs/r0116-native-eyes/'):
            reuse(Path(row['source']),G/row['file'],'Complete original native eye source/texture/license/provenance reused.')
    for n in ['native-eye-source-lineage.npz','native-eye-source-authoring.json']:
        reuse(E.parent/'r0116-native-compatible-eyes'/n,M/('r0116-'+n),'Exact original native iris correspondence/actual source data used by B.')
    reuse(E.parent/'r0119-anatomical-eye-rebuild/b-anatomical-eye-assembly-lineage.npz',M/'r0119-b-anatomical-eye-assembly-lineage.npz','Exact fixed eye assembly used by source/readback.')
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');rules=['# Exact r117 native brow working source, original sources and scoped evidence.','r0120-evidence/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0120-evidence/*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','r0120-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0120* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0120-source/*.blend filter=lfs diff=lfs merge=lfs -text','r0120-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol','makehuman-native-brow-textures/* -text']
    for rule in rules:
        if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0120*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
    integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(source),'file':(M/'r0120-source'/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size} for source in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0120','scope':'One unaccepted complete coupled ocular skin/closure source, fixed r119 eye geometry, all281 older sources and r117 working gains retained. Neutral queried cornea/iris/ciliary pairs have0 BVH candidates; actual sclera stores4/8 capped intersection-or-touch witnesses, not a global penetration count or continuous/finite proof. No adopted appearance/new complete operation. Three no-adopt rounds trigger relevant foundation change next. Evidence and archive are separate protected C directories behind canonical D junctions; immutable media linked on C and mutable metadata copied separately. Full normal LFS source on C, no history deletion or incomplete object.'}

    previous=read(E.parent/'r0119-anatomical-eye-rebuild/history-copy-integrity.json')
    stable=[row for row in previous['files'] if row['file']!='assets-source/aevrynd-character/female-next/female-next.asset.json']
    assert all(sha(Path(row['source']))==row['sha256'] and sha(G/row['file'])==row['sha256'] for row in stable)
    rolling=[row for row in previous['files'] if row['file']=='assets-source/aevrynd-character/female-next/female-next.asset.json'];assert len(rolling)==1
    assert sha(E/'manifest-before.json')==rolling[0]['sha256']==sha(M/'r0120-evidence/manifest-before.json')
    committed=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+rolling[0]['file']]);assert hashlib.sha256(committed).hexdigest()==rolling[0]['sha256']
    integrity['allPriorR119StableSourceAndArchiveRecordsStillExact']=len(stable)
    integrity['priorRollingManifestExactBeforeSnapshotAndCommittedBlobPreserved']=True
    save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0120-evidence/history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R120_FULL_EXACT_ARCHIVE_READY',len(set(allow)),source.stat().st_size,flush=True)
if __name__=='__main__':main()
