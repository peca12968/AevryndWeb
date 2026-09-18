"""Package the continuous inner-rim shader-mask review."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1072-continuous-inner-rim-mask.study.json"
TONE = ASSETS / "female-v249-mainline-r1072-continuous-inner-rim-mask.tone-audit.json"
R1068_AUDIT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1072-continuous-inner-rim"
REVIEW_DIR = ASSETS / "reviews/v249r1072-continuous-inner-rim"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1072.jpg"

panels = tuple(
    (OUT / f"{label}-{pose}.png", caption)
    for label, prefix in (("a-control", "control"), ("b-narrow-1.0mm", "1.0 mm / 0.70"), ("e-balanced-1.35mm", "1.35 mm / 0.55"), ("f-soft-1.60mm", "1.60 mm / 0.52"))
    for pose, suffix in (("neutral-front", "front"), ("neutral-oblique", "oblique"), ("open", "open"))
    for caption in (f"{prefix} {suffix}",)
)
sheet = Image.new("RGB", (1840, 1410), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1072 | continuous owned-skin rim mask | LOCAL TECHNICAL PASS", fill=(242, 242, 242))
for index, (path, label) in enumerate(panels):
    image = Image.open(path).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 4) * 455, 48 + (index // 4) * 450
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 185, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
sheet.save(REVIEW, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
tone = json.loads(TONE.read_text(encoding="utf-8"))
selected = next(item for item in study["variants"] if item["label"] == study["selectedVariant"])
metrics = selected["metrics"]
geometry_identical = metrics["geometryDigestBefore"] == metrics["geometryDigestAfter"]
weights_identical = metrics["weightDigestBefore"] == metrics["weightDigestAfter"]
study.update({
    "strictMouthScore100": 40,
    "toneAudit": str(TONE),
    "review": str(REVIEW),
    "geometryAndWeightsIdentical": geometry_identical and weights_identical,
    "collisionStatus": "INHERITED_R1068_PASS_GEOMETRY_AND_WEIGHTS_BIT_IDENTICAL",
    "collisionAudit": str(R1068_AUDIT),
    "performanceStatus": "NO_TOPOLOGY_OR_MATERIAL_SLOT_DELTA; one 13,817-value float point attribute and six shader nodes; no extra draw call",
    "finding": "The selected 1.35 mm / 0.55 continuous point mask affects 208 vertices and blends inside the existing owned skin material. Rim P99 falls by 14.33/255 and maximum by 11.33/255 while fixed cheek and upper-face crops remain unchanged. The faceted patches from r1071 are gone, but a thin grey-white line remains in front, oblique and open views.",
    "candidateStatus": "LOCAL_MATERIAL_TECHNICAL_PASS_VISUAL_PARTIAL",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1072-continuous-inner-rim-mask.study.json; female-v249-mainline-r1072-continuous-inner-rim-mask.tone-audit.json; reviews/v249r1072-continuous-inner-rim/contact-sheet-r1072.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1072_LOCAL_MATERIAL_TECHNICAL_PASS_VISUAL_PARTIAL_SCORE_40; selected 1.35mm continuous point mask affects 208 vertices inside the existing owned skin shader. Rim P99 falls 14.33/255 and maximum 11.33/255 with zero fixed cheek/upper-face drift. All 35 shape keys, geometry and weights are bit-identical to collision-qualified r1068; no topology, material-slot or draw-call delta. A thin grey-white line remains, so website v83 is unchanged."
current["latestMouthMaterialStudy"] = "aevrynd-female-cc0-continuous-inner-rim-r1072-study.blend"
current["latestMouthMaterialToneAudit"] = "female-v249-mainline-r1072-continuous-inner-rim-mask.tone-audit.json"
current["latestMouthReview"] = "reviews/v249r1072-continuous-inner-rim/contact-sheet-r1072.jpg"
current["nextFaceTopologyWork"] = "Use r1072 for r1073 and decouple colour from optical suppression: keep a smooth 1.35-1.80mm measured mask, reduce colour blend to near zero, and sweep roughness/specular-only response so the remaining line darkens without a pink lower-lip band. Repeat front/oblique/open and fixed-crop tone gates before any website work."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(REVIEW), "score": 40, "geometryIdentical": geometry_identical, "weightsIdentical": weights_identical, "status": study["candidateStatus"]}, indent=2))
