"""Exact bounded archive of opposing-arch and oral-arc prototype and its actual failed-contact evidence."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0075-occlusion-authoring';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next';D=R/'Reference/character/charmorph-vitruvian-cc0/r0075-occlusion-authoring'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0075.visual-audit.json');assert audit['retainedAsCompleteAuthoringPrototype'] and not audit['contactQualified'];assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();files=[];allow=[]
    def archive(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);immutable=src.suffix.lower() in ('.blend','.exr','.png','.gif','.npz')
        if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
        elif dst.exists():shutil.copyfile(src,dst)
        elif immutable:os.link(src,dst)
        else:shutil.copyfile(src,dst)
        value=sha(src);assert sha(dst)==value;rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':src.stat().st_size,'sha256':value,'source':str(src),'immutableHardlink':immutable})
    for row in audit['prototypeSources'].values():
        src=Path(row['source']);assert sha(src)==row['sha256'];archive(src,M/src.name)
    for n in ('aevrynd-female-next-r0075-authoring.json','aevrynd-female-next-r0075.LICENSE-SOURCE.txt'):archive(S/n,M/n)
    for p in sorted(E.rglob('*')):
        if not p.is_file() or p.suffix not in ('.json','.png','.gif','.log','.txt','.npz') or p.name in ('history-bundle.json','history-allowlist.json','github-receipt.json','history-copy-integrity.json'):continue
        rel=p.relative_to(E);archive(p,M/(('r0075-'+p.name) if len(rel.parts)==1 else ('r0075-'+rel.parts[0]+'/'+p.name)))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0075*.py')):archive(p,REPO/'scripts/character-next'/p.name)
    archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'c-independent-operation-and-interarch.json')['externalTextures']:
        rel=row['relative'].replace('\\','/').removeprefix('//');assert sha(S/rel)==sha(M/rel)==row['sha256']
    reused=[]
    for name in ('aevrynd-female-next-r0069-a-complete-controls-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend','aevrynd-female-next-r0074-c-rigid-dentition-controls-study.blend'):
        assert sha(S/name)==sha(M/name);reused.append({'file':(M/name).relative_to(REPO).as_posix(),'sha256':sha(M/name)})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');marker='# Exact r75 opposing-arch and oral-arc evidence.'
    if marker not in text:attr.write_text(text.rstrip()+'\n'+marker+'\nr0075-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0075* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0075-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0075*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());integrity={'status':'PASS_EXACT_ARCHIVE_AND_RELATIVE_DEPENDENCY_HASHES','files':files,'savedReadbackReused':'c-independent-operation-and-interarch.json','identicalSourceAndDependencyBytesMakeRedundantCopiedSourceReadbackUnnecessary':True,'formalRuntimePromotion':False};save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0075-history-copy-integrity.json')
    bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactSources':reused,'sharedTexturesVerifiedWithoutRecopy':15,'workingPrototype':'aevrynd-female-next-r0075-c-coordinated-oral-arc-study.blend','formalRuntimeOrWebsitePromoted':False,'contactFailed':True,'wholeCharacterStagnationReset':False,'sourceRightsNotice':'aevrynd-female-next-r0075.LICENSE-SOURCE.txt'};save(E/'history-bundle.json',bundle);save(M/'r0075-history-bundle.json',bundle);allow.append((M/'r0075-history-bundle.json').relative_to(REPO).as_posix());p=M/'r0075-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R75_EXACT_ARCHIVE',len(record['files']),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
