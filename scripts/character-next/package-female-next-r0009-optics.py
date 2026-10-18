"""Package unretouched comparison evidence and the exact r0009 history file list."""
import json, hashlib, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0009-optics'
REPO=R/'sites-engine-journey'; H=REPO/'assets-source/aevrynd-character/female-next'
S=R/'engine/assets/characters/female-next/source'; M=S.parent/'female-next.asset.json'
verification=json.loads((E/'saved-optics-verification.json').read_text()); assert verification['status']=='PASS'
candidate=Path(verification['candidate']); assert hashlib.sha256(candidate.read_bytes()).hexdigest()==verification['candidateSha256']
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',25)
canvas=Image.new('RGB',(1400,1400),(22,25,30)); draw=ImageDraw.Draw(canvas)
for y,label,name in [(0,'BEFORE / r0008 - implicit sphere, no explicit thickness','baseline-eyes-neutral.png'),(700,'AFTER / r0009 - slab, nominal thickness 0.55 mm','a-slab-thickness-eyes-neutral.png')]:
    draw.text((22,y+10),label,font=font,fill='white'); im=Image.open(E/name).convert('RGB'); assert im.size==(1400,650)
    canvas.paste(im,(0,y+50))
canvas.save(E/'r0009-reviewed-comparison.png')
rois={'left':[313,374,360,381],'right':[1033,374,1080,381]}; counts={}
for label,name in [('before','baseline-eyes-neutral.png'),('after','a-slab-thickness-eyes-neutral.png')]:
    im=Image.open(E/name).convert('RGB'); counts[label]={side:sum(min(p)>180 and max(p)-min(p)<40 for p in im.crop(box).getdata()) for side,box in rois.items()}
audit={'revision':'female-next-r0009','status':'RETAIN_OPTICAL_RESEARCH_ONLY_PARTIAL_VISIBLE_IMPROVEMENT','reviewedRenders':['baseline-eyes-neutral.png','no-cornea-eyes-neutral.png','unit-ior-eyes-neutral.png','no-screen-refraction-eyes-neutral.png','cycles-reference-eyes-neutral.png','trace-scale-eyes-neutral.png','reflection-isolation-eyes-neutral.png','a-slab-thickness-eyes-neutral.png','a-slab-thickness-face-neutral.png','a-slab-thickness-oblique-neutral.png','baseline-alternate-light-eyes-neutral.png','a-slab-thickness-alternate-light-eyes-neutral.png','a-slab-thickness-eyes-gaze-right.png'],
       'visibleGain':'The bright lower-iris crescent is strongly reduced at the locked frontal view and a second lighting setup; entire face remains plainly an unfinished mannequin.',
       'remainingDefects':['Iris still has an artificial smooth/radial appearance and a lower horizontal optical band.','Two large studio-light highlights remain; physically consistent light reflection is not sufficient proof of a realistic eye.','The single open corneal surface is an approximation, not a closed anatomically validated optical volume.','Lid wetline, caruncle, lashes, eyebrows, skin maps and hair are missing.','Blinking and facial expressions are not implemented or qualified.'],
       'localArtifactMetric':{'scope':'Fixed lower-crescent image ROIs only, not a realism score. Threshold: all RGB >180 and channel range <40. Pixel counts depend on this exact image framing.','rectanglesXYXY':rois,'brightNeutralPixels':counts},
       'wholeCharacterScore':None,'enginePromotionApproved':False,'websitePromotionApproved':False,'nextAction':'Build anatomically grounded eyelid rim, wetline/canthus and brow/lash structure; qualify blink; continue the complete-head milestone. Do not keep sweeping cornea scalar parameters.'}
(E/'female-next-r0009-optics.visual-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
report={'revision':'female-next-r0009','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(S/'aevrynd-female-next-r0008-a-tight-study.blend'),'candidate':str(candidate),'candidateSha256':verification['candidateSha256'],
        'status':audit['status'],'hypothesis':'An explicit thin-layer material representation reduces the hard lower-iris crescent caused in part by the Eevee corneal volume approximation.',
        'experiments':{'corneaHidden':'Crescent removed, but no valid final optics.','unitIOR':'Crescent removed, but physically invalid adoption.','screenTransmissionDisabled':'Crescent retained and iris loses transmission.','highQualityThinScreenTrace':'Crescent retained and dark peripheral artifacts appear.','specularIORLevelZero':'Crescent retained. This input does not isolate all reflection in a transmissive Principled BSDF.','cyclesReference':'Hard white crescent absent, but soft optical bands persist. Diagnostic only; no engine switch saved to candidate.','explicitSlabThickness':'Hard white crescent strongly reduced without geometry, light or exposure edits; nominal 0.55mm is an approximation parameter, not a measured shell.'},
        'savedVerification':verification,'technicalLimits':audit['remainingDefects'],
        'collisionScope':verification['collisionScope'],'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None},
        'formalPromotion':False,'overallCharacterScore':None,'visualAudit':'female-next-r0009-optics.visual-audit.json',
        'referenceSearch':{'urls':['https://docs.blender.org/manual/en/4.2/render/shader_nodes/output/material.html','https://docs.blender.org/manual/en/latest/render/eevee/material_settings.html'],'access':'Search discovered official documentation; full-page fetch returned HTTP 402/403. No unverified manual quote used. Settings and result were inspected and measured in the installed Blender.'}}
(E/'female-next-r0009-optics.report.json').write_text(json.dumps(report,indent=2)+'\n')
manifest=json.loads(M.read_text()); manifest.update({'latestStudyRevision':'female-next-r0009','latestStudyStatus':audit['status'],'opticalResearchSource':'source/'+candidate.name,'opticalResearchScope':'Material-only lower-iris artifact reduction. Geometry unchanged from r0008 a-tight; no whole-character, blink, continuous collision or runtime promotion.','latestStudyEvidence':str(E/'female-next-r0009-optics.report.json'),'nextRequiredWork':audit['nextAction']})
M.write_text(json.dumps(manifest,indent=2)+'\n')
(E/'continuation.json').write_text(json.dumps({'stage':'B_COMPLETE_HEAD_IN_PROGRESS','nextResearchInput':str(candidate),'collisionAuthority':'r0008 a-tight + r0009 exact collision-state equality','stoppedJobs':True,'liveJobHandles':[],
 'completed':['Cornea isolation and Cycles reference','Explicit material thickness candidate','Saved-file mesh/rig/lighting/material comparison','Multi-angle and alternate-light visual review'],
 'doNotRepeat':['Do not rerun r0008 full collisions for unchanged meshes.','Do not treat renderer or material correction as completion of a realistic face.','Do not repeat corneal scalar sweeps; move to missing anatomical structures.'],
 'nextAction':audit['nextAction'],'remainingMilestones':['head anatomy and eye rim','skin maps','brows/lashes and hairstyle','blink and facial expressions','body, clothing and motion','isolated engine import/LOD/performance','user acceptance'],'formalAssetsUnchanged':True},indent=2)+'\n')
files=[]
def mirror(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); files.append(dst.relative_to(REPO).as_posix())
mirror(candidate,H/candidate.name); mirror(M,H/M.name)
for p in sorted(E.iterdir()):
    if p.suffix in ('.png','.json','.log') and p.name!='history-files.json':
        mirror(p,H/(p.name if p.name.startswith('r0009-') else 'r0009-'+p.name))
for name in ['diagnose-female-next-r0009-optics.py','reference-female-next-r0009-optics.py','trace-female-next-r0009-optics.py','build-female-next-r0009-optical-thickness.py','verify-female-next-r0009-optics.py','review-female-next-r0009-optics.py','package-female-next-r0009-optics.py']:
    mirror(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
(E/'history-files.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps({'files':len(files),'candidate':str(candidate),'brightPixelCounts':counts,'status':audit['status']}))
