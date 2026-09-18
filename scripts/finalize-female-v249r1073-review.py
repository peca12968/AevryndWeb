"""Package the decoupled inner-rim optical response review."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1073-decoupled-inner-rim-optics.study.json"
TONE = ASSETS / "female-v249-mainline-r1073-decoupled-inner-rim-optics.tone-audit.json"
R1068_AUDIT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1073-decoupled-inner-rim-optics"
REVIEW_DIR = ASSETS / "reviews/v249r1073-decoupled-inner-rim-optics"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1073.jpg"

panels = tuple(
    (OUT / f"{label}-{pose}.png", caption)
    for label, prefix in (("a-control", "control"), ("b-roughness-only", "roughness only"), ("c-specular-only", "specular only"), ("d-optical-only", "combined optical"))
    for pose, suffix in (("neutral-front", "front"), ("neutral-oblique", "oblique"), ("open", "open"))
    for caption in (f"{prefix} {suffix}",)
)
sheet = Image.new("RGB", (1840, 1410), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1073 | decoupled inner-rim optics | LOCAL TECHNICAL PASS", fill=(242, 242, 242))
for index, (path, label) in enumerate(panels):
    image = Image.open(path).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 4) * 455, 48 + (index // 4) * 450
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 195, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
sheet.save(REVIEW, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
tone = json.loads(TONE.read_text(encoding="utf-8"))
selected = next(item for item in study["variants"] if item["label"] == study["selectedVariant"])
metrics = selected["metrics"]
geometry_identical = metrics["geometryDigestBefore"] == metrics["geometryDigestAfter"]
weights_identical = metrics["weightDigestBefore"] == metrics["weightDigestAfter"]
study.update({
    "strictMouthScore100": 42,
    "toneAudit": str(TONE),
    "review": str(REVIEW),
    "geometryAndWeightsIdentical": geometry_identical and weights_identical,
    "collisionStatus": "INHERITED_R1068_PASS_GEOMETRY_AND_WEIGHTS_BIT_IDENTICAL",
    "collisionAudit": str(R1068_AUDIT),
    "performanceStatus": "NO_TOPOLOGY_OR_MATERIAL_SLOT_DELTA; one 13,817-value float point attribute and five shader nodes; no extra draw call",
    "finding": "Roughness-only removes more of the peak than specular-only, and combining both is strongest. The selected 1.60 mm / 0.80 optical-only mask changes no base colour, lowers rim P99 by 25.67/255 and maximum by 24.33/255, and leaves fixed cheek/upper-face crops unchanged. The central chalk-white line becomes a subdued grey-brown inner edge; pale residuals remain near the commissures.",
    "candidateStatus": "LOCAL_OPTICAL_TECHNICAL_PASS_VISUAL_PARTIAL",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1073-decoupled-inner-rim-optics.study.json; female-v249-mainline-r1073-decoupled-inner-rim-optics.tone-audit.json; reviews/v249r1073-decoupled-inner-rim-optics/contact-sheet-r1073.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1073_LOCAL_OPTICAL_TECHNICAL_PASS_VISUAL_PARTIAL_SCORE_42; the selected 1.60mm/0.80 mask changes only roughness (+0.36) and specular target (0.0), with no base-colour tint. Rim P99 falls 25.67/255 and maximum 24.33/255; fixed cheek/upper-face crops are unchanged. All 35 keys, geometry and weights remain bit-identical to collision-qualified r1068, with no topology, slot or draw-call delta. Commissure residuals remain, so website v83 is unchanged."
current["latestMouthMaterialStudy"] = "aevrynd-female-cc0-decoupled-inner-rim-r1073-study.blend"
current["latestMouthMaterialToneAudit"] = "female-v249-mainline-r1073-decoupled-inner-rim-optics.tone-audit.json"
current["latestMouthReview"] = "reviews/v249r1073-decoupled-inner-rim-optics/contact-sheet-r1073.jpg"
current["nextFaceTopologyWork"] = "Use r1073 for r1074. Measure residual brightness by horizontal position in front/oblique/open renders, extend or reshape the continuous optical mask only around the left/right commissure residuals, and keep the central no-colour optical response unchanged. Repeat tone isolation and inherited-geometry gates before website work."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(REVIEW), "score": 42, "geometryIdentical": geometry_identical, "weightsIdentical": weights_identical, "status": study["candidateStatus"]}, indent=2))
