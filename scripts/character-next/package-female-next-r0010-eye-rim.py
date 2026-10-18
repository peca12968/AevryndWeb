"""Save strict local review, provenance, continuation state and exact history files."""
import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0010-eye-rim'; S=R/'engine/assets/characters/female-next/source'
REPO=R/'sites-engine-journey'; H=REPO/'assets-source/aevrynd-character/female-next';M=S.parent/'female-next.asset.json'
verify=json.loads((E/'saved-collision-verification.json').read_text()); selected=next(v for v in verify['results'] if v['label']=='c-spaced-lashes');assert selected['status']=='PASS_TESTED_STATIC_POSES'
report_path=E/'female-next-r0010-c-spaced-lashes.report.json'; report=json.loads(report_path.read_text()); candidate=Path(report['output']);assert hashlib.sha256(candidate.read_bytes()).hexdigest()==selected['fileSha256']==report['sha256']
for view in ('eyes','face','oblique'):
    shutil.copy2(R/f'Evidence/character-female-next/r0009-optics/a-slab-thickness-{view}-neutral.png',E/f'baseline-{view}-neutral.png')
for name in ('r0010-eye-rim-inspection.log','r0010-eye-rim-inspection-details.log'):
    source=E.parent/name
    if source.exists():shutil.copy2(source,E/name)
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',25);panel=Image.new('RGB',(1400,1400),(22,25,30));draw=ImageDraw.Draw(panel)
for y,label,name in [(0,'BEFORE / r0009 - bare eyelid and no lashes','baseline-eyes-neutral.png'),(700,'AFTER / r0010 - skin-bound lashes and wet rim / research only','c-spaced-lashes-eyes-neutral.png')]:
    draw.text((22,y+10),label,font=font,fill='white');im=Image.open(E/name).convert('RGB');assert im.size==(1400,650);panel.paste(im,(0,y+50))
panel.save(E/'r0010-reviewed-comparison.png')
minimum=min(v['bodyVertexSampleMinimumGapM'] for p in selected['poses'].values() for v in p['parts'].values())
audit={'revision':'female-next-r0010','status':'RETAIN_C_AS_PARTIAL_HEAD_COMPONENT_STUDY_NOT_PHOTOREAL','selectedVariant':'c-spaced-lashes',
 'variantDecisions':{'a-rim-lashes':'REJECTED_VISUAL: technically separated but repetitive equal-spacing comb appearance.','b-organic-lashes':'REJECTED_COLLISION: 1772 inter-strand triangle pairs at neutral; no body or eye crossings.','c-spaced-lashes':'RETAIN_RESEARCH_ONLY: organic variation with 43 skin-projected root relocations, 220 hairs preserved, zero tested triangle intersections.'},
 'reviewedImages':['a-rim-lashes-eyes-neutral.png','b-organic-lashes-eyes-neutral.png','c-spaced-lashes-eyes-neutral.png','c-spaced-lashes-oblique-neutral.png','c-spaced-lashes-profile-neutral.png','c-spaced-lashes-face-turn-right.png','c-spaced-lashes-alternate-light-eyes-neutral.png'],
 'visibleImprovement':'Distinct tapered lash fibres and their varying lengths/directions remove the completely bare eye rim. Narrow wetness region follows the original skin surface. No lighting or exposure change in standard comparisons.',
 'strictLocalAssessment':{'component':'Eyelash appearance only','estimatedScore':58,'uncertaintyPoints':10,'measurement':False,'reason':'Visible fibre variation is an improvement, but the result remains sparse, excessively fine and pale in side light; clump pattern and similar curls are still procedural. It is below the 80-point release threshold. This is a subjective evidence-based estimate, not an objective realism metric.'},
 'hardLimits':['No sculpted caruncle volume.','No blink keys, eyelid deformation or swept motion qualification.','Wetline is a skin material region, not a separate tear-meniscus volume.','Eyebrows, skin maps and scalp hair are missing.','Head still looks like a clay mannequin and cannot receive a full-character score.','Source is high-resolution; engine LOD and performance are untested.'],
 'minimumSampledLashVertexBodyGapM':minimum,'distanceScope':'Vertices to body triangles only. Exact triangle-crossing tests are separate; no exact all-surface gap or continuous-motion bound.',
 'overallCharacterScore':None,'formalPromotion':False,'enginePromotionApproved':False,'websitePromotionApproved':False,
 'nextAction':'Continue the complete-head milestone with eyebrow fibres, skin material/maps and anatomical inner-eye sculpting. Prepare a native-to-evaluated facial deformation transfer and regenerate skin-bound lashes before qualifying blinking. Do not keep tweaking this static lash style.'}
(E/'female-next-r0010-eye-rim.visual-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
for path,status in [(E/'female-next-r0010-eye-rim.report.json','REJECTED_VISUAL_COMB_PATTERN'),(E/'female-next-r0010-b-organic-lashes.report.json','REJECTED_INTER_STRAND_COLLISION')]:
    data=json.loads(path.read_text());data['status']=status;data['decisionEvidence']='female-next-r0010-eye-rim.visual-audit.json';path.write_text(json.dumps(data,indent=2)+'\n')
report.update({'status':audit['status'],'technicalVerification':'saved-collision-verification.json','visualAudit':'female-next-r0010-eye-rim.visual-audit.json','minimumSampledLashVertexBodyGapM':minimum,'overallCharacterScore':None,'localAppearanceEstimate':audit['strictLocalAssessment'],
 'collisionEvidenceScope':'Five sampled static poses, not blinking or continuous motion. Body and original optical geometry/deform weights match r0009; closed-solid body/eye proof inherited through r0009 saved verification.',
 'inheritedSourceEvidence':{'path':str(R/'Evidence/character-female-next/r0009-optics/saved-optics-verification.json'),'sha256':hashlib.sha256((R/'Evidence/character-female-next/r0009-optics/saved-optics-verification.json').read_bytes()).hexdigest()},
 'semanticRegionExportNote':'AFN10_EyelidWetlineRegion is a non-deforming semantic vertex group. Exporters must map only actual rig-bone groups as skin weights; the wetline also exists as a point-domain shader attribute.',
 'sourceStatistics':{'bodyVertices':214050,'bodyTriangles':428096,'opticalTriangles':30528,'lashTriangles':28160,'rigBones':55,'fileBytes':candidate.stat().st_size},
 'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None}})
report_path.write_text(json.dumps(report,indent=2)+'\n')
(E/'references.json').write_text(json.dumps({'references':[{'url':'https://static.makehumancommunity.org/about/concepts/basemesh.html','access':'Opened official documentation','usedFor':'Native helper geometry interpretation; original CC0 base from r0005 is preserved.'},{'url':'https://studio.blender.org/training/facial-rigging/eyelids-ribbon-mesh/','access':'Search discovered official training page; full fetch failed. No inaccessible content quoted or relied on.'}],
 'newAssetOrigin':'Aevrynd-authored tapered lash geometry, skin-triangle attachment records and wet-rim surface mask. No new downloaded mesh, texture or third-party code.'},indent=2)+'\n')
manifest=json.loads(M.read_text());manifest.update({'latestStudyRevision':'female-next-r0010','latestStudyStatus':audit['status'],'headDetailResearchSource':'source/'+candidate.name,'headDetailResearchScope':'Skin-bound lashes and wet-rim material region only; five static poses passed. No blink, complete head, runtime or website promotion.','latestStudyEvidence':str(report_path),'nextRequiredWork':audit['nextAction']});M.write_text(json.dumps(manifest,indent=2)+'\n')
(E/'continuation.json').write_text(json.dumps({'stage':'B_COMPLETE_HEAD_IN_PROGRESS','nextResearchInput':str(candidate),'latestFormalSourceUnchanged':'female-next-r0001','workingFoundationUnchanged':'female-next-r0005','collisionAuthority':'r0008 closed-solid source + r0009/r0010 unchanged-body proof + r0010 new-lash verification',
 'liveJobHandles':[],'completed':['Surface-derived skin rim and wetness region','220 tapered lashes in four named mesh layers','Natural-spacing repair: 43 root relocations, no removed hairs','Five static poses verified including lash self/cross collisions','Whole-face/profile/turn/alternate-light visual review'],
 'rejected':['a: equal-spacing comb appearance','b: inter-strand intersection'],
 'nextAction':audit['nextAction'],'remainingLimits':audit['hardLimits'],'doNotRepeat':['No further static lash parameter sweeps.','Do not claim static separation proves blinking.','Do not apply the 58-point lash-only estimate to the whole character.'],'rootBindingFile':'c-spaced-lashes-lash-bindings.json'},indent=2)+'\n')
for p in E.glob('*.json'):json.loads(p.read_text())
files=[]
def mirror(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);files.append(dst.relative_to(REPO).as_posix())
for name in ['aevrynd-female-next-r0010-a-rim-lashes-study.blend','aevrynd-female-next-r0010-b-organic-lashes-study.blend','aevrynd-female-next-r0010-c-spaced-lashes-study.blend']:mirror(S/name,H/name)
mirror(M,H/M.name)
for p in sorted(E.iterdir()):
    if p.suffix in ('.json','.png','.log') and p.name!='history-files.json':mirror(p,H/(p.name if p.name.startswith('r0010-') else 'r0010-'+p.name))
for name in ['inspect-female-next-r0010-eye-rim.py','build-female-next-r0010-eye-rim.py','repair-female-next-r0010-lash-spacing.py','verify-female-next-r0010-eye-rim.py','review-female-next-r0010-eye-rim.py','package-female-next-r0010-eye-rim.py']:mirror(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
(E/'history-files.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps({'files':len(files),'status':audit['status'],'minimumSampledLashBodyGapMicrons':minimum*1e6,'localLashAppearanceOnlyScore':58,'wholeCharacterScore':None,'candidate':str(candidate)}))
