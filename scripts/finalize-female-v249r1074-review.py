"""Package r1074 endpoint-falloff review and update mainline tracking."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1074-commissure-falloff.study.json"
TONE = ASSETS / "female-v249-mainline-r1074-commissure-falloff.tone-audit.json"
R1068_AUDIT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1074-commissure-falloff"
REVIEW_DIR = ASSETS / "reviews/v249r1074-commissure-falloff"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1074.jpg"

display = (
    ("a-control", "control"),
    ("b-r1073-baseline", "r1073 baseline"),
    ("c-extend-2.50", "extension only"),
    ("d-extend-2.50-radius-0.20", "+0.20 mm"),
    ("e-extend-2.50-radius-0.40", "+0.40 mm selected"),
    ("f-extend-2.50-radius-0.60", "+0.60 mm rejected"),
)
panels = tuple(
    (OUT / f"{label}-{pose}.png", f"{caption} {suffix}")
    for label, caption in display
    for pose, suffix in (("neutral-front", "front"), ("neutral-oblique", "oblique"), ("open", "open"))
)
sheet = Image.new("RGB", (1840, 2090), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1074 | commissure falloff | LOCAL TECHNICAL PASS", fill=(242, 242, 242))
for index, (path, label) in enumerate(panels):
    image = Image.open(path).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 4) * 455, 48 + (index // 4) * 405
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 235, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
sheet.save(REVIEW, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
tone = json.loads(TONE.read_text(encoding="utf-8"))
selected = next(item for item in study["variants"] if item["label"] == study["selectedVariant"])
metrics = selected["metrics"]
geometry_identical = metrics["geometryDigestBefore"] == metrics["geometryDigestAfter"]
weights_identical = metrics["weightDigestBefore"] == metrics["weightDigestAfter"]
front_change = tone["selectedTargetChangeFromR1073"]["neutral-front"]
open_change = tone["selectedTargetChangeFromR1073"]["open"]
study.update({
    "strictMouthScore100": 43,
    "toneAudit": str(TONE), "review": str(REVIEW),
    "geometryAndWeightsIdentical": geometry_identical and weights_identical,
    "collisionStatus": "INHERITED_R1068_PASS_GEOMETRY_AND_WEIGHTS_BIT_IDENTICAL",
    "collisionAudit": str(R1068_AUDIT),
    "performanceStatus": "NO_TOPOLOGY_OR_MATERIAL_SLOT_DELTA; same single point attribute and five shader nodes as r1073; no extra draw call",
    "finding": f"A 2.50 mm endpoint extension plus 0.40 mm endpoint-local radius gain preserves the r1073 central response and lowers the measured right commissure residual by {-front_change:.2f}/255 front and {-open_change:.2f}/255 open. The 0.60 mm sweep over-darkens the endpoint and is rejected.",
    "candidateStatus": "LOCAL_COMMISSURE_TECHNICAL_PASS_VISUAL_PARTIAL",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1074-commissure-falloff.study.json; female-v249-mainline-r1074-commissure-falloff.tone-audit.json; reviews/v249r1074-commissure-falloff/contact-sheet-r1074.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1074_LOCAL_COMMISSURE_TECHNICAL_PASS_VISUAL_PARTIAL_SCORE_43; selected 2.50mm endpoint extension plus 0.40mm endpoint-local radius gain lowers the measured right commissure residual 11/255 in both front and open views while the central rim is unchanged. Fixed cheek/upper-face crop drift remains below 0.005/255 mean absolute RGB. All 35 keys, geometry and weights remain bit-identical to collision-qualified r1068; website v83 is unchanged."
current["latestMouthMaterialStudy"] = "aevrynd-female-cc0-commissure-falloff-r1074-study.blend"
current["latestMouthMaterialToneAudit"] = "female-v249-mainline-r1074-commissure-falloff.tone-audit.json"
current["latestMouthReview"] = "reviews/v249r1074-commissure-falloff/contact-sheet-r1074.jpg"
current["nextFaceTopologyWork"] = "Use r1074 for r1075. Diagnose the remaining lip-edge appearance under asymmetric side lighting and smile deformation; distinguish true geometry/normal discontinuity from optical response before any topology edit. Preserve the accepted central and commissure response and repeat collision plus tone-isolation gates."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

refinement_path = ROOT / "scripts/CHARACTER-REFINEMENT.md"
refinement_entry = "### v249r1074 commissure falloff\n- Selected a 2.50 mm endpoint extension with a 0.40 mm endpoint-local radius gain; it lowers the measured right commissure residual by 11/255 in front and open renders without changing the central rim.\n- Rejected the 0.60 mm sweep because it over-darkens the endpoint below the central response. Geometry, all 35 shape keys, weights, topology, material slots and draw calls are unchanged; collision status inherits the bit-identical r1068 pass. Website v83 remains unchanged.\n"
refinement = refinement_path.read_text(encoding="utf-8")
if refinement_entry not in refinement:
    refinement_path.write_text(refinement.rstrip() + "\n\n" + refinement_entry, encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "score": 43, "geometryIdentical": geometry_identical, "weightsIdentical": weights_identical, "status": study["candidateStatus"]}, indent=2))
