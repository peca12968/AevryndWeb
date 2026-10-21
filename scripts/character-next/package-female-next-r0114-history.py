"""Exact full rejected source/evidence archive, reusing existing immutable textures/native inputs."""
from pathlib import Path
import json, hashlib, os, shutil, subprocess
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0114-native-neck-transition'
G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    assert not subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only']).strip()
    allow=[];files=[];reused=[]
    def archive(src,dst):
        immutable=src.suffix in ['.blend','.png','.npz','.gif'];dst.parent.mkdir(parents=True,exist_ok=True);h=sha(src)
        if dst.exists() and immutable:assert sha(dst)==h
        elif dst.exists():shutil.copyfile(src,dst)
        elif immutable:os.link(src,dst)
        else:shutil.copyfile(src,dst)
        assert sha(dst)==h;rel=dst.relative_to(G).as_posix();allow.append(rel)
        files.append({'source':str(src),'file':rel,'sha256':h,'bytes':src.stat().st_size,'immutableHardlink':immutable})
    a=read(E/'female-next-r0114.visual-audit.json');source=Path(a['prototypeSources']['a']['source'])
    for p in [source,S/'aevrynd-female-next-r0114-authoring.json',S/'aevrynd-female-next-r0114.LICENSE-SOURCE.txt']:archive(p,M/p.name)
    skip={'history-copy-integrity.json','history-allowlist.json','staged-verification.json','github-receipt.json','completion-resource-receipt.json','lfs-progress.log'}
    for p in sorted(E.rglob('*')):
        if p.is_file() and p.name not in skip and p.suffix in ['.json','.npz','.png','.gif','.log','.py','.blend','.txt']:archive(p,M/('r0114-'+p.relative_to(E).as_posix().replace('/','__')))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0114*.py')):archive(p,G/'scripts/character-next'/p.name)
    archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    def reuse(src,dst,role):
        h=sha(src);assert dst.is_file() and sha(dst)==h
        reused.append({'source':str(src),'file':dst.relative_to(G).as_posix(),'sha256':h,'bytes':src.stat().st_size,'role':role})
    for t in read(E/'minimum-saved-neck-readback.json')['candidate']['externalTextures']:
        rel=t['relative'].replace('\\','/').removeprefix('//');dst=(M/rel).resolve();assert dst.is_relative_to(M.resolve())
        reuse(Path(t['absolute']),dst,'Existing full shared texture, no duplicate copy.')
    w=a['workingCompleteWomanReference'];reuse(Path(w['source']),M/Path(w['source']).name,'Unchanged single working complete woman, not new adoption.')
    pre=E.parent/'r0113-coherent-head-foundation'
    reuse(pre/'whole-head-b-source-correspondence.npz',M/'r0113-whole-head-b-source-correspondence.npz','Exact existing native-head/source IDs used in neck inspection.')
    for row in read(pre/'history-copy-integrity.json')['files']:
        if row['file'].startswith('assets-source/aevrynd-character/female-next/source-inputs/r0113-makehuman-core/'):
            reuse(Path(row['source']),G/row['file'],'Existing complete native input/license/provenance; no re-download or duplication.')
    for n in ['build-female-next-r0113-native-neck-character.py','finalize-female-next-r0111.py']:
        reuse(R/'scripts/character-next'/n,G/'scripts/character-next'/n,'Existing direct script dependency.')
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8')
    rules=['# Exact r114 rejected complete neck source and evidence.','r0114-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','aevrynd-female-next-r0114* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',source.name+' filter=lfs diff=lfs merge=lfs -text','r0114-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol']
    for rule in rules:
        if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
    attr=G/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0114*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf-8',newline='\n');allow.append(attr.relative_to(G).as_posix())
    integrity={'files':files,'reusedInputs':reused,'fullSources':[{'source':str(source),'file':(M/source.name).relative_to(G).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size}],'allSourceArchiveBytesEqual':True,'normalFullLFSRequired':True,'scope':'One actual complete r114 neck candidate rejected: new folds and persistent posterior ledge. Complete source independently reopens, preserved old neutral/own blink and all original fibres/radii. No new complete appearance/operation, contact/runtime acceptance or score change. r113 B working woman retained, historical lower34/cadence1. Existing pinned native inputs/licenses/shared textures fully reused; no new dependencies.'}
    save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0114-history-copy-integrity.json');save(E/'history-allowlist.json',sorted(set(allow)))
    print('R114_EXACT_FULL_SOURCE_ARCHIVE_READY',len(set(allow)),source.stat().st_size,len(reused),flush=True)
if __name__=='__main__':main()
