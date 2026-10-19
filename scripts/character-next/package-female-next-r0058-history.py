"""Archive one rejected native-source candidate and corrected source reader."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(r'D:\Download\Aevrynd');G=R/'sites-engine-journey';M=G/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0058-source-emitter'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    assert subprocess.check_output(['git','-C',str(G),'diff','--cached','--name-only'])==b''
    audit=read(E/'female-next-r0058.visual-audit.json');receipt=read(E/'reconciliation-receipt.json');m=read(R/'engine/assets/characters/female-next/female-next.asset.json')
    assert all(m[k]==v for k,v in receipt['preservedFields'].items()) and not audit['appearance']['appearanceImprovement']
    attrs=M/'.gitattributes';text=attrs.read_text()
    if '# Exact r58' not in text:text=text.rstrip()+'\n# Exact r58 candidate, evidence and raw terminal bytes.\nr0058-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r0058-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0058-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r0058-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'
    attrs.write_text(text,encoding='utf8',newline='\n');scriptattrs=G/'scripts/character-next/.gitattributes';text=scriptattrs.read_text()
    if '*female-next-r0058*.py' not in text:text=text.rstrip()+'\n*female-next-r0058*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
    scriptattrs.write_text(text,encoding='utf8',newline='\n');files=[attrs,scriptattrs]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    source=Path(audit['source']);assert sha(source)==audit['sourceSha256'];cp(source,M/source.name);desc=S/'aevrynd-female-next-r0058-authoring.json';cp(desc,M/desc.name)
    for p in sorted(E.iterdir()):
        if p.suffix in ('.json','.npz','.png') and p.name not in ('history-file-manifest.json','git-paths.json','github-receipt.json'):cp(p,M/(p.name if p.name.startswith('r0058-') else 'r0058-'+p.name))
    for p in sorted((R/'scripts/character-next').glob('*female-next-r0058*.py')):cp(p,G/'scripts/character-next'/p.name)
    for p in sorted((R/'Evidence').glob('character-female-next-r0058-*.log')):cp(p,M/p.name)
    cp(R/'engine/assets/characters/female-next/female-next.asset.json',M/'female-next.asset.json')
    cp(E.parent/'r0057-coherent-foundation/github-receipt.json',M/'r0057-github-receipt.json')
    # Existing15derived images are shared alongside the sources. Validate their
    # actual bytes; no second 56MBcopy and no raw66MBlibrary needed for rebuilding
    # this candidate from its complete native emitter/key arrays.
    resources=[]
    for x in read(E/'a-reopened-verification.json')['relativeResourceImages']:
        p=M/'study-vitruvian-textures'/Path(x['relativePath'].replace('\\','/').lstrip('/')).name;assert sha(p)==x['sha256'];resources.append({'path':p.relative_to(G).as_posix(),'sha256':sha(p)})
    write(E/'history-file-manifest.json',{'revision':'female-next-r0058','adopted':False,'sharedRequiredResources':resources,'files':[{'path':p.relative_to(G).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    cp(E/'history-file-manifest.json',M/'r0058-history-file-manifest.json');write(E/'git-paths.json',sorted(set(p.relative_to(G).as_posix() for p in files)))
    print('R58_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)
if __name__=='__main__':main()
