"""Exact retained eye-material source, evidence and unchanged-source links."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0065-eye-shading';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    audit=read(E/'female-next-r0065.visual-audit.json');assert audit['decision']=='RETAIN_SCOPED_INNER_EYE_MATERIAL_IMPROVEMENT';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for p in sorted(S.glob('*r0065*')):
        if p.suffix in ('.blend','.json'):copy(p,M/p.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.gif','.log') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0065-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0065*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'a-functional-contact-transfer.json')['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    oldrefs=[]
    for name in ('b-contact-verification.json','b-additional-pose-verification.json','b-cavity-volume-verification.json'):
        src=E.parent/'r0060-ocular-assembly'/name;p=M/('r0060-'+name);assert p.exists() and sha(src)==sha(p);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'reuseScope':'Exact corresponding geometry only, as proven by r65 seven-pose hashes; not new continuous/full-character contact acceptance.'})
    for name in ('baseline-cycles-face.png','baseline-cycles-body-face.png'):
        src=E.parent/'r0061-surface-flow-groom'/name;p=M/('r0061-'+name);assert p.exists() and sha(src)==sha(p);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'reuseScope':'Exact r60 source + same Cycles controls; original full-head/body baseline reused.'})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r65 scoped inner-eye material gain and real native blink evidence.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\n'+'r0065-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r0065-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r0065-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0065*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedOnce':15,'reusedExactSourceEvidence':oldrefs,'sourceRole':'Offline complete r65A working candidate with retained r60 anatomical baseline and r51fallback. Not formal/website/runtime or female acceptance.','skippedReconstructible':['48raw a-blink-frames PNGs; actual GIF, controls and reconstruction script retained'],'noForeignAssetsOrCodeImported':True};p=M/'r0065-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0065-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R65_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
