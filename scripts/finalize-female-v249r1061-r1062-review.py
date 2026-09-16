"""Package and record the r1061 expression and r1062 material studies."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY_1061 = ASSETS / "female-v249-mainline-r1061-lip-form-expression.study.json"
AUDIT_1061 = ASSETS / "female-v249-mainline-r1061-lip-form-expression.collision-audit.json"
STUDY_1062 = ASSETS / "female-v249-mainline-r1062-lip-material.study.json"
REVIEW_DIR = ASSETS / "reviews/v249r1061-r1062-lips-expression-material"
SOURCE_1060 = ROOT.parent / "Temp/female-realism/v249r1060-shapekey-transfer"
SOURCE_1061 = ROOT.parent / "Temp/female-realism/v249r1061-lip-form-expression"
SOURCE_1062 = ROOT.parent / "Temp/female-realism/v249r1062-lip-material"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

panels = (
    (SOURCE_1060 / "neutral-front.png", "r1060 neutral"),
    (SOURCE_1061 / "c-anatomical-neutral-front.png", "r1061 neutral"),
    (SOURCE_1061 / "selected-open-1.00.png", "r1061 mouth open"),
    (SOURCE_1061 / "selected-smile-1.00.png", "r1061 smile"),
    (SOURCE_1062 / "a-r1061-control-neutral.png", "r1062 material control"),
    (SOURCE_1062 / "c-balanced-neutral.png", "r1062 mask 1.55"),
    (SOURCE_1062 / "e-defined-neutral.png", "r1062 mask 3.00"),
    (SOURCE_1062 / "f-full-mask-neutral.png", "r1062 mask 4.00"),
)
sheet = Image.new("RGB", (1840, 960), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1061-r1062 | expression collision PASS | material sweep visual reject", fill=(242, 242, 242))
for index, (path, label) in enumerate(panels):
    image = Image.open(path).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    column = index % 4
    row = index // 4
    x = 20 + column * 455
    y = 48 + row * 450
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 190, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1061-r1062.jpg"
sheet.save(review, quality=94, subsampling=0)

def mean_luma(path, crop):
    image = Image.open(path).convert("L").crop(crop)
    return ImageStat.Stat(image).mean[0]

control = SOURCE_1062 / "a-r1061-control-neutral.png"
selected = SOURCE_1062 / "e-defined-neutral.png"
crops = {
    "leftCheek": (30, 250, 240, 520),
    "rightCheek": (860, 250, 1070, 520),
    "upperFace": (390, 40, 710, 170),
    "mouth": (250, 245, 850, 525),
}
drift = {}
for name, crop in crops.items():
    before = mean_luma(control, crop)
    after = mean_luma(selected, crop)
    drift[name] = ((after - before) / before * 100.0) if before else 0.0

study_1061 = json.loads(STUDY_1061.read_text(encoding="utf-8"))
audit_1061 = json.loads(AUDIT_1061.read_text(encoding="utf-8"))
study_1061.update({
    "collisionAudit": str(AUDIT_1061),
    "collisionStatus": audit_1061["status"],
    "strictMouthScore100": 38,
    "retainedR1033MouthScore100": 39,
    "review": str(review),
    "finding": "The replacement expression keys raise maximum vertical motion from 0.051 mm to 2.310 mm for mouth-open and 1.274 mm for smile while retaining all 35 keys and zero collision. Neutral lip form changes remain subtle, smile readability is weak and the lower inner edge stays chalk-bright.",
    "candidateStatus": "TECHNICAL_EXPRESSION_AND_COLLISION_PASS_VISUAL_BELOW_RETAINED_R1033",
    "websitePromotionApproved": False,
})
STUDY_1061.write_text(json.dumps(study_1061, indent=2), encoding="utf-8")

study_1062 = json.loads(STUDY_1062.read_text(encoding="utf-8"))
study_1062.update({
    "strictMouthScore100": 38,
    "review": str(review),
    "fixedCropLumaDriftPercentVersusControl": drift,
    "collisionContract": "geometry and shape keys are byte-equivalent to collision-passing r1061; only owned skin node constants change",
    "finding": "Even with mask strength raised from 0.78 to 4.00, the inherited 0.25-maximum lips group produces only a weak diffuse shift and does not remove the white lower inner edge. The geometry-normal discontinuity remains dominant.",
    "candidateStatus": "VISUAL_REJECT_MATERIAL_MASK_CANNOT_REPAIR_GEOMETRY_NORMAL_EDGE",
    "websitePromotionApproved": False,
})
STUDY_1062.write_text(json.dumps(study_1062, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1060-mouth-region.inspect.json; female-v249-mainline-r1061-lip-form-expression.study.json; female-v249-mainline-r1061-lip-form-expression.collision-audit.json; female-v249-mainline-r1062-lip-material.study.json; reviews/v249r1061-r1062-lips-expression-material/contact-sheet-r1061-r1062.jpg"
current["latestMouthTopologyStatus"] = "R1061_TECHNICAL_EXPRESSION_AND_COLLISION_PASS; mouth-open maximum vertical motion rises from 0.051 mm to 2.310 mm and smile to 1.274 mm. All 35 keys, weights and four-frame/expressions collision gates pass. Strict score 38/100 remains below r1033 39 because smile readability is weak and the lower inner edge remains chalk-bright. R1062 material masks up to 4.0 are rejected because they cannot repair the geometry-normal edge."
current["latestMouthTopologyTransferStudy"] = "aevrynd-female-cc0-structured-lips-r1061-study.blend"
current["latestMouthTopologyCollisionAudit"] = "female-v249-mainline-r1061-lip-form-expression.collision-audit.json"
current["latestMouthReview"] = "reviews/v249r1061-r1062-lips-expression-material/contact-sheet-r1061-r1062.jpg"
current["nextFaceTopologyWork"] = "Build r1063 from r1061. Identify the exact lower-inner edge loop on the evaluated surface, remove the chalk-bright normal discontinuity through local tangent-continuous fairing or a rebuilt support ring, and increase smile corner displacement over a broader vertex field. Preserve the 35-key, normalized-weight and zero-collision contract; do not use further material masking to hide the edge."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

print(json.dumps({
    "review": str(review),
    "r1061Collision": audit_1061["status"],
    "r1061Score": study_1061["strictMouthScore100"],
    "r1062Status": study_1062["candidateStatus"],
    "fixedCropDriftPercent": drift,
}, indent=2))
