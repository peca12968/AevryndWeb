"""Archive a rejected oral pilot without promoting it or altering prior scores."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0024-oral-layers';REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):return ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',n)
def pictures():
    image=Image.new('RGB',(1200,980),(22,26,31));d=ImageDraw.Draw(image)
    for col,(prefix,label) in enumerate((('before','Before / same open field, oral layers hidden'),('after','Oral study B / CONTACT GATES FAILED'))):
        x=col*600;d.text((x+10,10),label,font=font(19),fill='white')
        image.paste(Image.open(E/f'{prefix}-open-face.png').convert('RGB').resize((600,600),Image.Resampling.LANCZOS),(x,40))
        d.text((x+10,650),'Same camera / lighting / exposure / pose',font=font(17),fill='white')
        image.paste(Image.open(E/f'{prefix}-open-mouth.png').convert('RGB').resize((600,300),Image.Resampling.LANCZOS),(x,680))
    image.save(E/'r0024-oral-comparison.png')
    image=Image.new('RGB',(1000,1080),(22,26,31));d=ImageDraw.Draw(image)
    for row,(state,label) in enumerate((('neutral','Neutral'),('open','Small open / diagnostic only'))):
        for col,prefix in enumerate(('before','after')):
            x=col*500;y=row*540;d.text((x+10,y+12),prefix+' / '+label,font=font(18),fill='white')
            image.paste(Image.open(E/f'{prefix}-{state}-oblique.png').convert('RGB').resize((500,500),Image.Resampling.LANCZOS),(x,y+40))
    image.save(E/'r0024-oral-multiview.png')
    frames=[]
    for frame in (1,4,7,10,13,16,19,22,25):
        im=Image.new('RGB',(640,680),(22,26,31));im.paste(Image.open(E/f'motion-{frame:02d}-face.png').convert('RGB').resize((640,640),Image.Resampling.LANCZOS),(0,40));ImageDraw.Draw(im).text((10,10),'ORAL MOTION STUDY / CONTACT FAILURES PRESENT',font=font(18),fill='white');frames.append(im)
    frames[0].save(E/'r0024-b-oral-motion-review.gif',save_all=True,append_images=frames[1:],duration=250,loop=0)
def main():
    build=read(E/'b-build-verification.json');static=read(E/'b-static-verification.json');renders=read(E/'b-renders.json');motion=read(E/'b-saved-motion-review-verification.json');provenance=read(E/'contact-provenance.json')
    assert sha(Path(build['output']))==build['outputSha256']==static['assetSha256']==renders['sourceSha256']
    assert sha(Path(motion['asset']))==motion['sha256'] and len(static['results'])==2
    matched=[]
    for state in ('neutral','open'):
        for view in ('face','oblique','mouth'):
            a=next(r for r in renders['renders'] if r['label']=='before-'+state and r['view']==view);b=next(r for r in renders['renders'] if r['label']=='after-'+state and r['view']==view)
            assert all(a[k]==b[k] for k in ('cameraMatrix','size','lens','engine','viewTransform','look','exposure','gamma','lights'))
            matched.append({'state':state,'view':view,'sameConditions':True})
    save(E/'render-controls-verification.json',{'status':'MATCHED_CONDITIONS','pairs':matched,'baselineDefinition':renders['baselineDefinition']});pictures()
    save(E/'a-rejection.json',{'status':'REJECT_EXACT_NATIVE_HELPER_RIGID_TRANSFER','row':'AFN24_LowerTeeth','helperRigidResidualM':.0007110226510348538,'maximumAllowedM':.0005,'reason':'The original helper target is nonrigid; never stretch teeth or relax the original gate to call it exact. A did not complete an asset. B uses a separately declared independent hinge approximation, which also fails contact gates.'})
    next_action=('Keep r23 B as the complete integrated working head. r24 adds editable CC0 oral data and independent rigid jaw controls only as a failed-contact research source. Do not refetch the archive or sweep mouth-open strength/dental scales. Before another full mouth animation, repair/rebuild the neutral dental-contact and cavity assembly: inspect each crown boundary/topology and distinguish actual interpenetration from structurally documented contact, using r24 contact-provenance pairs and source vertex IDs. Original CC0 dental geometry already has 1456 inter-tooth triangle pairs, so direct asset reuse is not a collision certificate. Build a bounded, anatomically justified pair/arch repair with actual crown shape and contact gaps, keeping neutral lip rest, complete head, skin, lights, eyes and hair fixed. Prove that small assembly first. Then bind gingival lining and tongue consistently to the same rigid jaw rather than mixing native linear soft-tissue targets with an independent hinge; check neutral and small-open actual surfaces before extending motion. Do not shrink all teeth/tongue, hide regions or exclude failures merely to pass. If the asset architecture cannot be repaired in one bounded candidate, replace the oral topology/asset route rather than repeating proxy refits. r20 blink, hair appearance/self/dynamics, expressions/full body/clothes, runtime/LOD/performance and explicit female acceptance remain incomplete.')
    audit={'stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':build['source'],'sourceSha256':build['sourceSha256'],'study':build['output'],'studySha256':build['outputSha256'],'decision':'RESEARCH_RETAINED_REJECT_FOR_WORKING_HEAD_OR_RUNTIME_PROMOTION','appearance':'Real dental/gingival/tongue geometry now appears through the same small opening. Whole face remains artificial; visible tooth band is blocky and tense, not an accepted natural mouth. Neutral exterior has no material/shape gain.','appearanceScore':None,'overallCharacterScore':None,'function':'32 crowns split into 16 upper and 16 lower; separate continuous gingival mesh and tongue, editable collections, independently driven fixed-axis lower jaw, safe-mode playable open/close review. Upper row held static. Not a physiological jaw calibration or accepted expression.','contact':'Neutral oral/body triangle pairs zero; small-open gingival/body 14. Dental inter-tooth and tongue/lining contacts remain unresolved; all raw contacts retained. Two endpoints only, no continuous proof.','static':str(E/'b-static-verification.json'),'originalCC0DentalNonAdjacentPairs':provenance['originalCC0Asset']['nonAdjacentPairs'],'originalCC0InterToothPairs':provenance['originalCC0Asset']['betweenDifferentTeeth'],'runtime':'NOT_IMPLEMENTED_OR_TESTED','nextAction':next_action}
    save(E/'female-next-r0024.visual-audit.json',audit)
    manifest_path=S.parent/'female-next.asset.json';manifest=read(manifest_path)
    assert manifest['workingReviewRevision']=='female-next-r0023-b' and sha(S.parent/manifest['workingReviewSource'])==manifest['workingReviewSha256'] and manifest['runtimeAsset'] is None
    continuation={'stage':audit['stage'],'lastGoalTurnClassification':'progress','classificationReason':'Official CC0 oral data fitted with an own parser, actual editable oral layers and independent rigid dental controls built, safe-mode motion reopened, matched full-head/closeup/multiview and playable frames rendered. First exact helper method rejected; independent hinge candidate also fails contacts. Source-vs-fitted comparison identifies inherited dental intersections, changing the next action to dental/cavity structure repair rather than proxy/strength sweeps.','previousGoalTurnClassification':'progress: user-requested v6 goal prompt and entry rules saved and pushed; no model progress claimed.','workingReviewSource':str(S.parent/manifest['workingReviewSource']),'workingReviewSha256':manifest['workingReviewSha256'],'oralResearchSource':build['output'],'oralResearchSha256':build['outputSha256'],'oralMotionReview':motion['asset'],'oralMotionReviewSha256':motion['sha256'],'latestEvidence':str(E/'female-next-r0024.visual-audit.json'),'liveJobHandles':[],'doNotRepeat':['Downloading or reindexing the already archived official oral assets.','Per-pose proxy adaptation scale for teeth: upper jaw would stretch despite static upper helpers.','Claiming native lower helper transfer is rigid: 0.711mm residual exceeds the original 0.5mm gate.','Promoting an independent hinge because its control plays: actual body/gingival/tongue/dental contact gates fail.','Repeated open-weight, global dental shrink or positional sweeps as a substitute for neutral contact topology.','Previously stopped annulus, covering strips, darkening, infinite root/ear pushing and hair tip-only schemes.'],'remainingGates':['r24 oral research has unresolved dental/tongue/lining contacts and is not adopted into r23 working head.','Mouth neutral form, natural expression and continuous collision remain incomplete.','Blink closure and scalp hair appearance/self/complete dynamics remain incomplete.','Full body/clothes, specified motions, engine/LOD/performance and user female acceptance incomplete.'],'nextAction':next_action,'overallCharacterScore':None}
    save(E/'continuation.json',continuation)
    manifest.update({'latestStudyRevision':'female-next-r0024','latestStudyStatus':'ORAL_LAYER_AND_RIGID_JAW_RESEARCH_CONTACT_FAILED_NOT_PROMOTED','latestStudyEvidence':str(E/'female-next-r0024.visual-audit.json'),'latestContinuation':str(E/'continuation.json'),'oralResearchSource':'source/'+Path(build['output']).name,'oralResearchSha256':build['outputSha256'],'oralMotionReviewSource':'source/'+Path(motion['asset']).name,'oralResearchScope':'Editable upper/lower teeth, continuous gingival lining and tongue with fixed-neutral adaptation and independent rigid hinge. Same-condition images and safe-mode sampled playback verified. Contact gates fail; research only, no working head/runtime promotion.','nextRequiredWork':next_action});save(manifest_path,manifest)
    rights=('Aevrynd r0024 oral graphical-data provenance\n\nSource: https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip\nOBJ/MHCLO/MHMAT original files explicitly declare release under CC0 in September 2020. Original credits: Data Collection AB, Joel Palmius, Jonas Hauquier. Archive/member hashes and HTTP-range/CRC evidence are in r0024-download-provenance.json. Original headers and raw textures retained unchanged. No MPFB program or external shader code copied into the engine.\n\nThe three mouth-open sparse graphical targets were archived in r23 from installed MakeHuman core data, already documented as CC0. Their bytes are preserved here for reproducibility without importing an addon. License declaration: https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html\n\nOwn additions: parser, coordinate mapping, partitioning, independent jaw control, Blender PBR approximation, verification and rendering scripts. CC0 source geometry is not claimed as original or exclusive Aevrynd authorship.\n\nB is a failed-contact research model. It does not replace r23, runtime or the website. Open AFN24_ORAL_GEOMETRY and AFN24_ORAL_CONTROLS collections; AFN24_MouthControl custom property open has range 0..0.2. The motion-review file has frames 1..25 at 12fps. Playback is diagnostic, not accepted natural motion. All image files are packed and no external library is linked. Rebuild in the current Aevrynd workspace using Blender and build-female-next-r0024-oral-layers.py -- --hinge; associated historical source/evidence and own helper scripts are required.\n')
    rights_path=S/'oral/r0024-PROVENANCE-AND-REVIEW.txt';rights_path.write_text(rights,encoding='utf8')
    entries=[]
    def copy(src,dest):
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);assert sha(src)==sha(dest);entries.append({'source':str(src),'archive':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size})
    for p in sorted(S.glob('*r0024*')):
        if p.is_file():assert p.stat().st_size<100*1024*1024;copy(p,M/p.name)
    for p in sorted((S/'oral').rglob('*')):
        if p.is_file():copy(p,M/'oral'/p.relative_to(S/'oral'))
    scripts=list((R/'scripts/character-next').glob('*r0024*.py'))+[R/'scripts/character-next/oral_proxy_data.py']
    for p in sorted(scripts):copy(p,REPO/'scripts/character-next'/p.name)
    for p in sorted(E.iterdir()):
        if p.is_file() and p.suffix in ('.json','.png','.gif','.txt','.log') and p.name not in ('git-paths.json','history-file-manifest.json'):
            copy(p,M/(p.name if p.name.startswith('r0024-') else 'r0024-'+p.name))
    copy(manifest_path,M/'female-next.asset.json')
    save(E/'history-file-manifest.json',{'files':entries,'scope':'Rejected oral contact study with original CC0 graphical source, scripts, actual renders, playback and all failed evidence. Integrated r23 and formal runtime/site unchanged.'})
    copy(E/'history-file-manifest.json',M/'r0024-history-file-manifest.json')
    paths=sorted({str(Path(row['archive']).relative_to(REPO)).replace('\\','/') for row in entries});save(E/'git-paths.json',paths)
    print(json.dumps({'files':len(paths),'bytes':sum(r['bytes'] for r in entries),'decision':audit['decision'],'workingHead':manifest['workingReviewRevision'],'study':build['output']},indent=2))
if __name__=='__main__':main()
