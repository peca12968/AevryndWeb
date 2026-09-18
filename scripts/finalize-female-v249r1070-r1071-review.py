"""Package r1070 ray diagnostics and the rejected r1071 face-material sweep."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
INSPECTION = ASSETS / "female-v249-mainline-r1070-visible-support-faces.inspect.json"
STUDY = ASSETS / "female-v249-mainline-r1071-ray-hit-inner-strip-material.study.json"
R1070 = ROOT.parent / "Temp/female-realism/v249r1070-visible-support-faces"
R1071 = ROOT.parent / "Temp/female-realism/v249r1071-ray-hit-inner-strip"
REVIEW_DIR = ASSETS / "reviews/v249r1070-r1071-inner-strip"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def make_sheet(path, title, panels, columns):
    rows = (len(panels) + columns - 1) // columns
    sheet = Image.new("RGB", (20 + columns * 455, 60 + rows * 450), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 14), title, fill=(242, 242, 242))
    for index, (source, label) in enumerate(panels):
        image = Image.open(source).convert("RGB")
        image.thumbnail((445, 420), Image.Resampling.LANCZOS)
        x, y = 20 + (index % columns) * 455, 48 + (index // columns) * 450
        sheet.paste(image, (x, y))
        draw.rectangle((x + 5, y + 5, x + 190, y + 30), fill=(18, 18, 18))
        draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
    sheet.save(path, quality=94, subsampling=0)


r1070_review = REVIEW_DIR / "contact-sheet-r1070.jpg"
make_sheet(r1070_review, "Aevrynd v249r1070 | false colour + pixel ray localization", (
    (R1070 / "all-support-classified-front.png", "all support faces"),
    (R1070 / "camera-facing-only-front.png", "84 camera-facing"),
    (R1070 / "camera-facing-only-open.png", "84 facing / open"),
    (R1070 / "adjacent-old-all-front.png", "old adjacent faces"),
    (R1070 / "adjacent-old-facing-lower-front.png", "old lower facing"),
    (R1070 / "adjacent-old-facing-lower-open.png", "old lower / open"),
), 3)

r1071_review = REVIEW_DIR / "contact-sheet-r1071.jpg"
make_sheet(r1071_review, "Aevrynd v249r1071 | ray-hit face material | VISUAL REJECT", tuple(
    (R1071 / f"{label}-{pose}.png", caption)
    for label, prefix in (("a-control", "control"), ("b-exact-ray-hit", "10 faces"), ("c-one-ring", "58 faces"), ("e-support-adjacent-union", "389 faces"))
    for pose, suffix in (("neutral-front", "front"), ("neutral-oblique", "oblique"), ("open", "open"))
    for caption in (f"{prefix} {suffix}",)
), 4)

inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
inspection["bodyMaterialSlots"] = inspection["bodyMaterialSlots"][:3]
bright = [item for item in inspection["whiteLinePixelRays"] if item.get("sampleKind") == "brightLine"]
inspection.update({
    "brightLineRayCount": len(bright),
    "brightLineFirstHitObjects": sorted({item.get("object") for item in bright if item.get("object")}),
    "brightLineFirstHitMaterials": sorted({item.get("material") for item in bright if item.get("material")}),
    "brightLineMappedBaseFaces": sorted({item.get("nearestBaseFace") for item in bright if item.get("nearestBaseFace") is not None}),
    "review": str(r1070_review),
    "finding": "False-colouring all 299 support faces, the 84 camera-facing subset and adjacent old faces leaves the white rim visible. Camera rays through measured bright pixels hit the r1068 body with the owned skin material and map to ten low-density source faces; no tooth or separate oral object is the first hit.",
    "findingStatus": "DIAGNOSTIC_PASS_SOURCE_LOCALIZED",
})
INSPECTION.write_text(json.dumps(inspection, indent=2), encoding="utf-8")

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "selectedVariant": None,
    "strictMouthScore100": 39,
    "review": str(r1071_review),
    "finding": "The exact ten ray-hit faces create sparse pink patches; one- and two-ring growth create larger faceted blocks. Even the 389-face support-plus-adjacent union retains the white boundary while tinting both inner lips. Discrete low-density face material assignment cannot form a continuous inner-lip transition.",
    "candidateStatus": "VISUAL_REJECT_FACETED_MATERIAL_BOUNDARY",
    "collisionAuditRequired": False,
    "collisionAuditReason": "Rejected at the visual gate without geometry changes; r1068 remains the collision-qualified technical base.",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1070-visible-support-faces.inspect.json; reviews/v249r1070-r1071-inner-strip/contact-sheet-r1070.jpg; female-v249-mainline-r1071-ray-hit-inner-strip-material.study.json; reviews/v249r1070-r1071-inner-strip/contact-sheet-r1071.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1070_DIAGNOSTIC_PASS_R1071_VISUAL_REJECT; false-colour and camera-ray tests prove the grey-white rim first hits the body owned-skin shader and maps to ten mixed old/new source faces. Exact, one-ring, two-ring and 389-face union material coverage leaves the bright boundary and creates faceted blocks. Strict score remains 39/100; r1068 remains the collision-qualified technical base and website v83 is unchanged."
current["latestMouthReview"] = "reviews/v249r1070-r1071-inner-strip/contact-sheet-r1071.jpg"
current["nextFaceTopologyWork"] = "Use r1068 for r1072. Build a continuous sub-millimetre point/corner attribute from the measured bright-line ray locations and blend darker inner-lip colour plus higher roughness inside the existing owned skin shader, with no extra material slot; require smooth front/oblique/open results and fixed-crop tone isolation before collision promotion."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"r1070": str(r1070_review), "r1071": str(r1071_review), "score": 39, "status": study["candidateStatus"]}, indent=2))
