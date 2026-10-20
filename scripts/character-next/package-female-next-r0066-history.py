"""Exact bounded rejected-study archive; never stage other work."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0066-skin-response';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    audit=read(E/'female-next-r0066.visual-audit.json');assert audit['decision']=='REJECT_SKIN_RESPONSE_AS_MAINLINE';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for p in sorted(S.glob('*r0066*')):
        if p.suffix in ('.blend','.json'):copy(p,M/p.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0066-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0066*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'a-native-readback.json')['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    oldrefs=[]
    prior=E.parent/'r0065-eye-shading'
    for name in ('a-eye-face.png','a-eye-body-face.png','a-eye-oblique.png','a-eye-profile.png','a-eye-alternate-oblique.png','a-face-control.json','a-extra-view-controls.json','a-build-summary.json','a-functional-contact-transfer.json'):
        p=M/('r0065-'+name);assert p.exists() and sha(p)==sha(prior/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Exact r65 baseline source, controls/images or bounded ocular verification only.'})
    source=Path(read(E/'a-build-summary.json')['source']);p=M/source.name;assert sha(p)==sha(source);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Complete working woman remains r65; r66 is rejected.'})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r66 bounded source-skin rejection and complete views.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\n'+'r0066-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r0066-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r0066-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0066*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedWithoutRecopy':15,'reusedExactSourceEvidence':oldrefs,'sourceRole':'Rejected complete r66 study only; r65 remains offline working source; formal/r51fallback/runtime/site/female acceptance unchanged.','newExternalAssetsOrCodeImported':False};p=M/'r0066-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0066-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R66_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
