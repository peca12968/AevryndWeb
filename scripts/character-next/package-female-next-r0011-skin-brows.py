"""Strict visual review, tone evidence, CC0 provenance and precise Git history packaging."""
import json,hashlib,shutil,statistics,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows';S=R/'engine/assets/characters/female-next/source';REPO=R/'sites-engine-journey';H=REPO/'assets-source/aevrynd-character/female-next';M=S.parent/'female-next.asset.json'
verification=json.loads((E/'saved-collision-verification.json').read_text());assert verification['status']=='PASS_TESTED_STATIC_POSES'
report_path=E/'female-next-r0011-b-ridge-skin-brows.report.json';report=json.loads(report_path.read_text());candidate=Path(report['output']);assert hashlib.sha256(candidate.read_bytes()).hexdigest()==verification['candidateSha256']==report['sha256']
review=json.loads((E/'controlled-review.json').read_text());tone={}
for row in review['records']:
    if row['condition']!='standard':continue
    im=Image.open(row['image']).convert('RGB');values=[]
    for x,y in row['skinReferencePixels']:
        pixels=[im.getpixel((x+dx,y+dy)) for dx in range(-5,6) for dy in range(-5,6)];rgb=[statistics.mean(p[c] for p in pixels) for c in range(3)];values.append({'pixel':[x,y],'meanDisplayRGB':rgb,'displayLuma':sum(c*w for c,w in zip(rgb,[.2126,.7152,.0722]))})
    tone[row['label']]={'sites':values,'meanDisplayLuma':statistics.mean(x['displayLuma'] for x in values)}
tone['changePercent']=100*(tone['b-ridge-skin-brows']['meanDisplayLuma']/tone['baseline']['meanDisplayLuma']-1)
tone['scope']='Same six fixed cheek/forehead sites, 11x11 display-image samples, same camera/lights/exposure. This is display tone, separate from linear albedo calibration; not proof of skin accuracy.'
(E/'display-tone-audit.json').write_text(json.dumps(tone,indent=2)+'\n')
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',25);panel=Image.new('RGB',(2200,1160),(22,25,30));draw=ImageDraw.Draw(panel)
for x,label,name in [(0,'BEFORE / r0010 - clay skin, no brow fibres','baseline-tone-face-neutral.png'),(1100,'AFTER / r0011 - mapped skin and brow fibres','b-ridge-skin-brows-face-neutral.png')]:
    draw.text((x+18,16),label,font=font,fill='white');im=Image.open(E/name).convert('RGB');assert im.size==(1100,1100);panel.paste(im,(x,60))
panel.save(E/'r0011-reviewed-comparison.png')
minimum=min(x['minimumSampledVertexBodyGapM'] for p in verification['poses'].values() for x in p['brows'].values());count=sum(x['hairs'] for x in verification['structures'].values())
audit={'revision':'female-next-r0011','status':'RETAIN_B_AS_MAPPED_SKIN_BROW_RESEARCH_NOT_PHOTOREAL','selectedVariant':'b-ridge-skin-brows',
 'variantDecisions':{'a-skin-brows':'REJECTED_VISUAL: brows too high and sparse. No independent collision acceptance claimed.','b-ridge-skin-brows':'RETAIN_RESEARCH_ONLY: clearer pigment anatomy, reference albedo preserved, improved brow placement/density, static collision gates passed.'},
 'visibleImprovement':['UV-mapped lips, nasal pigment and regional facial colour replace uniform clay albedo.','Brow fibres occupy a narrower, lower anatomical region; 637 independent skin-bound hairs remain visible.'],
 'strictLocalAssessments':[{'component':'Skin appearance','estimatedScore':61,'uncertaintyPoints':10,'reason':'Mapped anatomical colour is a visible improvement. Legacy diffuse still contains baked shadow/scalp pigment; the microrelief is synthetic, and grazing-light realism remains limited.'},{'component':'Eyebrow appearance','estimatedScore':54,'uncertaintyPoints':10,'reason':'Placement and density improved, but the short straight fibres still look etched, pale and procedural. A natural multi-scale groom is not complete.'}],
 'scoreScope':'Subjective component-only estimates with uncertainty, not measured realism or a full-character score. Both remain below the 80-point component release gate.',
 'remainingDefects':['Head hair is not modelled; baked scalp stubble in the diffuse is not 3D hair.','Face anatomy/identity, caruncle and mouth structures remain unfinished.','Legacy diffuse contains baked lighting; it is not a measured, fully de-lit PBR albedo.','Brow stroke regularity and fine/pale appearance remain artificial.','No blink, facial expressions or continuous motion proof.','Procedural micro-bump and regional shader inputs need engine baking/export; no runtime LOD/performance gate passed.'],
 'newBrowHairs':count,'minimumSampledBrowVertexBodyGapM':minimum,'distanceScope':verification['distanceScope'],'displayToneChangePercentAtReferenceSites':tone['changePercent'],
 'overallCharacterScore':None,'enginePromotionApproved':False,'websitePromotionApproved':False,
 'nextAction':'Build actual scalp/hairline, primary hair masses, guide clumps and finer strands as separate layers, then collision-aware motion. Keep working toward full head anatomy and native-to-evaluated facial deformation/blink transfer. Do not spend another round on small static brow parameter sweeps. Skin de-lighting/scalp-pigment cleanup and baking remain required before runtime promotion.'}
(E/'female-next-r0011-skin-brows.visual-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
early=E/'female-next-r0011-skin-brows.report.json';a=json.loads(early.read_text());a.update({'status':'REJECTED_VISUAL_BROW_POSITION_AND_DENSITY','decisionEvidence':'female-next-r0011-skin-brows.visual-audit.json'});early.write_text(json.dumps(a,indent=2)+'\n')
report.update({'status':audit['status'],'technicalEvidence':'saved-collision-verification.json','visualAudit':'female-next-r0011-skin-brows.visual-audit.json','displayToneEvidence':'display-tone-audit.json','localAppearanceEstimates':audit['strictLocalAssessments'],'overallCharacterScore':None,
 'sourceStatistics':{'bodyVertices':214050,'bodyTriangles':428096,'opticalTriangles':30528,'lashTriangles':28160,'browTriangles':sum(x['triangles'] for x in report['brows']),'rigBones':55,'fileBytes':candidate.stat().st_size},
 'externalAssetProvenance':'download-provenance.json','nextAction':audit['nextAction'],'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None}});report_path.write_text(json.dumps(report,indent=2)+'\n')
partial=E/'makehuman-system-assets-cc0.zip.partial'
if partial.exists():(E/'full-pack-download-cancelled.json').write_text(json.dumps({'status':'INTENTIONALLY_CANCELLED','processHandle':'exec session 2166 exited after interrupt, code 1','partialBytes':partial.stat().st_size,'isValidZip':zipfile.is_zipfile(partial),'reason':'Replaced whole-pack transfer with verified HTTP range extraction of two selected graphical asset files. Partial archive excluded from history and deliverables.'},indent=2)+'\n')
(E/'references.json').write_text(json.dumps({'sources':[{'url':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','finding':'Official asset table lists young_asian_female as CC0.'},{'url':'https://static.makehumancommunity.org/about/license.html','finding':'Core graphical assets and program code have separate licenses.'}],
 'localLicenseEvidence':'young_asian_female.mhmat explicitly declares CC0 release in September 2020 and records the original rights holders.','codePolicy':'Only graphical texture and material-description data imported. No MPFB shader/program source copied; Aevrynd skin and brow authoring scripts written independently.','sourceTextureModifications':'Source PNG bytes unchanged. Explicit shader albedo calibration and added region/microrelief inputs are recorded separately.'},indent=2)+'\n')
manifest=json.loads(M.read_text());manifest.update({'latestStudyRevision':'female-next-r0011','latestStudyStatus':audit['status'],'headDetailResearchSource':'source/'+candidate.name,'headDetailResearchScope':'Mapped CC0 skin pigment and new bound brow fibres; static five-pose checks only. No complete character or runtime promotion.','skinResearchSource':'source/'+candidate.name,'latestStudyEvidence':str(report_path),'nextRequiredWork':audit['nextAction']});M.write_text(json.dumps(manifest,indent=2)+'\n')
(E/'continuation.json').write_text(json.dumps({'stage':'B_COMPLETE_HEAD_IN_PROGRESS','nextResearchInput':str(candidate),'liveJobHandles':[],'sourceGeometryAuthority':'r0010 c-spaced-lashes retained exactly; r0011 introduces only new brow geometry and skin shading.',
 'completed':['Verified selected official CC0 texture extraction: CRC32, ETag and SHA256','Native UV pigment mapping and six-site linear albedo calibration','Skin roughness regions and non-displacing authoring microrelief','637 bound brow hairs in two named layers','Fresh saved-file source integrity and five static pose collision checks','Profile/oblique/alternate-light/tone reviews'],
 'rejected':['a: overly high and sparse brows'],'nextAction':audit['nextAction'],'remainingDefects':audit['remainingDefects'],'doNotRepeat':['Do not call baked scalp colour a hair model.','Do not treat legacy diffuse as fully de-lit measured albedo.','Do not retune static lash/brow scalar values indefinitely.','Do not transfer component estimates to the whole character.'],'browBindingFile':'b-ridge-brow-bindings.json','wholeCharacterScore':None},indent=2)+'\n')
for p in E.glob('*.json'):json.loads(p.read_text())
files=[]
def mirror(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);files.append(dst.relative_to(REPO).as_posix())
for name in ['aevrynd-female-next-r0011-a-skin-brows-study.blend','aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend']:mirror(S/name,H/name)
mirror(M,H/M.name)
for p in sorted((S/'textures/makehuman-system-cc0').iterdir()):mirror(p,H/'textures/makehuman-system-cc0'/p.name)
for p in sorted(E.iterdir()):
    if p.suffix in ('.json','.png','.log') and p.name!='history-files.json':mirror(p,H/(p.name if p.name.startswith('r0011-') else 'r0011-'+p.name))
for name in ['fetch-female-next-r0011-skin-assets.py','inspect-female-next-r0011-skin-uv.py','calibrate-female-next-r0011-skin.py','build-female-next-r0011-skin-brows.py','verify-female-next-r0011-skin-brows.py','review-female-next-r0011-skin-brows.py','package-female-next-r0011-skin-brows.py']:mirror(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
(E/'history-files.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps({'files':len(files),'status':audit['status'],'browHairs':count,'minimumSampledGapMicrons':minimum*1e6,'referenceDisplayToneChangePercent':tone['changePercent'],'wholeCharacterScore':None}))
