"""Exact complete control-study source, data, real frames and failed contact evidence."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0069-complete-controls';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next';D=R/'Reference/character/charmorph-vitruvian-cc0/r0069-rig-data'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0069.visual-audit.json');assert audit['decision']=='RETAIN_COMPLETE_FK_AND_SCALP_FOLLOW_STUDY_PHYSICS_UNACCEPTED';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    source=Path(audit['source']);assert sha(source)==audit['sha256'];copy(source,M/source.name)
    for name in ('aevrynd-female-next-r0069-authoring.json','aevrynd-female-next-r0069.LICENSE-SOURCE.txt'):copy(S/name,M/name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.gif','.log','.txt','.npz','.npy') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0069-'+p.name))
    for p in sorted((E/'a-motion-frames').glob('*.png')):copy(p,M/'r0069-motion-frames'/p.name)
    assert len(list((E/'a-motion-frames').glob('*.png')))==32
    provenance=read(D/'PROVENANCE.json')
    for row in provenance['files']:
        p=D/row['file'];assert sha(p)==row['sha256'];copy(p,M/'r0069-input-data'/row['file'])
    copy(D/'PROVENANCE.json',M/'r0069-input-data/PROVENANCE.json');copy(D.parent/'config.yaml',M/'r0069-input-data/config.yaml');assert sha(D.parent/'config.yaml')==provenance['configSha256']
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0069*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'a-independent-readback.json')['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    oldrefs=[];prior=E.parent/'r0068-guide-structure'
    for name in ('c-guide-face.png','c-guide-body-face.png','c-guide-oblique.png','c-guide-profile.png','c-guide-back.png','c-guide-alternate-oblique.png','c-full-view-controls.json','c-build-summary.json','c-tissue-knot-probe.json','history-readback.json'):
        p=M/('r0068-'+name);assert p.exists() and sha(p)==sha(prior/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Exact previous complete C appearance source/controls, no hair physics acceptance.'})
    for path in ('aevrynd-female-next-r0068-c-live-body-contact-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'):
        p=M/path;assert sha(p)==sha(S/path);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Previous complete appearance study or scoped qualified ocular/anatomy foundation, distinct roles.'})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r69 complete FK/scalp-follow study; head-turn contact fails.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\nr0069-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0069* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0069-motion-frames/** -text\nr0069-input-data/** -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0069-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    original_config_rule='r0069-input-data/config.yaml -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol'
    if original_config_rule not in attr.read_text(encoding='utf8'):attr.write_text(attr.read_text(encoding='utf8').rstrip()+'\n# Preserve the pinned upstream config bytes, including its two whitespace-only lines.\n'+original_config_rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r0069*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedWithoutRecopy':15,'reusedExactEvidence':oldrefs,'sourceRole':'R69 full woman with52 FK bones and sampled render-root following retained as working study. Head-turn tissue contacts FAIL; shoulder skin quality, flexible dynamics, full contacts and runtime unaccepted. R65 scoped foundation and formal r1 unchanged.','sourceLicenseNotice':'aevrynd-female-next-r0069.LICENSE-SOURCE.txt','pinnedInputDataCredit':'Vitruvian CC0 declared config; source hair remains Daniel Bystedt CC BY-SA, version unspecified. No external service/addon/code installation.','originalBoneDataOfflineArchived':True,'all32ActualMotionFramesArchived':True,'excludedModels':[],'formalPromotionOrFemaleAcceptance':False};p=M/'r0069-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0069-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R69_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
