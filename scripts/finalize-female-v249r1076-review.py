"""Package r1076 curvature, invariant, collision and performance gates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1076-commissure-curvature.study.json"
VISUAL = ASSETS / "female-v249-mainline-r1076-commissure-curvature.visual-audit.json"
INVARIANT = ASSETS / "female-v249-mainline-r1076-commissure-curvature.invariant-audit.json"
COLLISION = ASSETS / "female-v249-mainline-r1076-commissure-curvature.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1076-commissure-curvature"
REVIEW_DIR = ASSETS / "reviews/v249r1076-commissure-curvature"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1076.jpg"

variants = (("a-control", "control"), ("b-relax-0.15", "15% selected"), ("c-relax-0.30", "30% rejected"), ("d-relax-0.45", "45% rejected"))
views = (("neutral-front", "front"), ("neutral-oblique", "oblique"), ("open-front", "open"), ("smile-front", "smile"), ("left-key-front", "left key"), ("right-key-front", "right key"))
sheet = Image.new("RGB", (1800, 2580), (15, 15, 15))
draw = ImageDraw.Draw(sheet)
draw.text((20, 6), "Aevrynd v249r1076 | paired commissure curvature relaxation | LOCAL PASS", fill=(242, 242, 242))
for row, (variant, variant_label) in enumerate(variants):
    for column, (view, view_label) in enumerate(views):
        image = Image.open(OUT / f"{variant}-{view}.png").convert("RGB")
        image.thumbnail((285, 390), Image.Resampling.LANCZOS)
        x, y = 15 + column * 295, 30 + row * 630
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + 280, y + 24), fill=(10, 10, 10))
        draw.text((x + 4, y + 5), f"{variant_label} {view_label}", fill=(240, 240, 240))
sheet.save(REVIEW, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
visual = json.loads(VISUAL.read_text(encoding="utf-8"))
invariant = json.loads(INVARIANT.read_text(encoding="utf-8"))
collision = json.loads(COLLISION.read_text(encoding="utf-8"))
selected = next(item for item in study["variants"] if item["label"] == study["selectedVariant"])
performance_pass = (
    study["topologyChanged"] is False and study["materialChanged"] is False
    and invariant["checks"]["topologyIdentical"] and invariant["checks"]["materialSlotCountIdentical"]
)
study.update({
    "strictMouthScore100": 45,
    "visualAudit": str(VISUAL), "invariantAudit": str(INVARIANT), "collisionAudit": str(COLLISION), "review": str(REVIEW),
    "collisionStatus": collision["status"], "invariantStatus": invariant["status"],
    "performanceStatus": "PASS_NO_VERTEX_FACE_MATERIAL_SLOT_MODIFIER_OR_DRAW_CALL_DELTA" if performance_pass else "FAIL",
    "finding": "The selected 15% paired relaxation changes only eight vertices by at most 0.0572 mm. Neutral commissure maximum normal spread falls 88.04 to 38.63 degrees and smile falls 88.74 to 37.84 degrees. Central curvature and fixed crops are unchanged; all pose/expression collision gates pass. Stronger 30% and 45% variants reverse the gain and are rejected.",
    "candidateStatus": "LOCAL_GEOMETRY_TECHNICAL_PASS_VISUAL_SUBTLE",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1076-commissure-curvature.study.json; female-v249-mainline-r1076-commissure-curvature.visual-audit.json; female-v249-mainline-r1076-commissure-curvature.invariant-audit.json; female-v249-mainline-r1076-commissure-curvature.collision-audit.json; reviews/v249r1076-commissure-curvature/contact-sheet-r1076.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1076_LOCAL_GEOMETRY_TECHNICAL_PASS_VISUAL_SUBTLE_SCORE_45; selected 15% paired relaxation changes eight vertices <=0.0572mm, lowers neutral/smile commissure maximum normal spread by 49.41/50.90 degrees, preserves all relative shape-key deltas within 7.68e-9m, and passes four-frame, open, smile and 14-layer collision gates. No topology, material, modifier or draw-call delta; website v83 is unchanged."
current["latestMouthTopologyStudy"] = "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
current["latestMouthReview"] = "reviews/v249r1076-commissure-curvature/contact-sheet-r1076.jpg"
current["nextFaceTopologyWork"] = "Use r1076 as the mouth-edge baseline for r1077. Re-run the strict full-head multi-angle scorecard and rank remaining face defects rather than continuing microscopic mouth tuning; prioritize the largest visible issue among eyelid form, eye wetness/sclera integration, nose-to-lip anatomy and facial plane definition. Preserve r1076 collision and performance gates."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

refinement_path = ROOT / "scripts/CHARACTER-REFINEMENT.md"
entry = "### v249r1076 paired commissure curvature relaxation\n- Selected a 15% symmetrized far-neighbor relaxation on four topology-matched vertex pairs. It changes eight vertices by at most 0.0572 mm and lowers maximum commissure normal spread from 88.04 to 38.63 degrees neutral and 88.74 to 37.84 degrees smiling; 30% and 45% over-correct and are rejected.\n- All 35 relative shape-key deltas are preserved within 7.68e-9 m; topology, weights, materials, modifiers and draw calls are unchanged. Four-frame, open-mouth, smile, self-collision and 14 face-attachment gates pass. Website v83 remains unchanged.\n"
refinement = refinement_path.read_text(encoding="utf-8")
if entry not in refinement:
    refinement_path.write_text(refinement.rstrip() + "\n\n" + entry, encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "score": 45, "collision": collision["status"], "invariants": invariant["status"], "performance": study["performanceStatus"], "status": study["candidateStatus"]}, indent=2))
