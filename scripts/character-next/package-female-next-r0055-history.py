"""Exact-file archive of reconciled r54 and bounded r55 production evidence.

Requires the explicit visual decision; never infers adoption from test counts.
"""
from pathlib import Path
import json,hashlib,shutil
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
E=R/'Evidence/character-female-next/r0055-authored-cc0-bob'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    audit=read(E/'female-next-r0055.visual-audit.json');continuation=read(E/'continuation.json')
    mp=R/'engine/assets/characters/female-next/female-next.asset.json';m=read(mp)
    preservedKeys=['workingReviewRevision','workingReviewSource','workingReviewSha256','workingReviewStatus','currentSourceRevision','currentSource','strictOverallScore','strictScoreAppliesTo','runtimeAsset','runtimeStatus','enginePromotionApproved','websitePromotionApproved']
    preserved={k:m[k] for k in preservedKeys};assert sha(S/Path(m['workingReviewSource']).name)==m['workingReviewSha256']
    assert not audit['appearance']['appearanceImprovement'] and audit['runtime']['status']=='NOT_TESTED_NOT_PROMOTED'
    descriptors=[];snapshots=[]
    for revision,folder in [('r0054','r0054-clump-volume'),('r0055','r0055-authored-cc0-bob')]:
        folder=R/'Evidence/character-female-next'/folder
        for p in sorted(folder.glob('*-build-summary.json')):
            row=read(p);out=Path(row['output']);assert sha(out)==row['outputSha256'];snapshots.append(out)
        descriptor=S/('aevrynd-female-next-'+revision+'-authoring.json')
        if revision=='r0055':write(descriptor,{'revision':'female-next-r0055','decision':audit['decision'],'adopted':False,'completeWorkingSource':str(S/Path(m['workingReviewSource']).name),'completeWorkingSha256':m['workingReviewSha256'],'evidence':str(E/'female-next-r0055.visual-audit.json'),'research':audit['function'],'nextAction':continuation['nextAction']})
        descriptors.append(descriptor)
    m.update(latestStudyRevision='female-next-r0055',latestStudyStatus=audit['decision'],latestStudyEvidence=str(E/'female-next-r0055.visual-audit.json'),latestContinuation=str(E/'continuation.json'),nextRequiredWork=continuation['nextAction'],
        characterAuthoringDescriptorR54='source/aevrynd-female-next-r0054-authoring.json',characterAuthoringDescriptorR55='source/aevrynd-female-next-r0055-authoring.json')
    assert all(m[k]==v for k,v in preserved.items());write(mp,m)
    files=[]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for p in snapshots+descriptors:cp(p,M/p.name)
    cp(mp,M/'female-next.asset.json')
    for revision,folder in [('r0054','r0054-clump-volume'),('r0055','r0055-authored-cc0-bob')]:
        folder=R/'Evidence/character-female-next'/folder
        for p in sorted(folder.iterdir()):
            if p.suffix in ('.json','.npz','.png') and p.name not in ('git-paths.json','history-file-manifest.json'):
                cp(p,M/(p.name if p.name.startswith(revision+'-') else revision+'-'+p.name))
        for p in sorted((R/'scripts/character-next').glob('*female-next-'+revision+'*.py')):cp(p,REPO/'scripts/character-next'/p.name)
        for p in sorted((R/'Evidence').glob('character-female-next-'+revision+'-*.log')):cp(p,M/p.name)
    reference=R/'Reference/character/charmorph-vitruvian-cc0';provenance=read(reference/'PROVENANCE.json')
    for row in provenance['files']:assert sha(reference/row['file'])==row['sha256']
    for p in sorted(reference.iterdir()):
        # Original library .blend remains a local reference. It contains auto-run
        # rig texts that were disabled, never imported or published as engine code.
        # Extracted CC0 mesh arrays and exact source hashes suffice for this study.
        if p.is_file() and p.name!='char.blend':cp(p,M/('r0055-reference-'+p.name))
    files.extend([M/'.gitattributes',REPO/'scripts/character-next/.gitattributes'])
    write(E/'history-file-manifest.json',{'revisions':['female-next-r0054','female-next-r0055'],'files':[{'path':str(p.relative_to(REPO)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    cp(E/'history-file-manifest.json',M/'r0055-history-file-manifest.json')
    write(E/'git-paths.json',sorted(set(str(p.relative_to(REPO)).replace('\\','/') for p in files)))
    print('R54_R55_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)

if __name__=='__main__':main()
