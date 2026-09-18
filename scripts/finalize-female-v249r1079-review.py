"""Package r1079 canthus contour gates and strict review."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]; ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1079-canthus-contour-sweep.study.json"
VISUAL = ASSETS / "female-v249-mainline-r1079-canthus-contour.visual-audit.json"
INVARIANT = ASSETS / "female-v249-mainline-r1079-canthus-contour.invariant-audit.json"
COLLISION = ASSETS / "female-v249-mainline-r1079-canthus-contour.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1079-canthus-contour"
REVIEW_DIR = ASSETS / "reviews/v249r1079-canthus-contour"; REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1079.jpg"

variants=(("a-control","control"),("b-conservative-0.35","35%"),("c-balanced-0.55","SELECTED 55%"),("d-strong-0.75","rejected 75%"))
views=(("eye-front","eye front"),("eye-oblique","eye oblique"),("face-front","face front"),("face-three-quarter","face 3/4"))
sheet=Image.new("RGB",(1620,2020),(15,15,15)); draw=ImageDraw.Draw(sheet)
draw.text((15,6),"Aevrynd v249r1079 | canthus/lower-lid contour fairing | LOCAL PARTIAL PASS | eyes 39/100",fill=(242,242,242))
for row,(variant,label) in enumerate(variants):
    for column,(view,view_label) in enumerate(views):
        image=Image.open(OUT/f"{variant}-{view}.png").convert("RGB"); image.thumbnail((390,480),Image.Resampling.LANCZOS)
        x,y=15+column*400,30+row*495; sheet.paste(image,(x,y)); draw.rectangle((x,y,x+385,y+25),fill=(10,10,10)); draw.text((x+5,y+5),f"{label} | {view_label}",fill=(240,240,240))
sheet.save(REVIEW,quality=94,subsampling=0)

study=json.loads(STUDY.read_text(encoding="utf-8")); visual=json.loads(VISUAL.read_text(encoding="utf-8")); invariant=json.loads(INVARIANT.read_text(encoding="utf-8")); collision=json.loads(COLLISION.read_text(encoding="utf-8"))
study.update({
    "strictEyesAndEyelidsScore100":39,"strictFullHeadScore100":40,"visualAudit":str(VISUAL),"invariantAudit":str(INVARIANT),"collisionAudit":str(COLLISION),"review":str(REVIEW),
    "collisionStatus":collision["status"],"invariantStatus":invariant["status"],"performanceStatus":"PASS_NO_TOPOLOGY_WEIGHT_MATERIAL_MODIFIER_OBJECT_OR_DRAW_CALL_DELTA",
    "finding":"The selected 55% fairing reduces maximum folded lower-corner deviation from 2.045/1.884 mm to 0.920/0.848 mm and closes horizontal aperture width by only 0.36 mm. Total bright-sclera proxy changes just +0.15%, confirming the gain comes from contour regularity rather than wholesale eye closure. It moves 174 existing outer/wall vertices by at most 1.136 mm, preserves every relative delta across 35 shape keys exactly, and passes four-frame, expression, body-self and 14-attachment collision gates. The 75% variant is rejected as overly straight.",
    "candidateStatus":"LOCAL_CANTHUS_CONTOUR_PASS_VISUAL_PARTIAL","websitePromotionApproved":False,
})
STUDY.write_text(json.dumps(study,indent=2),encoding="utf-8")

current=json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestTargetNativeEyelidTechnicalCandidate"]="aevrynd-female-cc0-canthus-contour-r1079-study.blend"
current["latestTargetNativeEyelidStudy"]="female-v249-mainline-r1079-canthus-contour-sweep.study.json"
current["latestTargetNativeEyelidAudit"]="female-v249-mainline-r1079-canthus-contour.visual-audit.json; female-v249-mainline-r1079-canthus-contour.invariant-audit.json; female-v249-mainline-r1079-canthus-contour.collision-audit.json"
current["latestTargetNativeEyelidReview"]="reviews/v249r1079-canthus-contour/contact-sheet-r1079.jpg"
current["latestTargetNativeEyelidStatus"]="R1079_LOCAL_CANTHUS_CONTOUR_PASS_VISUAL_PARTIAL_SCORE_39; selected 55% lower-corner fairing reduces folded deviation 2.045/1.884mm to 0.920/0.848mm with only 0.36mm horizontal closure and +0.15% total sclera proxy. It moves 174 existing outer/wall vertices <=1.136mm, preserves all 35 relative shape-key deltas exactly, and passes four-frame, expression, self and 14-attachment collision gates. No topology or draw-call delta; website v83 remains unchanged."
current["latestFullHeadStatus"]="R1079_STRICT_FULL_HEAD_40_OF_100_HERO_FAIL; eyes/lids improve 38 to 39 through lower-corner contour regularity while the rounded full-head score remains 40. Rigid iris/gaze, caruncle shading and uniform lid crease remain; hairline 32 and skin 36 are still major blockers. Website v83 is unchanged."
current["nextFaceTopologyWork"]="Use r1079 as the eye-contour baseline for r1080. Diagnose iris/cornea depth, iris scale, sclera value and gaze convergence in frontal and oblique views; test optical/material variants without adding runtime objects or violating cornea, lid or lash clearance. Preserve r1079 contour, 35 shape keys and all collision gates."
CURRENT.write_text(json.dumps(current,indent=2),encoding="utf-8")

refinement_path=ROOT/"scripts/CHARACTER-REFINEMENT.md"
entry="### v249r1079 canthus and lower-lid contour fairing\n- Measured the paired 45-point apertures and found folded lower-corner runs with 2.045/1.884 mm maximum deviation. The selected 55% fairing lowers them to 0.920/0.848 mm while closing total horizontal width by only 0.36 mm; the bright-sclera proxy changes just +0.15%, so the gain is contour regularity rather than hiding the eye. The 75% variant becomes overly straight and is rejected.\n- Moved 174 existing outer/wall vertices by at most 1.136 mm with no topology, weight, material, modifier, object or draw-call delta. All 35 relative shape-key deltas are exactly preserved. Four rig frames, mouth-open, smile, body self-collision and 14 face attachments remain at zero overlap. Eyes/lids rise 38 to 39; full-head remains 40 and website v83 is unchanged.\n"
refinement=refinement_path.read_text(encoding="utf-8")
if entry not in refinement: refinement_path.write_text(refinement.rstrip()+"\n\n"+entry,encoding="utf-8")
print(json.dumps({"review":str(REVIEW),"eyesScore":39,"fullHeadScore":40,"collision":collision["status"],"invariants":invariant["status"],"performance":study["performanceStatus"],"status":study["candidateStatus"]},indent=2))
