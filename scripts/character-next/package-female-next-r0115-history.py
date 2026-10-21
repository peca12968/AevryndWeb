"""Full source checkpoints on C-backed canonical/archive mounts, exact ordinary evidence and reused inputs."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0115-native-continuous-neck';G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
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
    a=read(E/'female-next-r0115.visual-audit.json');sources=[Path(x['source']) for x in a['prototypeSources'].values()]
    for p in sources:
        dst=M/'r0115-source'/p.name;assert dst.is_file() and os.path.samefile(p,dst);archive(p,dst)
    for p in [S/'aevrynd-female-next-r0115-authoring.json',S/'aevrynd-female-next-r0115.LICENSE-SOURCE.txt']:archive(p,M/p.name)
    skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
    for p in sorted(E.rglob('*')):
        if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/('r0115-'+p.relative_to(E).as_posix().replace('/','__')))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0115*.py')):archive(p,G/'scripts/character-next'/p.name)
    archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    def reuse(src,dst,role):
        h=sha(src);assert dst.is_file() and sha(dst)==h;reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':h,'bytes':src.stat().st_size,'role':role})
    for t in read(E/'minimum-saved-continuous-readback.json')['externalTextures']:
        rel=t['relative'].replace('\\','/');assert rel.startswith('//../');rel=rel[5:];dst=M/rel;reuse(Path(t['absolute']),dst,'Complete existing shared texture; new nested sources use ../ relative paths.')
    w=a['previousWorkingCompleteWomanReference'];reuse(Path(w['source']),M/Path(w['source']).name,'Immutable previous complete working rollback, preserved full source.')
    pre=E.parent/'r0113-coherent-head-foundation'
    for row in read(pre/'history-copy-integrity.json')['files']:
        if row['file'].startswith('assets-source/aevrynd-character/female-next/source-inputs/r0113-makehuman-core/'):
            reuse(Path(row['source']),G/row['file'],'Complete pinned original native mesh/targets/license/provenance reused, no asset download/duplication.')
    for n in ['coherent-native-head-b.json','whole-head-b-source-correspondence.npz','b-mobile-lash-bindings.json']:reuse(pre/n,M/('r0113-'+n),'Original native staging/source identity and baseline fibres.')
    for n in ['build-female-next-r0113-native-neck-character.py','author-female-next-r0113-native-neck.py','finalize-female-next-r0111.py']:reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Existing exact direct script dependency.')
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');rules=['# Exact r115 continuous native sources and scoped static appearance evidence.','r0115-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0115* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','r0115-source/*.blend filter=lfs diff=lfs merge=lfs -text','r0115-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']
    for rule in rules:
        if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix());attr=G/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0115*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
    integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(p),'file':(M/'r0115-source'/p.name).relative_to(G).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'perCommandLFSStorage':'C:/Users/USER/.cache/aevrynd-character-lfs-r0115','canonicalAndArchiveSourceMountsHaveSameDepthAndSharedTextureLayout':True,'scope':'One production round, one original connected-native-skin construction, two actual complete candidates A wrong closed Basis and repaired B; original capacity checkpointA0 is not another candidate. Adopt only actual complete neutral neck/shoulder appearance gain. All other gates/score/formal runtime/user acceptance remain unaccepted. Preserve all full failures, all fibres/radii, old273 sources, previous working rollback and rights. Contact broad phase emitted only shared neighbours, zero actual non-neighbour narrow tests, no global/finite/continuous claim.'}
    save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0115-history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)));print('R115_EXACT_ARCHIVE_READY',len(set(allow)),len(sources),sum(p.stat().st_size for p in sources),flush=True)
if __name__=='__main__':main()
