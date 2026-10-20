"""Exact failed r64 sources, own atlas data and evidence, no private PDF."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0064-guide-ribbons';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    audit=read(E/'female-next-r0064.visual-audit.json');assert audit['decision']=='REJECT_COMPLETE_CARD_ASSEMBLY_RETAIN_AUTHORING_DATA_FORMAT_ONLY';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for p in sorted(S.glob('*r0064*')):
        if p.suffix in ('.blend','.json'):copy(p,M/p.name)
    for p in sorted((S/'study-r0064-textures').glob('*.png')):copy(p,M/'study-r0064-textures'/p.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0064-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0064*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for x in read(E/'c-native-readback.json')['relativeTextures']:
        p=M/x['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==x['sha256']
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r64 rejected explicit guide/card assembly and own atlas.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\n'+'r0064-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r0064-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r0064-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'+'study-r0064-textures/* -text\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0064*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'referencePDFOrPhotosRedistributed':False,'ownAtlasSource':'texture-female-next-r0064-cards.py','savedShaderTexturesPacked':2,'ownUVFlowSeparatePNG':True,'allThreeSnapshotsRetained':True,'noCharacterRuntimeWebsitePromotion':True};p=M/'r0064-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0064-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R64_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
