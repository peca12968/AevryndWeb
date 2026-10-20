"""Exact bounded rejected-study archive; never stage other work."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0067-native-eve';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    audit=read(E/'female-next-r0067.visual-audit.json');assert audit['decision']=='REJECT_NATIVE_EVE_FREE_SHAFT_CONTACT_FAILURE';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for p in sorted(S.glob('*r0067*')):
        if p.suffix in ('.blend','.json'):copy(p,M/p.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt','.npz') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json','a-converted-eve-data.npz'):copy(p,M/('r0067-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0067*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'b-native-readback.json')['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    oldrefs=[]
    prior=E.parent/'r0065-eye-shading'
    for name in ('a-eye-face.png','a-eye-body-face.png','a-eye-oblique.png','a-eye-profile.png','a-eye-back.png','a-eye-alternate-oblique.png','a-face-control.json','a-extra-view-controls.json','a-build-summary.json','a-functional-contact-transfer.json'):
        p=M/('r0065-'+name);assert p.exists() and sha(p)==sha(prior/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Exact r65 baseline source, controls/images or bounded ocular verification only.'})
    source=Path(read(E/'a-build-summary.json')['source']);p=M/source.name;assert sha(p)==sha(source);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Complete working woman remains r65; r67 is rejected.'})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r67 native Eve full-style trial, radius correction and rejection.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\n'+'r0067-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r0067-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r0067-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0067*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedWithoutRecopy':15,'reusedExactSourceEvidence':oldrefs,'sourceRole':'Rejected complete r67A/B studies; r65 remains working source. Correct native radius/child transfer scope retained; no hair-contact, natural dynamic, runtime or female acceptance.','newSoftwareAddonsOrCodeInstalled':False,'publisherCCBYSALearningBinaryArchived':False,'publisherReferenceKeptSeparateFromEngine':True,'skippedReconstructible':['a-converted-eve-data.npz; recover from saved A']};p=M/'r0067-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0067-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R67_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
