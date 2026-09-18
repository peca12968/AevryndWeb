"""Package the rejected r1069 support-band depth sweep."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1069-support-band-turn.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1069-support-band-turn"
REVIEW_DIR = ASSETS / "reviews/v249r1069-support-band-turn"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

panels = (
    ("a-control-neutral-front.png", "control neutral"),
    ("c-0.10mm-neutral-front.png", "0.10 mm neutral"),
    ("e-0.35mm-neutral-front.png", "0.35 mm neutral"),
    ("a-control-neutral-oblique.png", "control oblique"),
    ("c-0.10mm-neutral-oblique.png", "0.10 mm oblique"),
    ("e-0.35mm-neutral-oblique.png", "0.35 mm oblique"),
    ("a-control-open.png", "control open"),
    ("c-0.10mm-open.png", "0.10 mm open"),
    ("e-0.35mm-open.png", "0.35 mm open"),
)
sheet = Image.new("RGB", (1385, 1410), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1069 | 234-vertex support-band turn | VISUAL REJECT", fill=(242, 242, 242))
for index, (name, label) in enumerate(panels):
    image = Image.open(RENDER_DIR / name).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 3) * 455, 48 + (index // 3) * 450
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 165, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1069.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
for variant in study["variants"]:
    variant["metrics"]["movedVertices"] = 0 if variant["metrics"]["depthMm"] == 0 else 234
study.update({
    "selectedVariant": None,
    "strictMouthScore100": 39,
    "review": str(review),
    "finding": "Moving all 234 baked support vertices inward by 0.05-0.35 mm across all 35 shape keys leaves the grey-white strip perceptually unchanged in neutral front, oblique and mouth-open views. The strongest bound also fails to hide it, proving the defect is tied to the visible face row and its shading/material transition rather than global support-band depth.",
    "candidateStatus": "VISUAL_REJECT_NO_GAIN",
    "collisionAuditRequired": False,
    "collisionAuditReason": "Rejected at the visual gate before promotion; r1068 remains the collision-qualified technical base.",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1069-support-band.inspect.json; female-v249-mainline-r1069-support-band-turn.study.json; reviews/v249r1069-support-band-turn/contact-sheet-r1069.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1069_VISUAL_REJECT_NO_GAIN; translating all 234 r1068 support-band vertices inward by 0.05-0.35mm across all 35 shape keys leaves the grey-white strip unchanged in neutral, oblique and open views. Strict score remains 39/100. r1068 remains the collision-qualified technical mouth base; website v83 is unchanged."
current["latestMouthReview"] = "reviews/v249r1069-support-band-turn/contact-sheet-r1069.jpg"
current["nextFaceTopologyWork"] = "Use r1068 as the technical base for r1070. Classify the 299 faces touching the baked support vertices by evaluated camera-facing normal, material and render contribution; isolate the exact visible lower-inner row, then rebuild or shade only that row as a continuous inward vestibule transition before collision promotion."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "score": 39, "status": study["candidateStatus"]}, indent=2))
