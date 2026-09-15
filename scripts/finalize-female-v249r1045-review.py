"""Finalize the strict r1045 owned mouth-topology donor review."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1045-mouth-donor-fit-sweep"
REVIEW_DIR = ASSETS / "reviews" / "v249r1045-mouth-source-topology"
STUDY = ASSETS / "female-v249-mainline-r1045-mouth-donor-fit-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
items = (
    ("r1033 + aligned donor", "b-aligned-mouth-front.png"),
    ("r1033 + donor 4 mm forward", "f-front-4mm-mouth-front.png"),
    ("r1033 + donor 8 mm forward", "g-front-8mm-mouth-front.png"),
    ("r446 donor isolated", "b-aligned-donor-isolation.png"),
)
sheet = Image.new("RGB", (1600, 980), (22, 22, 22))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1045 owned mouth donor | STRICT VISUAL REJECT", fill=(238, 238, 238))
for index, (label, filename) in enumerate(items):
    image = Image.open(RENDER_DIR / filename).convert("RGB")
    image.thumbnail((800, 430), Image.Resampling.LANCZOS)
    x = (index % 2) * 800
    y = 60 + (index // 2) * 460
    sheet.paste(image, (x, y + 28))
    draw.text((x + 12, y + 5), label, fill=(238, 238, 238))
review = REVIEW_DIR / "contact-sheet-r1045.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 16,
    "retainedR1033Score100": 39,
    "visualFinding": "The r446 donor is a symmetric detached lip shell with inflated uniform thickness, sharp commissure points and a straight wetline. At fitted depth it masks the face; moved forward it floats and intersects the retained perioral surface.",
    "topologyFinding": "No inspected CC0 historical body contains a reusable complete open mouth boundary. The r446 oral objects are explicit layers but are unsuitable as a final attached source without a new native retopology.",
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "VISUAL_AND_ATTACHMENT_REJECT_RETAIN_R1033",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1045 historical CC0 mouth-source scan and detached r446 lip donor alignment"
current["latestMouthRejectedReason"] = "r1045 inspects r249, r446, r602 and r1033 and finds no complete reusable open mouth boundary. The r446 455-vertex upper/lower lip shells are explicit owned CC0-derived layers, but alignment exposes inflated uniform thickness, pointed commissures and detached body intersection. Strict score 16/100; r1033 remains retained at 39/100."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1045-source-topology-inspection.json; female-v249-mainline-r1045-mouth-donor-fit-sweep.study.json; reviews/v249r1045-mouth-source-topology/contact-sheet-r1045.jpg"
current["latestMouthTopologyStatus"] = "R1045_SOURCE_SCAN_AND_DONOR_FIT_VISUAL_REJECT_SCORE_16; no historical body supplies a clean complete mouth boundary, and the r446 detached lip shells cannot meet attachment or realism gates. r1033 remains retained; website v83 is unchanged."
current["nextFaceTopologyWork"] = "Build a new native contiguous upper/lower oral-vestibule patch from the retained r1033 lip landmark field, using evenly spaced orbicularis flow, closed commissure poles and welded attachment. Transfer all 35 shape keys and deform weights, add dedicated jaw control, then repeat dynamic collision, fixed-tone and multi-angle gates. Historical detached lip-shell transplantation is closed."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "strictScore": study["strictMouthScore100"]}, indent=2))
