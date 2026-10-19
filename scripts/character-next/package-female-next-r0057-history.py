"""Exact offline history bundle for reconciled r56 and r57; no promotion."""
from pathlib import Path
import json, hashlib, shutil, subprocess
R=Path(r'D:\Download\Aevrynd'); REPO=R/'sites-engine-journey'; S=R/'engine/assets/characters/female-next/source'
M=REPO/'assets-source/aevrynd-character/female-next'; E=R/'Evidence/character-female-next/r0057-coherent-foundation'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'])==b'', 'Index must be empty before exact package staging.'
    a=read(E/'female-next-r0057.visual-audit.json'); c=read(E/'continuation.json'); receipt=read(E/'reconciliation-receipt.json')
    assert not a['appearance']['appearanceImprovement'] and a['runtime']['status']=='NOT_TESTED_NOT_PROMOTED'
    mp=R/'engine/assets/characters/female-next/female-next.asset.json'; m=read(mp)
    assert all(m[k]==v for k,v in receipt['preservedMainAndFormalFields'].items())
    assert sha(S/Path(m['workingReviewSource']).name)==m['workingReviewSha256']
    attrs=M/'.gitattributes'; content=attrs.read_text()
    addition='\n# Preserve exact r56/r57 study, evidence and resource bytes.\nr005[67]-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\naevrynd-female-next-r005[67]-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\ncharacter-female-next-r005[67]-* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nr0057-reference-* -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\nstudy-vitruvian-textures/*.exr -text\n'
    if 'Preserve exact r56/r57' not in content:content=content.rstrip()+'\n'+addition
    if '# Raw terminal logs' not in content:content=content.rstrip()+'\n# Raw terminal logs retain diagnostic whitespace byte for byte.\ncharacter-female-next-r005[67]-*.log -text whitespace=-blank-at-eol,-blank-at-eof,-space-before-tab,cr-at-eol\n'
    attrs.write_text(content,encoding='utf8',newline='\n')
    scriptattrs=REPO/'scripts/character-next/.gitattributes'; content=scriptattrs.read_text()
    if '*female-next-r005[67]*.py' not in content:content=content.rstrip()+'\n*female-next-r005[67]*.py -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n'
    scriptattrs.write_text(content,encoding='utf8',newline='\n')
    files=[attrs,scriptattrs]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for x in receipt['snapshots']:
        p=Path(x['file']);assert sha(p)==x['sha256'];cp(p,M/p.name)
    for rev,folder in [('r0056','r0056-target-native-comb'),('r0057','r0057-coherent-foundation')]:
        cp(S/('aevrynd-female-next-'+rev+'-authoring.json'),M/('aevrynd-female-next-'+rev+'-authoring.json'))
        for p in sorted((R/'Evidence/character-female-next'/folder).iterdir()):
            if p.suffix in ('.json','.npz','.png') and p.name not in ('git-paths.json','history-file-manifest.json','github-receipt.json'):
                cp(p,M/(p.name if p.name.startswith(rev+'-') else rev+'-'+p.name))
        for p in sorted((R/'scripts/character-next').glob('*female-next-'+rev+'*.py')):cp(p,REPO/'scripts/character-next'/p.name)
        for p in sorted((R/'Evidence').glob('character-female-next-'+rev+'-*')):
            if p.is_file() and p.suffix in ('.log','.err'):cp(p,M/p.name)
    cp(mp,M/'female-next.asset.json')
    reference=R/'Reference/character/charmorph-vitruvian-cc0'
    # No raw library .blend (embedded texts), addon code or duplicate 365MB4K cache.
    for name in ['PROVENANCE.json','r0057-texture-provenance.json','Default.npy','Gender_Female.npz','Bob.npz','config.yaml','README.md','settings.yaml']:
        cp(reference/name,M/('r0057-reference-'+name))
    textures=read(E/'texture-derivatives.json')
    for x in textures['files']:
        src=S/'study-vitruvian-textures'/x['file'];assert sha(src)==x['sha256'];cp(src,M/'study-vitruvian-textures'/src.name)
    assert len(textures['files'])==15
    write(E/'history-file-manifest.json',{'revisions':['female-next-r0056','female-next-r0057'],'retainedPortableSource':m['coherentFoundationResearchSource'],'formalMainRuntimeUnchanged':True,'files':[{'path':p.relative_to(REPO).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    cp(E/'history-file-manifest.json',M/'r0057-history-file-manifest.json')
    write(E/'git-paths.json',sorted(set(p.relative_to(REPO).as_posix() for p in files)))
    print('R56_R57_EXACT_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)
if __name__=='__main__':main()
