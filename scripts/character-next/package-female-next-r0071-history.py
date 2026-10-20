"""Archive exact rejected sources/evidence and the complete-character review."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0071-hair-scattering';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0071.visual-audit.json');assert not audit['adoptedModel'] and not audit['appearanceImprovement']
    assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip()
    files=[];allow=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for row in audit['studies'].values():
        src=Path(row['source']);assert sha(src)==row['sha256'];copy(src,M/src.name)
    for name in ('aevrynd-female-next-r0071-authoring.json','aevrynd-female-next-r0071.LICENSE-SOURCE.txt'):copy(S/name,M/name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt') and p.name not in ('history-readback.json','history-readback.log','history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0071-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0071*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'independent-readback.json')['studies'][0]['externalTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert sha(p)==row['sha256']
    reused=[]
    for n in ('aevrynd-female-next-r0069-a-complete-controls-study.blend','aevrynd-female-next-r0068-c-live-body-contact-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'):
        p=M/n;assert sha(p)==sha(S/n);reused.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Unchanged existing source; not a new r71 candidate.'})
    for relative,source in [('r0068-c-guide-face.png',E.parent/'r0068-guide-structure/c-guide-face.png'),('r0068-c-guide-body-face.png',E.parent/'r0068-guide-structure/c-guide-body-face.png'),('r0069-a-control-face.png',E.parent/'r0069-complete-controls/a-control-face.png'),('r0069-a-control-body-face.png',E.parent/'r0069-complete-controls/a-control-body-face.png')]:
        p=M/relative;assert sha(p)==sha(source);reused.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Existing equal-condition whole-character neutral comparison; explicitly reused.'})
    attr=M/'.gitattributes';content=attr.read_text(encoding='utf8');header='# Exact r71 rejected material trials and whole-character review.'
    if header not in content:attr.write_text(content.rstrip()+'\n'+header+'\nr0071-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0071* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0071-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());p=REPO/'scripts/character-next/.gitattributes';text=p.read_text(encoding='utf8');rule='*female-next-r0071*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:p.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(p.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactSourcesAndEvidence':reused,'sharedTexturesVerifiedWithoutRecopy':15,'bothRejectedWholeActorBlendSourcesArchived':True,'activeCompleteSourceRemainsR69':True,'formalRuntimeOrWebsitePromoted':False,'sourceRightsNotice':'aevrynd-female-next-r0071.LICENSE-SOURCE.txt','stagnationReset':False,'newSoftwareOrVendorRuntimeImported':False}
    p=M/'r0071-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle)
    for name in ('history-readback.json','history-readback.log'):allow.append((M/('r0071-'+name)).relative_to(REPO).as_posix())
    p=M/'r0071-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record)
    print('R71_EXACT_HISTORY_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
