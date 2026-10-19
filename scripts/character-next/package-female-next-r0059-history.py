"""Exact-file archive: native blink controls, actual frames, failed contacts."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0059-authored-blink'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    assert subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only'])==b''
    a=read(E/'female-next-r0059.visual-audit.json');receipt=read(E/'reconciliation-receipt.json');m=read(R/'engine/assets/characters/female-next/female-next.asset.json');assert all(m[key]==value for key,value in receipt['preservedFields'].items());assert not a['appearance']['appearanceImprovement'] and a['runtime']['status']=='NOT_TESTED_NOT_PROMOTED'
    attrs=M/'.gitattributes';text=attrs.read_text()
    if '# Exact r59' not in text:text=text.rstrip()+'\n# Exact r59 source, motion evidence and raw terminal bytes.\nr0059-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0059-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0059-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0059-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nr0059-source-morphs.json -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nr0059-blink-frames/*.png -text\n'
    attrs.write_text(text,encoding='utf8',newline='\n');scriptattrs=G/'scripts/character-next/.gitattributes';text=scriptattrs.read_text()
    if '*female-next-r0059*.py' not in text:text=text.rstrip()+'\n*female-next-r0059*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
    scriptattrs.write_text(text,encoding='utf8',newline='\n');files=[attrs,scriptattrs]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    source=Path(a['source']);assert sha(source)==a['sourceSha256'];cp(source,M/source.name);descriptor=S/'aevrynd-female-next-r0059-authoring.json';cp(descriptor,M/descriptor.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.npz','.png','.gif') and p.name not in ('history-file-manifest.json','git-paths.json','github-receipt.json'):cp(p,M/(p.name if p.name.startswith('r0059-') else 'r0059-'+p.name))
    frames=read(E/'a-blink-clip-renders.json')['frames'];assert len(frames)==48
    for x in frames:
        p=Path(x['path']);cp(p,M/'r0059-blink-frames'/p.name)
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0059*.py')):cp(p,G/'scripts/character-next'/p.name)
    for p in sorted((R/'Evidence').glob('character-female-next-r0059-*.log')):cp(p,M/p.name)
    cp(R/'engine/assets/characters/female-next/female-next.asset.json',M/'female-next.asset.json');cp(E.parent/'r0058-source-emitter/github-receipt.json',M/'r0058-github-receipt.json')
    for x in read(E/'source-provenance.json')['files']:assert sha(E/x['file'])==x['sha256']
    resources=[]
    for x in read(E/'a-functional-verification.json')['relativeResourceImages']:
        p=M/'study-vitruvian-textures'/Path(x['relativePath'].replace('\\','/').lstrip('/')).name;assert sha(p)==x['sha256'];resources.append({'path':p.relative_to(G).as_posix(),'sha256':sha(p)})
    write(E/'history-file-manifest.json',{'revision':'female-next-r0059','adopted':False,'sharedRequiredResources':resources,'originalEmbeddedCodeOrNewSoftwareImported':False,'files':[{'path':p.relative_to(G).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    cp(E/'history-file-manifest.json',M/'r0059-history-file-manifest.json');write(E/'git-paths.json',sorted(set(p.relative_to(G).as_posix() for p in files)));print('R59_EXACT_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)
if __name__=='__main__':main()
