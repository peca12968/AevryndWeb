"""Archive exact complete C and bounded evidence, excluding duplicate A/B caches."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0068-guide-structure';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    audit=read(E/'female-next-r0068.visual-audit.json');assert audit['decision']=='RETAIN_COMPLETE_APPEARANCE_STUDY_FULL_PHYSICS_UNACCEPTED';assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip();allow=[];files=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    source=Path(audit['source']);assert sha(source)==audit['sha256'];copy(source,M/source.name)
    for name in ('aevrynd-female-next-r0068-authoring.json','aevrynd-female-next-r0068.LICENSE-SOURCE.txt'):copy(S/name,M/name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.png','.log','.txt','.npz') and p.name not in ('history-bundle.json','history-allowlist.json','github-receipt.json','a-original-preview-face.png'):copy(p,M/('r0068-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0068*.py')):copy(p,REPO/'scripts/character-next'/p.name)
    copy(S.parent/'female-next.asset.json',M/'female-next.asset.json')
    for row in read(E/'c-native-readback.json')['relativeTextures']:
        p=M/row['relative'].replace('\\','/').removeprefix('//');assert p.exists() and sha(p)==row['sha256']
    oldrefs=[];prior=E.parent/'r0065-eye-shading'
    for name in ('a-eye-face.png','a-eye-body-face.png','a-eye-oblique.png','a-eye-profile.png','a-eye-back.png','a-eye-alternate-oblique.png','a-face-control.json','a-extra-view-controls.json','a-build-summary.json','a-functional-contact-transfer.json'):
        p=M/('r0065-'+name);assert p.exists() and sha(p)==sha(prior/name);oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Exact r65 baseline images/controls or existing scoped neutral/ocular evidence, not new hair contact.'})
    p=M/Path(audit['qualifiedFoundation']).name;assert sha(p)==audit['qualifiedFoundationSha256'];oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Scoped verified r65 ocular/anatomy foundation retained separately from complete C appearance study.'})
    for name in ('r0066-skin-response','r0067-native-eve'):
        tag='a-skin' if name.startswith('r0066') else 'b-eve';prefix='r0066-' if name.startswith('r0066') else 'r0067-'
        for view in ('face','body-face'):
            p=M/(prefix+tag+'-'+view+'.png');assert sha(p)==sha(E.parent/name/(tag+'-'+view+'.png'));oldrefs.append({'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'scope':'Rejected study image reused only for three-round complete-character review.'})
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf-8');header='# Exact r68 attributed guide-surface complete appearance study; physics unaccepted.'
    if header not in text:attr.write_text(text.rstrip()+'\n'+header+'\nr0068-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0068* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0068-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n',encoding='utf-8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix());attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf-8');rule='*female-next-r0068*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf-8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    excluded=[]
    for tag in ('a','b'):
        row=read(E/(tag+'-build-summary.json'));p=Path(row['output']);assert sha(p)==row['outputSha256'];excluded.append({'localFile':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'reason':'Rejected complete stage contains redundant rebuildable static render-body reference cache. Local immutable .blend retained; scripts, exact curve arrays, previews and falsification evidence archived. These A/B .blend files are NOT uploaded.'})
    bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedWithoutRecopy':15,'reusedExactEvidence':oldrefs,'sourceRole':'C complete attributed appearance study retained, full hair physics unaccepted. R65 scoped qualified foundation and formal r1 unchanged. No female approval/runtime promotion.','sourceCredit':audit['sourceCredit'],'sourceLicenseNotice':'aevrynd-female-next-r0068.LICENSE-SOURCE.txt','excludedLocalModels':excluded,'publisherBinaryArchived':False,'publisherFileURL':'https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend','publisherSha256':'1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48','reconstructibleDuplicateExcluded':'a-original-preview-face.png exactly duplicates a-guide-preview-face.png','newSoftwareAddonOrPaidRuntimeInstalled':False}
    p=M/'r0068-history-bundle.json';save(p,bundle);allow.append(p.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle);p=M/'r0068-history-allowlist.json';allow.append(p.relative_to(REPO).as_posix());save(p,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))});print('R68_EXACT_BUNDLE',len(allow),sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
