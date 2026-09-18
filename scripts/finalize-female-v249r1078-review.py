"""Package r1078 visual, invariant, collision and performance gates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall-sweep.study.json"
VISUAL = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.visual-audit.json"
INVARIANT = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.invariant-audit.json"
COLLISION = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1078-eyelid-inner-wall"
REVIEW_DIR = ASSETS / "reviews/v249r1078-eyelid-inner-wall"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1078.jpg"

variants = (
    ("a-control", "control"),
    ("b-one-ring-forward-0.12", "one ring 0.12 mm"),
    ("c-two-ring-forward-0.22", "SELECTED two ring 0.22 mm"),
    ("d-two-ring-forward-0.32", "rejected over-closed 0.32 mm"),
)
views = (("eye-front", "eye front"), ("eye-oblique", "eye oblique"), ("face-front", "face front"), ("face-three-quarter", "face 3/4"))
sheet = Image.new("RGB", (1620, 2020), (15, 15, 15))
draw = ImageDraw.Draw(sheet)
draw.text((15, 6), "Aevrynd v249r1078 | collision-safe eyelid inner walls | LOCAL PARTIAL PASS | eyes 38/100", fill=(242, 242, 242))
for row, (variant, variant_label) in enumerate(variants):
    for column, (view, view_label) in enumerate(views):
        image = Image.open(OUT / f"{variant}-{view}.png").convert("RGB")
        image.thumbnail((390, 480), Image.Resampling.LANCZOS)
        x, y = 15 + column * 400, 30 + row * 495
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + 385, y + 25), fill=(10, 10, 10))
        draw.text((x + 5, y + 5), f"{variant_label} | {view_label}", fill=(240, 240, 240))
sheet.save(REVIEW, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
visual = json.loads(VISUAL.read_text(encoding="utf-8"))
invariant = json.loads(INVARIANT.read_text(encoding="utf-8"))
collision = json.loads(COLLISION.read_text(encoding="utf-8"))
selected = next(item for item in study["variants"] if item["label"] == study["selectedVariant"])
performance_pass = (
    invariant["checks"]["materialSlotsIdentical"] and invariant["checks"]["modifiersIdentical"]
    and invariant["checks"]["objectCountIdentical"] and selected["patch"]["addedVertices"] == 180
    and selected["patch"]["addedFaces"] == 180
)
study.update({
    "strictEyesAndEyelidsScore100": 38,
    "strictFullHeadScore100": 40,
    "visualAudit": str(VISUAL), "invariantAudit": str(INVARIANT), "collisionAudit": str(COLLISION), "review": str(REVIEW),
    "collisionStatus": collision["status"], "invariantStatus": invariant["status"],
    "performanceStatus": "PASS_PLUS_180_VERTICES_180_FACES_NO_OBJECT_MATERIAL_SLOT_MODIFIER_OR_DRAW_CALL_DELTA" if performance_pass else "FAIL",
    "finding": "The selected two-ring 0.22 mm support wall preserves the 45-edge outer aperture silhouette, adds 180 fully weighted vertices and 180 faces, and reduces the fixed-view bright low-saturation sclera proxy by 8.24% left and 7.51% right. All four pose frames, mouth-open, smile, body self-collision and 14 face-attachment gates pass. The 0.32 mm variant is rejected as visually over-closed. Canthus holes, uniform lid contour and rigid iris/gaze still prevent hero quality.",
    "candidateStatus": "LOCAL_EYELID_STRUCTURE_PASS_VISUAL_PARTIAL",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestTargetNativeEyelidTechnicalCandidate"] = "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
current["latestTargetNativeEyelidStudy"] = "female-v249-mainline-r1078-eyelid-inner-wall-sweep.study.json"
current["latestTargetNativeEyelidAudit"] = "female-v249-mainline-r1078-eyelid-inner-wall.visual-audit.json; female-v249-mainline-r1078-eyelid-inner-wall.invariant-audit.json; female-v249-mainline-r1078-eyelid-inner-wall.collision-audit.json"
current["latestTargetNativeEyelidReview"] = "reviews/v249r1078-eyelid-inner-wall/contact-sheet-r1078.jpg"
current["latestTargetNativeEyelidStatus"] = "R1078_LOCAL_EYELID_STRUCTURE_PASS_VISUAL_PARTIAL_SCORE_38; selected two-ring 0.22mm inner wall preserves the 45-edge aperture silhouette, reduces the bright sclera proxy 8.24% left and 7.51% right, adds 180 fully weighted vertices/faces, preserves 35 shape keys and passes four-frame, expression, self and 14-attachment collision gates. No object, material slot, modifier or draw-call delta; website v83 remains unchanged."
current["latestFullHeadStatus"] = "R1078_STRICT_FULL_HEAD_40_OF_100_HERO_FAIL; eyes/lids improve 34 to 38 through physically connected inner walls, moving the weighted full-head score from 39 to 40. Canthus holes, uniform lid contour and rigid iris/gaze remain; hairline 32 and skin 36 are still major blockers. Website v83 is unchanged."
current["nextFaceTopologyWork"] = "Use r1078 as the eyelid thickness baseline for r1079. Close the medial/lateral canthus holes and introduce anatomically asymmetric upper/lower lid contour while preserving the 45-edge outer silhouette, 35 shape keys, zero eye/lash overlap, zero body self-collision and the no-new-draw-call gate. Then re-evaluate iris depth and gaze rigidity."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

refinement_path = ROOT / "scripts/CHARACTER-REFINEMENT.md"
entry = "### v249r1078 collision-safe eyelid inner walls\n- Preserved the current 45-edge outer aperture silhouette and tested one-ring 0.12 mm plus two-ring 0.22/0.32 mm weighted inner walls. The selected 0.22 mm wall reduces the fixed-view bright sclera proxy 8.24% left and 7.51% right; 0.32 mm is technically clean but visually over-closed. The initial inward +Y direction intersected the corneas and was rejected before the collision-safe forward sweep.\n- The candidate adds 180 fully weighted vertices and 180 faces with all 35 shape keys compatible. Original vertices, weights and face prefix remain bit-identical; four rig frames, mouth-open, smile, body self-collision and 14 face attachments report zero overlap. Eyes/lids rise 34 to 38 and strict full-head 39 to 40, still below hero quality because canthus closure, lid contour and gaze remain weak. Website v83 remains unchanged.\n"
refinement = refinement_path.read_text(encoding="utf-8")
if entry not in refinement:
    refinement_path.write_text(refinement.rstrip() + "\n\n" + entry, encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "eyesScore": 38, "fullHeadScore": 40, "collision": collision["status"], "invariants": invariant["status"], "performance": study["performanceStatus"], "status": study["candidateStatus"]}, indent=2))
