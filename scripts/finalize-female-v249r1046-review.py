"""Finalize r1046 review evidence and authoritative character history."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1046-depth-cleanup-sweep"
REVIEW_DIR = ASSETS / "reviews" / "v249r1046-depth-cleanup"
STUDY = ASSETS / "female-v249-mainline-r1046-depth-cleanup-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
items = (
    ("17-face cleanup / balanced neutral", "b-balanced-neutral.png"),
    ("20-face cleanup / neutral", "d-full-depth-neutral.png"),
    ("20-face cleanup / mouth-open", "d-full-depth-mouth-open.png"),
    ("20-face cleanup / smile", "d-full-depth-smile.png"),
)
sheet = Image.new("RGB", (1600, 980), (22, 22, 22))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1046 depth cleanup | TECHNICAL PASS / VISUAL REJECT 33/100", fill=(238, 238, 238))
for index, (label, filename) in enumerate(items):
    image = Image.open(RENDER_DIR / filename).convert("RGB")
    image.thumbnail((800, 430), Image.Resampling.LANCZOS)
    x = (index % 2) * 800
    y = 60 + (index // 2) * 460
    sheet.paste(image, (x, y + 28))
    draw.text((x + 12, y + 5), label, fill=(238, 238, 238))
review = REVIEW_DIR / "contact-sheet-r1046.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "selectedTechnicalStudy": "d-full-depth",
    "strictMouthScore100": 33,
    "retainedR1033Score100": 39,
    "visualFinding": "The corrected rear wall hides the central inherited depth stack and all four bounds pass six collision states. The remaining bilateral pale skin strips are front boundary faces, while the slit, commissures and expression change remain too planar for hero quality.",
    "materialAndLightingChanged": False,
    "globalDarkeningClaim": "none; only the intended local oral cavity becomes darker",
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "TECHNICAL_PASS_VISUAL_REJECT_RETAIN_R1033",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1046 measured 17/20-face depth cleanup and bounded rear vestibule wall"
current["latestMouthRejectedReason"] = "r1046 deletes the complete 20-face measured internal depth stack and places a correctly head-bound rear wall. All four wall bounds pass frames 1/20/33/61 plus mouth-open and smile with zero body self, body-layer and inter-layer overlap. Central fragments are hidden, but bilateral pale front-boundary strips, planar slit and shallow expressions limit strict quality to 33/100, below retained r1033 at 39/100."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1046-mouth-depth-stack.inspect.json; female-v249-mainline-r1046-depth-cleanup-sweep.study.json; reviews/v249r1046-depth-cleanup/contact-sheet-r1046.jpg"
current["latestMouthTopologyStatus"] = "R1046_DEPTH_STACK_CLEANUP_TECHNICAL_PASS_VISUAL_REJECT_SCORE_33; selected d-full-depth removes 20 measured inherited faces and uses a 20x3.2mm rear wall. Six collision states pass, central fragments are hidden, bilateral front-boundary strips remain. r1033 stays retained; website v83 is unchanged."
current["nextFaceTopologyWork"] = "Use r1046 as the clean rear-cavity study and replace only the bilateral pale front-boundary strips with a welded upper/lower inner-lip patch derived from the r1033 outer landmark field. Build explicit commissure poles and jaw-coupled vertical separation, transfer all 35 shape keys and deform weights, then repeat collision, fixed-tone and multi-angle review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "strictScore": study["strictMouthScore100"]}, indent=2))
