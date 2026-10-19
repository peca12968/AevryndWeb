"""Exact failed-character-trial archive; no unrelated changes or large caches."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0061-surface-flow-groom';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    audit=json.loads((E/'female-next-r0061.visual-audit.json').read_text());assert audit['decision']=='REJECT_FULL_GROOM_RETAIN_REST_LINEAGE_TOOLS_ONLY'
    allow=[];files=[]
    def copy(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        rel=dst.relative_to(REPO).as_posix();allow.append(rel);files.append({'file':rel,'bytes':dst.stat().st_size,'sha256':sha(dst)})
    for src in sorted(S.glob('*r0061*')):
        if src.suffix in ('.blend','.json'):assert src.stat().st_size<100*1024*1024;copy(src,M/src.name)
    for src in sorted(E.iterdir()):
        if src.suffix in ('.json','.png','.log') and src.name not in ('github-receipt.json','history-bundle.json','history-allowlist.json'):
            copy(src,M/('r0061-'+src.name))
        elif src.name in ('a-guides-authoring.npz','b-guides-authoring.npz'):copy(src,M/('r0061-'+src.name))
    for src in sorted((R/'scripts/character-next').glob('*female-next-r0061*.py')):copy(src,REPO/'scripts/character-next'/src.name)
    copy(R/'engine/assets/characters/female-next/female-next.asset.json',M/'female-next.asset.json')
    textures=json.loads((E/'c-source-readback.json').read_text())['textures'];verified=[]
    for row in textures:
        name=row['relative'].replace('\\','/').rsplit('/',1)[-1];target=M/'study-vitruvian-textures'/name;assert target.exists() and sha(target)==row['sha256'];verified.append(name)
    attr=M/'.gitattributes';text=attr.read_text(encoding='utf8');header='# Exact r61 failed full-groom sources and evidence; shared textures retained once.'
    if header not in text:
        text=text.rstrip()+'\n'+header+'\n'+'r0061-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'aevrynd-female-next-r0061-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'+'r0061-character-female-next-r0061-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'
        attr.write_text(text,encoding='utf8',newline='\n')
    allow.append(attr.relative_to(REPO).as_posix())
    scriptsAttr=REPO/'scripts/character-next/.gitattributes';text=scriptsAttr.read_text(encoding='utf8');rule='*female-next-r0061*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
    if rule not in text:scriptsAttr.write_text(text.rstrip()+'\n'+rule+'\n',encoding='utf8',newline='\n')
    allow.append(scriptsAttr.relative_to(REPO).as_posix())
    bundle={'schema':1,'decision':audit['decision'],'sourceOfTruth':audit['source'],'sourceSha256':audit['sourceSha256'],'files':files,'sharedTexturesAlreadyPresentVerified':verified,'skippedReconstructibleCaches':['actual-body-render-surface.npz','b-fibres-authoring.npz','native-uv-island-lineage.npz'],'rebuildCache':'Run build-female-next-r0061-surface-flow-groom.py without --pilot/--fibres to rebuild actual body cache from verified r60B. C native CURVES store the display positions/radii and rest root attributes; full b-fibres-authoring arrays can be read from C instead of archived twice.','notPromoted':True,'allFourCreatedBlendSnapshotsRetained':True}
    path=M/'r0061-history-bundle.json';save(path,bundle);allow.append(path.relative_to(REPO).as_posix());save(E/'history-bundle.json',bundle)
    path=M/'r0061-history-allowlist.json';allow.append(path.relative_to(REPO).as_posix());save(path,{'files':sorted(set(allow))});save(E/'history-allowlist.json',{'files':sorted(set(allow))})
    staged=subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'],text=True);assert not staged.strip(),'Index not empty'
    print('R61_BUNDLE_READY',len(allow),'files',sum(x['bytes'] for x in files),'bytes, shared EXRs not copied',flush=True)
if __name__=='__main__':main()
