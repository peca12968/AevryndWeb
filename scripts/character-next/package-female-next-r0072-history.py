"""Exact rejected complete form study plus pinned original CC0 sculpt inputs."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0072-craniofacial-form';S=R/'engine/assets/characters/female-next/source';D=R/'Reference/character/charmorph-vitruvian-cc0/r0072-facial-form';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next';I=M/'source-inputs/r0072-cc0-facial-form'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0072.visual-audit.json');assert not audit['adoptedModel'] and not audit['appearanceImprovement'];assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();files=[];allow=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    src=Path(audit['source']);assert sha(src)==audit['sourceSha256'];copy(src,M/src.name)
    for name in ('aevrynd-female-next-r0072-authoring.json','aevrynd-female-next-r0072.LICENSE-SOURCE.txt'):copy(S/name,M/name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt','.npz') and p.name not in ('history-readback.json','history-readback.log','history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0072-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0072*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    for row in read(D/'PROVENANCE.json')['files']:
        src=D/row['path'];assert sha(src)==row['sha256'];copy(src,I/row['path'])
    copy(D/'PROVENANCE.json',I/'PROVENANCE.json')
    for name in ('Default.npy','config.yaml','README.md'):copy(D.parent/name,I/name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'independent-readback.json')['externalTextures']:
        assert sha(M/row['relative'].replace('\\','/').removeprefix('//'))==row['sha256']
    reused=[]
    for n in ('aevrynd-female-next-r0069-a-complete-controls-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'):
        p=M/n;assert sha(p)==sha(S/n);reused.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Unchanged active complete character or scoped verified fallback.'})
    for view in ('face','body-face','oblique','profile','back','alternate-oblique'):
        p=M/('r0069-a-control-'+view+'.png');src=E.parent/'r0069-complete-controls'/('a-control-'+view+'.png');assert sha(p)==sha(src);reused.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Existing same-condition baseline image, explicitly reused.'})
    attr=M/'.gitattributes';content=attr.read_text(encoding='utf8');header='# Exact r72 rejected form study and native sculpt evidence.'
    if header not in content:attr.write_text(content.rstrip()+'\n'+header+'\nr0072-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0072* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0072-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());p=I/'.gitattributes';p.write_text('# Preserve publisher data/whitespace byte-for-byte; do not trim original inputs.\n* -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n');allow.append(p.relative_to(REPO).as_posix())
    p=REPO/'scripts/character-next/.gitattributes';text=p.read_text(encoding='utf8');rule='*female-next-r0072*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:p.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(p.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactEvidence':reused,'sharedTexturesVerifiedWithoutRecopy':15,'rejectedCompleteBlendSourceArchived':True,'sourceRightsNotice':'aevrynd-female-next-r0072.LICENSE-SOURCE.txt','newSculptDataLicense':'CC0, pinned author config and full credits included; hairstyle remains separately Bystedt CC BY-SA version unspecified.','sourcePresetFilesAreInspectedInputsNotAdoptedRecipes':True,'noEmilyAssetsCodeOrReferenceImagesImported':True,'activeCharacterRemainsR69':True,'formalRuntimeOrWebsitePromoted':False,'wholeCharacterStagnationReset':False}
    p=M/'r0072-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle)
    for name in ('history-readback.json','history-readback.log'):allow.append((M/('r0072-'+name)).relative_to(REPO).as_posix())
    p=M/'r0072-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());record={'files':sorted(set(allow))};save(p,record);save(E/'history-allowlist.json',record);print('R72_EXACT_HISTORY_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
