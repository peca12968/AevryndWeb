"""Archive two visually rejected tip studies without promoting either model."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0016-feathered-tips';S=R/'engine/assets/characters/female-next/source'
REPO=R/'sites-engine-journey';H=REPO/'assets-source/aevrynd-character/female-next';M=S.parent/'female-next.asset.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj): (E/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
av=json.loads((E/'saved-prefix-verification.json').read_text());bv=json.loads((E/'b-saved-containment-verification.json').read_text())
assert av['status']=='PASS_EXACT_POLY_PREFIX_RADIUS_CONTRACTION' and bv['status']=='PASS_POLY_PREFIX_AND_TERMINAL_CAPSULE_CONTAINMENT'
for v in (av,bv):assert sha(v['output'])==v['outputSha256']
controls=json.loads((E/'baseline-pilot-renders.json').read_text())['renders']
for name in ('candidate-a','candidate-b'):
    candidate=json.loads((E/(name+'-pilot-renders.json')).read_text())
    expected=av if name=='candidate-a' else bv
    assert candidate['sourceSha256']==expected['outputSha256']
    for a,b in zip(controls,candidate['renders']):
        assert {k:v for k,v in a.items() if k!='path'}=={k:v for k,v in b.items() if k!='path'}
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',24);small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',18)
panel=Image.new('RGB',(2100,778),(20,23,28));draw=ImageDraw.Draw(panel)
for i,(name,title,subtitle) in enumerate((('baseline','Retained r0014','Original complete-head control'),('candidate-a','A / REJECTED','CV-grid cutting adds steps'),('candidate-b','B / REJECTED','Continuous cuts; sheet-like mass remains'))):
    panel.paste(Image.open(E/(name+'-pilot-oblique.png')).convert('RGB'),(i*700,78));draw.text((i*700+18,12),title,font=font,fill='white' if i==0 else (255,154,132));draw.text((i*700+18,45),subtitle,font=small,fill=(220,220,220))
panel.save(E/'r0016-rejected-tip-comparison.png')
next_action=('Keep r0014 C review as the complete static groom. r0016 A and B are visually rejected: local end trimming/taper does not remove the sheet-like main mass. Stop this tip-only method; do not run a third trimming sweep or raise the appearance score. Next build a genuinely volumetric primary/secondary clump layout from r0014 roots, with measurable cross-section/depth variation instead of one common envelope sheet. Establish the intended bob silhouette and lock directions in front/profile/oblique before adding density or fine noise; use one bounded candidate and actual complete-head A/B renders. Keep roots skin-bound and verify whole guide capsules before child expansion; final children need their own checks. If the volume study cannot preserve meaningful contact guarantees, retain it only as rejected diagnostics and change the route architecture. r0015 wind remains 48-guide-only. Before retrying turning, replace the geometrically infeasible single convex root-transition proxy with actual body/SDF contact or justified decomposition; no more iteration-count or stretch-tolerance sweeps. Face detail, expressions, oral components, body/clothes, child/self collision, native runtime and user acceptance remain incomplete. No male or formal runtime/site promotion.')
audit={'revision':'female-next-r0016','status':'BOTH_TIP_CANDIDATES_VISUALLY_REJECTED','source':av['source'],'sourceSha256':av['sourceSha256'],
    'candidateDecisions':{'A':'REJECTED: snapped-to-CV cuts visibly introduce stepped/patchy ends in the same-camera complete-head pilot.','B':'REJECTED: continuous subsegment cuts fix the A quantization defect, but the dense sheet-like hair mass and hard grouped edge remain. Not a sufficient realism gain over r0014.'},
    'actualModelImprovement':'None accepted. The retained full groom and its appearance estimate are unchanged.',
    'technicalFindings':{'A':'Exact old POLY prefixes and reduced radii inherit the five static surface cases.','B':'Existing native curve arrays resized successfully. Complete retained prefixes plus new terminal capsules are contained in the previously verified conservative capsules, including measured float32 roundoff. This is a reusable authoring operation, not a character-quality gain.','BMinimumTerminalContainmentSlackM':min(c['minimumTerminalContainmentSlackAfterRoundoffM'] for c in bv['checks'] if c['minimumTerminalContainmentSlackAfterRoundoffM'] is not None),'radiiAndArrayScope':'All 21,086 curves checked from reopened saved files; packed images and no linked libraries verified.'},
    'visualEvidence':{'comparison':str(E/'r0016-rejected-tip-comparison.png'),'pilotViews':['oblique'],'pilotResolution':[700,700],'inspected':['baseline-pilot-oblique.png','candidate-a-pilot-oblique.png','candidate-b-pilot-oblique.png'],'fullResolutionExpansion':'NOT_RUN: both candidates rejected at early visual gate; no claimed front/profile acceptance.','control':'Same camera, lens, resolution, renderer, color management, exposure and gamma; head/material/lighting controls held by the build checks.'},
    'strictHairAppearanceEstimate':None,'overallCharacterScore':None,'scopeLimits':['No accepted new groom. Original r0014 static surface scope only; no moving hair or self-contact proof.','No new dynamics, expressions, anatomy, runtime, performance or final acceptance evidence.'],
    'nextAction':next_action,'enginePromotionApproved':False,'websitePromotionApproved':False}
save('female-next-r0016-tips.visual-audit.json',audit)
save('continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','lastGoalTurnClassification':'progress','classificationReason':'Two actual Blender candidates saved/reopened and rendered. A exposes control-point quantization, B removes it but fails the appearance gate. Evidence stops tip-only refinements and redirects the next action to volumetric clump layout; no quality gain claimed.','currentFullGroomInput':av['source'],'rejectedCandidates':[av['output'],bv['output']],'liveJobHandles':[],'nextAction':next_action,'doNotRepeat':['CV-grid tip trimming.','Another tip-only trim/taper sweep to fix the uniform-sheet hair mass.','Single enclosing convex proxy through the skin-bound turning root corridor.','Increasing iterations or relaxing stretch to solve geometric infeasibility.'],'remainingGates':audit['scopeLimits']+['Hairline/part, volume, face realism and expressions, oral structures, whole-body/clothes, complete dynamic hair and self contact, native engine performance and user acceptance remain incomplete.'],'overallCharacterScore':None})
save('references.json',{'source':'https://www.sidefx.com/tutorials/grooming-and-rendering-realistic-hair/','author':'Joshua Matthews / SideFX','use':'Conceptual separation of guide shaping/cutting, clumping, and individual strand variation. No third-party code, assets, screenshots or software dependency imported.','outcome':'Local tip-only approach disproved as the next realism solution; preserve observed failures, move to whole volumetric clump structure.'})
save('render-record-note.json',{'note':'The first A and B pilots initially shared a generic candidate-pilot filename. Both were subsequently re-rendered from their saved assets to distinct candidate-a-pilot and candidate-b-pilot names. Archive uses only these unambiguous images/reports; no lost source model or synthetic reconstruction.','earlyGenericPilotReports':'Superseded; not included in this archive.'})
manifest=json.loads(M.read_text());assert manifest['hairResearchSource']=='source/aevrynd-female-next-r0014-c-review.blend'
manifest.update({'latestStudyRevision':'female-next-r0016','latestStudyStatus':audit['status'],'latestStudyEvidence':str(E/'female-next-r0016-tips.visual-audit.json'),'nextRequiredWork':next_action,'rejectedTipStudies':[{'source':'source/'+Path(v['output']).name,'sha256':v['outputSha256'],'decision':'VISUALLY_REJECTED'} for v in (av,bv)]})
M.write_text(json.dumps(manifest,indent=2)+'\n')
files=[]
def mirror(p,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);files.append(dest.relative_to(REPO).as_posix())
for p in sorted(S.glob('aevrynd-female-next-r0016-*')):
    if p.suffix in ('.blend','.npz'):assert p.stat().st_size<100_000_000;mirror(p,H/p.name)
mirror(M,H/M.name)
for p in sorted(E.iterdir()):
    if p.name=='history-files.json' or p.name.startswith('candidate-pilot-'):continue
    if p.suffix in ('.json','.png'):
        if p.suffix=='.json':json.loads(p.read_text())
        mirror(p,H/('r0016-'+p.name if not p.name.startswith('r0016-') else p.name))
for p in sorted(E.parent.glob('r0016*.log')):mirror(p,H/p.name)
for name in ('build-female-next-r0016-feathered-tips.py','build-female-next-r0016-continuous-cut.py','package-female-next-r0016-tip-study.py'):
    mirror(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
save('history-files.json',files)
print(json.dumps({'files':len(files),'decision':audit['status'],'fullGroom':'r0014 unchanged','overallScore':None}))
