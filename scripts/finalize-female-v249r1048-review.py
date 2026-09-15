"""Finalize r1048 removal and figure-eight fill rejection evidence."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
REMOVE_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1048-strip-removal-sweep"
FILL_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1048-figure8-fill"
REVIEW_DIR = ASSETS / "reviews" / "v249r1048-boundary-rebuild"
REMOVE_STUDY = ASSETS / "female-v249-mainline-r1048-strip-removal-sweep.study.json"
FILL_STUDY = ASSETS / "female-v249-mainline-r1048-figure8-fill.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
items = (
    ("delete 8 strip faces", REMOVE_DIR / "a-strip8-neutral.png"),
    ("delete 15 strip/rear/neighbour faces", REMOVE_DIR / "d-strip8-all-neutral.png"),
    ("five-face skin fill", FILL_DIR / "a-skin-fill-neutral.png"),
    ("five-face wetline fill", FILL_DIR / "b-wetline-fill-neutral.png"),
)
sheet = Image.new("RGB", (1600, 980), (22, 22, 22))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1048 boundary removal/refill | STRICT VISUAL REJECT 24/100", fill=(238, 238, 238))
for index, (label, path) in enumerate(items):
    image = Image.open(path).convert("RGB")
    image.thumbnail((800, 430), Image.Resampling.LANCZOS)
    x = (index % 2) * 800
    y = 60 + (index // 2) * 460
    sheet.paste(image, (x, y + 28))
    draw.text((x + 12, y + 5), label, fill=(238, 238, 238))
review = REVIEW_DIR / "contact-sheet-r1048.jpg"
sheet.save(review, quality=94, subsampling=0)

remove_study = json.loads(REMOVE_STUDY.read_text(encoding="utf-8"))
remove_study.update({
    "strictMouthScore100": 18,
    "visualFinding": "Removing the proven strip faces eliminates the white bands but exposes a central pink disk and bilateral hanging fragments; broader removal increases the dark tabs.",
    "status": "VISUAL_REJECT_NOT_A_REBUILD",
})
REMOVE_STUDY.write_text(json.dumps(remove_study, indent=2), encoding="utf-8")

fill_study = json.loads(FILL_STUDY.read_text(encoding="utf-8"))
fill_study.update({
    "strictMouthScore100": 24,
    "retainedR1033Score100": 39,
    "visualFinding": "Blender fills 26 new boundary edges with only five large faces. Skin fill recreates pointed pale shelves and a central notch; wetline fill creates dark hanging rectangles. Shared degree-four pinch vertices prevent anatomical flow.",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "TOPOLOGY_AND_VISUAL_REJECT_RETAIN_R1033",
})
FILL_STUDY.write_text(json.dumps(fill_study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1048 eight-to-fifteen-face removal and five-face figure-eight hole fill"
current["latestMouthRejectedReason"] = "r1048 shows the eight strip faces form bilateral 10-edge figure-eight boundaries with one degree-four pinch vertex per side. Direct deletion exposes a central disk and hanging fragments; broader deletion enlarges them. Filling 26 new boundary edges yields only five large faces, recreating pale shelves or dark rectangular tabs. Strict score 24/100; no candidate is saved."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1048-removal-boundaries.inspect.json; female-v249-mainline-r1048-strip-removal-sweep.study.json; female-v249-mainline-r1048-figure8-fill.study.json; reviews/v249r1048-boundary-rebuild/contact-sheet-r1048.jpg"
current["latestMouthTopologyStatus"] = "R1048_FIGURE_EIGHT_BOUNDARY_REBUILD_REJECT_SCORE_24; exact removal and hole fill prove the shared degree-four pinch topology cannot support anatomical inner lips. r1046 remains a depth-cleanup study and r1033 remains retained."
current["nextFaceTopologyWork"] = "Return to the clean 36-edge primary mouth aperture, remove the four small figure-eight components as whole disconnected interior islands, and construct one welded two-path upper/lower inner-lip strip with dedicated commissure poles. Transfer all 35 shape keys and deform weights, add jaw-coupled separation, then run six-state collision and multi-angle review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": fill_study["status"], "strictScore": fill_study["strictMouthScore100"]}, indent=2))
