"""Archive rejected skin studies once, reusing immutable bytes and readback evidence."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0073-complete-skin'
REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0073.visual-audit.json');assert not audit['adoptedModel']
    assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip()
    files=[];allow=[]
    def archive(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024
        dst.parent.mkdir(parents=True,exist_ok=True)
        immutable=src.suffix.lower() in ('.blend','.exr','.png','.npz')
        if dst.exists() and immutable:assert sha(src)==sha(dst),str(dst)
        elif dst.exists():shutil.copyfile(src,dst)
        elif immutable:os.link(src,dst)
        else:shutil.copyfile(src,dst)
        a=sha(src);assert a==sha(dst)
        rel=dst.relative_to(REPO).as_posix();allow.append(rel)
        files.append({'file':rel,'bytes':src.stat().st_size,'sha256':a,'source':str(src),'immutableHardlink':immutable})
    for t,row in audit['studies'].items():
        src=Path(row['source']);assert sha(src)==row['sha256'];archive(src,M/src.name)
        check=read(E/(t+'-independent-readback.json'))
        assert check['sha256']==row['sha256'] and check['status'].startswith('PASS_SAVED_SOURCE_MASKS')
        for image in check['externalTextures']:
            rel=image['relative'].replace('\\','/').removeprefix('//');src=S/rel;dst=M/rel
            assert sha(src)==image['sha256']
            if not dst.exists():archive(src,dst)
            assert sha(dst)==image['sha256']
    originals=read(E/'b-independent-readback.json')['original4kSourceBytesChecked'];assert len(originals)==12
    for image in originals:
        src=S/'study-vitruvian-textures-source4k'/image['file'];assert sha(src)==image['sha256']
        archive(src,M/'study-vitruvian-textures-source4k'/image['file'])
    for n in ('aevrynd-female-next-r0073-authoring.json','aevrynd-female-next-r0073.LICENSE-SOURCE.txt'):archive(S/n,M/n)
    excluded={'history-bundle.json','history-allowlist.json','history-copy-integrity.json','github-receipt.json'}
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt','.npz') and p.name not in excluded:archive(p,M/('r0073-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0073*')):
        if p.suffix in ('.py','.ps1'):archive(p,REPO/'scripts/character-next'/p.name)
    archive(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for name in ('config.yaml','README.md'):archive(R/'Reference/character/charmorph-vitruvian-cc0'/name,M/'source-inputs/r0073-cc0-source'/name)
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');marker='# Exact r73 rejected source skin and original texture evidence.'
    if marker not in text:attr.write_text(text.rstrip()+'\n'+marker+'\nr0073-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0073* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0073-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nstudy-vitruvian-textures-source4k/*.exr -text\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    attr=M/'source-inputs/r0073-cc0-source/.gitattributes';attr.write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
    attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8')
    for ext in ('.py','.ps1'):
        rule='*female-next-r0073*'+ext+' -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
        if rule not in text:text=text.rstrip()+'\n'+rule+'\n'
    attr.write_text(text,encoding='utf8',newline='\n');allow.append(attr.relative_to(REPO).as_posix())
    integrity={'status':'PASS_EXACT_BINARY_AND_DEPENDENCY_COPY_HASHES','files':files,'savedModelReadbackReused':['a-independent-readback.json','b-independent-readback.json'],'newBlenderReadbackUnnecessaryBecauseCopiedBlendAndAllResolvedImageBytesExact':True,'noAppearanceContactMotionOrRuntimeAcceptance':True}
    save(E/'history-copy-integrity.json',integrity);archive(E/'history-copy-integrity.json',M/'r0073-history-copy-integrity.json')
    bundle={'schema':1,'decision':audit['decision'],'files':files,'activeCharacterRemainsR69':True,'formalRuntimeOrWebsitePromoted':False,'wholeCharacterStagnationReset':False,'sourceRightsNotice':'aevrynd-female-next-r0073.LICENSE-SOURCE.txt','mapDataLicense':'CC0 source declaration/credits included; hairstyle separately Bystedt CC BY-SA version unspecified.','sourceReadbackEvidenceReusedForIdenticalArchiveBytes':True}
    save(E/'history-bundle.json',bundle);save(M/'r0073-history-bundle.json',bundle);allow.append((M/'r0073-history-bundle.json').relative_to(REPO).as_posix())
    p=M/'r0073-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record)
    print('R73_EXACT_ARCHIVE',len(record['files']),'files',sum(x['bytes'] for x in files),'bytes; identical sources not rerendered.')
if __name__=='__main__':main()
