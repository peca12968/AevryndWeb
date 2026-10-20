"""Exact r62 reconciliation + r63 complete-character production archive.

No website assets, unrelated work or duplicate large simulation checkpoints.
Shared licensed texture files must already exist with verified exact hashes.
"""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0063-layered-crop';OLD=E.parent/'r0062-packed-bundle';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    audit=read(E/'female-next-r0063.visual-audit.json');assert audit['runtime']['status']=='NOT_TESTED_NOT_PROMOTED'
    prior=read(OLD/'reconciled-study-audit.json');assert not prior['function']['nativeMotionBlendCreated']
    assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True).strip()
    files=[];allow=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024*1024,src
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        path=dst.relative_to(REPO).as_posix();allow.append(path);files.append({'file':path,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for number in ('0062','0063'):
        for src in sorted(S.glob('*r'+number+'*')):
            if src.suffix in ('.blend','.json'):copy(src,M/src.name)
    for number,folder in (('0062',OLD),('0063',E)):
        for src in sorted(folder.iterdir()):
            if src.suffix in ('.json','.png','.log','.txt','.py') and src.name not in ('github-receipt.json','history-bundle.json','history-allowlist.json'):
                copy(src,M/(f'r{number}-'+src.name))
            elif src.name in ('a-packed-bundle-authoring.npz','b-global-guide-motion.npz','a-crop-authoring.npz'):
                copy(src,M/(f'r{number}-'+src.name))
    # The saved source stores positions/radii/root metadata. Duplicate broad
    # simulation checkpoints and generated object/library intermediates stay
    # local; rejected guide cache is small and retained to reproduce its fail.
    for src in sorted((R/'scripts/character-next').iterdir()):
        if ('female-next-r0062' in src.name or 'female-next-r0063' in src.name) and src.suffix in ('.py','.cmd'):
            copy(src,REPO/'scripts/character-next'/src.name)
    copy(R/'engine/character/physics/shaft_contacts.cpp',REPO/'engine/character/physics/shaft_contacts.cpp')
    ref=R/'engine/character/physics/groom_xpbd_reference.py';assert sha(ref)==sha(REPO/'engine/character/physics'/ref.name)
    copy(R/'engine/assets/characters/female-next/female-next.asset.json',M/'female-next.asset.json')
    textures=[]
    for item in read(E/'a-native-readback.json')['relativeTextures']:
        name=item['relative'].replace('\\','/').rsplit('/',1)[-1];target=M/'study-vitruvian-textures'/name;assert target.exists() and sha(target)==item['sha256'];textures.append(name)
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r62 bounded unit research and r63 complete crop trial.'
    if header not in text:
        text=text.rstrip()+'\n'+header+'\n'+'r006[23]-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r006[23]-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r006[23]-character-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'
        attr.write_text(text,encoding='utf8',newline='\n')
    profile_rule='r0062-independent-contact-profile.txt -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol'
    if profile_rule not in text:
        text=text.replace('r0062-independent-contact-profile.txt -text whitespace=-blank-at-eof\n','').rstrip()+'\n'+profile_rule+'\n';attr.write_text(text,encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    attr=REPO/'scripts/character-next/.gitattributes';text=attr.read_text(encoding='utf8');rule='*female-next-r006[23]* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    attr=REPO/'engine/character/physics/.gitattributes';text=attr.read_text(encoding='utf8') if attr.exists() else '';rule='shaft_contacts.cpp -text'
    if rule not in text:attr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    bundle={'schema':1,'decision':audit['decision'],'files':files,'sharedTexturesVerifiedOnce':textures,'r62Decision':prior['decision'],'r62NativeKernelStatus':prior['nativePrototype'],'skippedReconstructibleCaches':['c-independent-checkpoint.npz','c-discrete-rejected-checkpoint.npz','actual-body-render-surface.npz','native/*.obj','native/*.dll','native/*.lib','native/*.exp'],'rebuild':'Blender scripts retain hardcoded project root; run from original workspace layout. Native DLL requires existing MSVC BuildTools and saved .cmd. Current sweep API and all r62 motion remain unaccepted. Saved Blender sources do not depend on the DLL.','noWebsiteOrRuntimePromotion':True}
    path=M/'r0063-history-bundle.json';save(path,bundle);allow.append(path.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle)
    path=M/'r0063-history-allowlist.json';allow.append(path.relative_to(REPO).as_posix());save(path,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))})
    print('R63_EXACT_HISTORY_BUNDLE',len(allow),'files',sum(x['bytes'] for x in files),'bytes')
if __name__=='__main__':main()
