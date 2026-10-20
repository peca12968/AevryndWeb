"""Exact three-source rejected-study history; no runtime promotion or other work."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0070-native-flexible';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    audit=read(E/'female-next-r0070.visual-audit.json');assert audit['decision']=='REJECT_ALL_NATIVE_FLEXIBLE_TRIALS_KEEP_R69';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();files=[];allow=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for tag,row in audit['metrics'].items():
        p=Path(row['source']);assert sha(p)==row['sha256'];copy(p,M/p.name)
    for name in ('aevrynd-female-next-r0070-authoring.json','aevrynd-female-next-r0070.LICENSE-SOURCE.txt'):copy(S/name,M/name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt','.npz','.npy') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json'):copy(p,M/('r0070-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0070*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    module=R/'engine/character/physics/groom_native_xpbd_reference.py';copy(module,REPO/'engine/character/physics'/module.name);copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    oldrefs=[];prior=E.parent/'r0069-complete-controls'
    for name in ('aevrynd-female-next-r0069-a-complete-controls-study.blend','aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'):
        p=M/name;assert sha(p)==sha(S/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Unchanged complete active r69 actor or separately qualified r65 ocular/anatomy basis.'})
    for name in ('a-control-face.png','a-control-body-face.png','a-control-oblique.png','a-control-profile.png','a-control-back.png','a-control-alternate-oblique.png','r0069-actual-complete-motion.gif','a-independent-readback.json','a-moved-tissue-probe.json','a-neutral-full-view-controls.json'):
        p=M/('r0069-'+name);assert p.exists() and sha(p)==sha(prior/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Existing full active-character evidence; not counted as a new r70 improvement.'})
    for row in read(E/'rejected-study-readback.json')['studies'][0]['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r70 rejected complete-actor flexible trials; no physics adopted.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\nr0070-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0070* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0070-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    for path,rule in ((REPO/'scripts/character-next/.gitattributes','*female-next-r0070*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'),(REPO/'engine/character/physics/.gitattributes','groom_native_xpbd_reference.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol')):
        text=path.read_text(encoding='utf8') if path.exists() else ''
        if rule not in text:path.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
        allow.append(path.relative_to(REPO).as_posix())
    bundle={'schema':1,'decision':audit['decision'],'files':files,'reusedExactEvidence':oldrefs,'sharedTexturesVerifiedWithoutRecopy':15,'allThreeRejectedBlendSourcesArchived':True,'excludedModels':[],'sourceRole':'All r70 sources are rejected one-step whole-actor physics studies. Active complete actor remains r69, qualified ocular/anatomy basis r65, formal r1 untouched. No adopted appearance, dynamics, contact, runtime or female approval.','experimentalPythonModule':'Rejected study only, not registered engine runtime.','upstreamCodeImportedOrSoftwareInstalled':False,'sourceRightsNotice':'aevrynd-female-next-r0070.LICENSE-SOURCE.txt','referencesAreLearningOnly':True};p=M/'r0070-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0070-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R70_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
