"""Exact model, authoring and scoped evidence history; no runtime promotion."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0060-ocular-assembly'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    assert subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only'])==b'';audit=read(E/'female-next-r0060.visual-audit.json');receipt=read(E/'reconciliation-receipt.json');m=read(R/'engine/assets/characters/female-next/female-next.asset.json');assert all(m[key]==value for key,value in receipt['preservedFields'].items()) and audit['contact']['status']=='PASS_SEVEN_TESTED_STATIC_OCULAR_SURFACE_AND_SPACE_SCOPE_ONLY';assert m['runtimeStatus']=='NOT_PROMOTED'
    attrs=M/'.gitattributes';content=attrs.read_text()
    if '# Exact r60' not in content:content=content.rstrip()+'\n# Exact r60 component sources, evidence and raw terminal bytes.\nr0060-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0060-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0060-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0060-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nr0060-blink-frames/*.png -text\n'
    attrs.write_text(content,encoding='utf8',newline='\n');scriptattrs=G/'scripts/character-next/.gitattributes';content=scriptattrs.read_text()
    if '*female-next-r0060*.py' not in content:content=content.rstrip()+'\n*female-next-r0060*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
    scriptattrs.write_text(content,encoding='utf8',newline='\n');files=[attrs,scriptattrs]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for x in receipt['sourceSnapshots']:
        p=Path(x['source']);assert sha(p)==x['sha256'];cp(p,M/p.name)
    descriptor=S/'aevrynd-female-next-r0060-authoring.json';cp(descriptor,M/descriptor.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.npz','.png','.gif') and p.name not in ('history-file-manifest.json','git-paths.json','github-receipt.json'):cp(p,M/(p.name if p.name.startswith('r0060-') else 'r0060-'+p.name))
    frames=read(E/'b-blink-clip-renders.json')['frames'];assert len(frames)==48
    for x in frames:
        p=Path(x['path']);cp(p,M/'r0060-blink-frames'/p.name)
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0060*.py')):cp(p,G/'scripts/character-next'/p.name)
    for p in sorted((R/'Evidence').glob('character-female-next-r0060-*.log')):cp(p,M/p.name)
    cp(R/'engine/assets/characters/female-next/female-next.asset.json',M/'female-next.asset.json');cp(E.parent/'r0059-authored-blink/github-receipt.json',M/'r0059-github-receipt.json')
    resources=[]
    for x in read(E/'b-functional-lineage-verification.json')['relativeImages']:
        p=M/'study-vitruvian-textures'/Path(x['path'].replace('\\','/').lstrip('/')).name;assert sha(p)==x['sha256'];resources.append({'path':p.relative_to(G).as_posix(),'sha256':sha(p)})
    write(E/'history-file-manifest.json',{'revision':'female-next-r0060','formalAdopted':False,'retainedScope':audit['contact']['status'],'sharedRequiredResources':resources,'files':[{'path':p.relative_to(G).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]});cp(E/'history-file-manifest.json',M/'r0060-history-file-manifest.json');write(E/'git-paths.json',sorted(set(p.relative_to(G).as_posix() for p in files)));print('R60_EXACT_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)
if __name__=='__main__':main()
