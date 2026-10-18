"""Retain bounded free-lock volume research with explicit crown/contact limits."""
import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0017-volume-locks';C=E/'c-exact-crown-transition'
REPO=R/'sites-engine-journey';H=REPO/'assets-source/aevrynd-character/female-next';M=S.parent/'female-next.asset.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(name,data): (E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
    build=read(C/'saved-build-verification.json');surface=read(C/'saved-surface-verification.json');binding=read(C/'authoring-binding-verification.json');crown=read(C/'crown-invariant-verification.json')
    assert surface['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(surface['poses'])==5
    assert crown['status']=='PASS_EXACT_SOURCE_CROWN' and binding['status']=='PASS_EXACT_ROOT_BINDING_INHERITANCE'
    assert sha(build['output'])==build['outputSha256']==surface['candidateSha256']==binding['sourceSha256']==crown['sourceSha256']
    assert read(E/'b-crown-transition/crown-invariant-verification.json')['status']=='FAIL_EXACT_CROWN_INVARIANT'
    controlRows=[]
    for baselinePath,candidatePath in ((E/'baseline-renders.json',C/'candidate-c-renders.json'),(E/'baseline-side-light-renders.json',C/'candidate-c-side-light-renders.json')):
        baseline,candidate=read(baselinePath),read(candidatePath);assert candidate['sourceSha256']==build['outputSha256']
        assert len(baseline['renders'])==len(candidate['renders'])
        for a,b in zip(baseline['renders'],candidate['renders']):
            assert {k:v for k,v in a.items() if k!='path'}=={k:v for k,v in b.items() if k!='path'}
            controlRows.append({'baseline':a['path'],'candidate':b['path'],'sameCameraLensResolutionRendererViewExposureAndLights':True})
    save('render-controls-verification.json',{'status':'PASS_PAIRED_STANDARD_AND_SIDE_LIGHT_CONTROLS','pairs':controlRows,'scope':'Unmodified original light setup and separately labelled all-light 90-degree rotation; no exposure/material changes. Geometry can legitimately change reflected light/shadows.'})
    font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',25);small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',18)
    panel=Image.new('RGB',(1400,780),(19,22,27));draw=ImageDraw.Draw(panel)
    for i,(path,title,subtitle) in enumerate(((E/'baseline-oblique.png','r0014 / original control','Same face, roots, counts, material and lighting'),(C/'candidate-c-oblique.png','r0017 C / volume research','24 master locks; preserved original crown'))):
        panel.paste(Image.open(path).convert('RGB').resize((700,700),Image.Resampling.LANCZOS),(700*i,80));draw.text((700*i+15,12),title,font=font,fill='white');draw.text((700*i+15,47),subtitle,font=small,fill=(215,215,215))
    panel.save(E/'r0017-oblique-comparison.png')
    save('crown-proof-scope.json',{'scope':'Exact identity applies to source-domain crown control vertices (source z >= 1.515 m), separately for guides and final children. This is not a claim that every continuous boundary-crossing segment, reflection or rendered pixel is identical to r0014. All candidate segments are separately included in the five-pose capsule checks.'})
    grid=Image.new('RGB',(1800,1290),(19,22,27));draw=ImageDraw.Draw(grid)
    for col,view in enumerate(('face','oblique','profile')):
        draw.text((col*600+15,12),view+' / r0014 top, r0017 C bottom',font=small,fill='white')
        for row,path in enumerate((E/f'baseline-{view}.png',C/f'candidate-c-{view}.png')):grid.paste(Image.open(path).convert('RGB').resize((600,600),Image.Resampling.LANCZOS),(col*600,50+row*620))
    grid.save(E/'r0017-three-view-comparison.png')
    segments=sum(x['segments'] for row in surface['poses'].values() for x in row['body'].values())
    minimum=min(x['minimumCapsuleClearanceLowerBoundM'] for row in surface['poses'].values() for x in row['body'].values())
    next_action=('Use r0017 C as a retained offline full-groom research source, with r0014 kept as the crown/root/control reference. Free side lengths now have curved, separated locks; the hair is still visibly artificial, with a zipper-like part, hard frontal/temporal edge, abrupt side transition/highlights and hard tips. Do not raise an overall character score or call this complete hair/dynamics acceptance. Freeze this bounded volume study instead of running a fourth style candidate. Next move the complete-head milestone forward through the visibly weak eyebrow/eye-area appearance: inspect the actual brow shader, fibre radius/coverage and reference pigment under fixed lighting, distinguish material versus geometry causes with a minimal diagnostic, then make one evidence-based face candidate while keeping skin albedo/exposure and retained hair fixed. Review the entire face as well as close-ups. Keep hairline/part and the side-transition defect on the remaining visual list; do not repeat r0016 tip-only trimming or r0017 unbounded master attraction through the crown. r0015 wind is only an old-r0014 48-guide diagnostic, not a motion certificate for this new groom. Before returning to head turning, replace the infeasible single convex root-transition proxy with actual-body/SDF contact or justified decomposition; no stretch-limit/iteration sweeps. Full expressions/oral structures, whole body/clothes, complete hair dynamics/self contact and native runtime/LOD/performance remain outstanding. Female user acceptance is required before male work.')
    audit={'revision':'female-next-r0017','status':'FREE_LOCK_VOLUME_RESEARCH_RETAINED_EXACT_CROWN_STATIC_SCOPE_ONLY','selectedCandidate':'C','source':str(S/'aevrynd-female-next-r0014-c-review.blend'),'workingReviewSource':build['output'],
        'candidateDecisions':{'A':'VISUALLY_REJECTED: full-field 24-master attraction adds readable side flow but overinflates/scallops the crown in profile, despite the static surface gate passing.','B':'REJECTED_EXACT_CROWN_INVARIANT: height-faded attraction improves the crown visually, but shell/child interpolation still moves 5 guide and 13,900 child CVs in the declared frozen crown region. Static collision is separate and passed.','C':'RESEARCH_RETAINED: preserve exact original crown in guides and final children, retaining curved free-length locks. Same-camera front/oblique/profile and side-light views show the lower flow change. Still unqualified as photorealistic hair or a complete character.'},
        'actualVisibleGain':['Curved side-lock flow and front/side depth separation replace part of the previous uniform curtain.','Exact original upper crown restored instead of A scallops; this is regression control, not a claim of improved original hairline/part.'],
        'strictHairAppearanceEstimate':{'score':50,'uncertaintyPoints':10,'scope':'Subjective static appearance of r0017 C in complete-head front/oblique/profile and alternate lighting, not the complete hair/dynamics category. No score increase claimed; the flow gain is offset by obvious remaining defects.','deductions':['Hairline/temporal cutoff and zipper-like part remain artificial.','The transition into free locks produces sharp local bends/highlight ridges in profile.','Ends and glossy bands still look too uniform and sheet-like.','No accepted full dynamics, self contact or runtime rendering.']},
        'overallCharacterScore':None,'verified':{'masterLocks':24,'guides':424,'fibres':build['fibres'],'points':build['points'],'headSkinMaterialsLightsRadiiCountsHeld':True,'exactCrownArrays':crown['arrays'],'rootBindingChecks':binding['childRootsChecked'],'staticPoses':list(surface['poses']),'bodySegmentObservations':segments,'minimumConservativeBodyClearanceLowerBoundM':minimum,'bodySurfaceScope':'Complete POLY capsules using maximum endpoint radius and 1 um numerical allowance; conservative lower bound, not exact global distance. Optical/brow/lash surface separation also checked.','sourceGeometrySha256':build['outputSha256']},
        'remainingGates':['Not photorealistic; stated hair defects and weak face/brow appearance remain.','No hair/hair self contact, wind/turn-stop/continuous proof for this new groom.','No expressions/oral completeness, whole-body/clothes, native runtime/LOD/performance or final female acceptance.'],'nextAction':next_action,'runtimePromotionApproved':False,'websitePromotionApproved':False}
    save('female-next-r0017-volume.visual-audit.json',audit)
    save('continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','lastGoalTurnClassification':'progress','classificationReason':'Three bounded real Blender volume candidates; A crown regression and B exact-region failure rejected. C restores exact crown/roots, passes complete five-pose surface checks, and provides visible side-lock depth/flow in controlled multi-view/alternate-light renders. No photoreal or overall-score promotion.','currentFullGroomInput':build['output'],'comparison':str(E/'r0017-oblique-comparison.png'),'authoringDescriptor':binding['descriptor'],'liveJobHandles':[],'nextAction':next_action,'doNotRepeat':['Tip-only trims as a cure for the whole sheet-like mass.','Unbounded master attraction through the crown.','Assuming unchanged guide crown implies unchanged interpolated child crown.','The infeasible single enclosing turning-root proxy or iteration/stretch sweeps.'],'remainingGates':audit['remainingGates'],'overallCharacterScore':None})
    save('references.json',{'primarySource':'https://www.sidefx.com/tutorials/grooming-and-rendering-realistic-hair/','usedFor':'Guide versus strand structure and primary clumping concepts, studied in the preceding turn. No downloaded/copy-transferred source art, code, screenshots or new software dependency.','implementation':'Locally authored 24-master clustering, volumetric field, crown-region constraints, child-delta transport and verification; existing CC0 source provenance remains r0014.'})
    save('orchestration-note.json',{'initialAWrapperExit':8,'cause':'PowerShell property collection .Count was read without array materialization, incorrectly rejecting a completed five-pose PASS report after Blender exited 0.','resolution':'Read authoritative JSON, used @(...PSObject.Properties).Count; resumed render/export without rerunning the already passed collision check.','modelOrCollisionFailure':False})
    manifest=read(M);assert manifest['runtimeAsset'] is None and manifest['currentSourceRevision']=='female-next-r0001'
    manifest.update({'latestStudyRevision':'female-next-r0017','latestStudyStatus':audit['status'],'latestStudyEvidence':str(E/'female-next-r0017-volume.visual-audit.json'),'hairResearchSource':'source/'+Path(build['output']).name,'hairResearchStatus':'RETAIN_FREE_LOCK_VOLUME_EXACT_CROWN_STATIC_SCOPE_ONLY','hairResearchScope':'24 primary master locks with curved free-length volume. Original crown region, roots, radii, counts and head/skin/light state retained exactly; full 21,086 fibres/body/optical/brow/lash surface checks in five static poses. Still artificial; self contact, dynamics and runtime not qualified.','hairAuthoringDescriptor':'source/'+Path(binding['descriptor']).name,'hairMotionResearchScope':'r0015 is an old-r0014 48-guide fixed-head wind diagnostic only, not proof for r0017 hair. Turning rejected; no complete new-groom dynamics/self-contact qualification.','hairMaterialResearchScope':'r0014 Huang material comparison is retained on old r0014 geometry; not a matching-geometry r0017 material or runtime proof.','nextRequiredWork':next_action})
    M.write_text(json.dumps(manifest,indent=2)+'\n')
    files=[]
    def mirror(p,dest):
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);files.append(dest.relative_to(REPO).as_posix())
    for p in sorted(S.glob('aevrynd-female-next-r0017-*')):
        if p.suffix in ('.blend','.npz','.json'):assert p.stat().st_size<100_000_000;mirror(p,H/p.name)
    mirror(M,H/M.name)
    for folder,prefix in ((E,'r0017-'),(E/'b-crown-transition','r0017-b-'),(C,'r0017-c-')):
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix in ('.json','.png') and p.name!='history-files.json':
                if p.suffix=='.json':read(p)
                mirror(p,H/(p.name if p.name.startswith('r0017-') else prefix+p.name))
    for p in sorted(E.parent.glob('r0017*.log')):mirror(p,H/p.name)
    for name in ('build-female-next-r0017-volume-locks.py','export-female-next-r0017-groom.py','package-female-next-r0017-volume-locks.py'):mirror(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
    save('history-files.json',files)
    print(json.dumps({'files':len(files),'status':audit['status'],'bodySegmentObservations':segments,'strictStaticHairEstimate':50,'overallScore':None}))
if __name__=='__main__':main()
