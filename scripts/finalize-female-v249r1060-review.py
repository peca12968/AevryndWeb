"""Finalize the r1060 shape-key transfer and collision review."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1060-shapekey-transfer.study.json"
AUDIT = ASSETS / "female-v249-mainline-r1060-shapekey-transfer.collision-audit.json"
REVIEW_DIR = ASSETS / "reviews/v249r1060-shapekey-transfer"
SOURCE_DIR = ROOT.parent / "Temp/female-realism/v249r1060-shapekey-transfer"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

views = (
    ("neutral-front.png", "neutral front"),
    ("neutral-oblique.png", "neutral oblique"),
    ("mouth-open.png", "mouth-open key 1.0"),
    ("smile.png", "smile key 1.0"),
)
sheet = Image.new("RGB", (1320, 1370), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((24, 18), "Aevrynd v249r1060 | 35-key transfer + collision PASS | TECHNICAL CANDIDATE", fill=(242, 242, 242))
for index, (filename, label) in enumerate(views):
    image = Image.open(SOURCE_DIR / filename).convert("RGB")
    image.thumbnail((625, 625), Image.Resampling.LANCZOS)
    column = index % 2
    row = index // 2
    x = 20 + column * 650
    y = 62 + row * 650
    sheet.paste(image, (x, y))
    draw.rectangle((x + 6, y + 6, x + 188, y + 32), fill=(20, 20, 20))
    draw.text((x + 12, y + 11), label, fill=(245, 245, 245))

review = REVIEW_DIR / "contact-sheet-r1060.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 36,
    "retainedR1033MouthScore100": 39,
    "collisionAudit": str(AUDIT),
    "collisionStatus": audit["status"],
    "review": str(review),
    "finding": "The compact Basis-space cleanup retains all 35 shape keys, normalized deform weights, subdivision and Armature deformation. It removes the visible inherited mouth fragments and stays stable in neutral, four rig frames, mouth-open and smile. The mouth is still a dark shallow slit with weak expression separation and incomplete lip anatomy.",
    "candidateStatus": "TECHNICAL_TOPOLOGY_AND_DEFORMATION_PASS_VISUAL_BELOW_RETAINED_R1033",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1060-shapekey-transfer.study.json; female-v249-mainline-r1060-shapekey-transfer.collision-audit.json; reviews/v249r1060-shapekey-transfer/contact-sheet-r1060.jpg"
current["latestMouthTopologyStatus"] = "R1060_TECHNICAL_TOPOLOGY_AND_DEFORMATION_PASS; 13,583 vertices, 13,519 faces, all 35 shape keys, normalized deform weights, restored subdivision and Armature. Four rig frames plus mouth-open and smile have zero non-adjacent body self-collision; 14 face attachments have zero overlap. Strict mouth score 36/100 remains below retained r1033 at 39/100 because expression separation and lip anatomy remain weak."
current["latestMouthTopologyTransferStudy"] = "aevrynd-female-cc0-smooth-mouth-transfer-r1060-study.blend"
current["latestMouthTopologyCollisionAudit"] = "female-v249-mainline-r1060-shapekey-transfer.collision-audit.json"
current["latestMouthReview"] = "reviews/v249r1060-shapekey-transfer/contact-sheet-r1060.jpg"
current["nextFaceTopologyWork"] = "Use r1060 as the clean technical topology source for r1061. Author stronger upper/lower vermilion curvature, Cupid bow, philtrum transition, closed commissures and jaw-coupled vertical opening while retaining the proven 35-key, normalized-weight and zero-collision contract. Keep r1033 as the visual face mainline until the strict mouth score exceeds 39/100."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

print(json.dumps({
    "review": str(review),
    "collision": audit["status"],
    "strictMouthScore100": study["strictMouthScore100"],
    "status": study["candidateStatus"],
}, indent=2))
