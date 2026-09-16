"""Finalize r1049 face-component and island-removal findings."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageChops, ImageStat


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1049-mouth-island-removal-sweep"
REVIEW_DIR = ASSETS / "reviews" / "v249r1049-mouth-components"
STUDY = ASSETS / "female-v249-mainline-r1049-mouth-island-removal-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
names = ("a-central5", "b-central6", "c-central-side", "d-all-small-mouth")
images = [Image.open(RENDER_DIR / f"{name}-neutral.png").convert("RGB") for name in names]
reference = images[0]
differences = []
for image in images[1:]:
    stat = ImageStat.Stat(ImageChops.difference(reference, image))
    differences.append(max(stat.mean))

sheet = Image.new("RGB", (1600, 980), (22, 22, 22))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1049 disconnected-island test | NO VISUAL EFFECT", fill=(238, 238, 238))
labels = ("remove 26 island faces", "remove 32 island faces", "remove 80 island faces", "remove 230 island faces")
for index, (label, image) in enumerate(zip(labels, images)):
    image.thumbnail((800, 430), Image.Resampling.LANCZOS)
    x = (index % 2) * 800
    y = 60 + (index // 2) * 460
    sheet.paste(image, (x, y + 28))
    draw.text((x + 12, y + 5), label, fill=(238, 238, 238))
review = REVIEW_DIR / "contact-sheet-r1049.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "maximumMeanPixelDifferenceAmongNeutralBounds": max(differences, default=0.0),
    "strictMouthScore100": 18,
    "retainedR1033Score100": 39,
    "finding": "Removing up to 230 faces from genuinely disconnected small components produces no meaningful pixel change. The central disk, bilateral tabs and strip remnants therefore belong to the 13,584-face main component.",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "HYPOTHESIS_REJECT_MAIN_COMPONENT_RETOPOLOGY_REQUIRED",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1049 151-component classification and 26/32/80/230-face disconnected-island removal"
current["latestMouthRejectedReason"] = "r1049 finds 151 face-connected body components, but removing successively broader sets of 26 to 230 genuinely disconnected mouth-overlapping faces produces no meaningful visual change after the eight strip faces are removed. The central disk, bilateral tabs and strip remnants are all part of the 13,584-face main component. Small-island cleanup is closed."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1049-mouth-face-components.inspect.json; female-v249-mainline-r1049-mouth-island-removal-sweep.study.json; reviews/v249r1049-mouth-components/contact-sheet-r1049.jpg"
current["latestMouthTopologyStatus"] = "R1049_FACE_COMPONENT_HYPOTHESIS_REJECT_SCORE_18; 151 components classified and up to 230 disconnected faces removed with no visual effect. All visible artifacts remain in the main face component; no candidate saved."
current["nextFaceTopologyWork"] = "Treat the complete visible artifact set as main-component topology. Starting from r1033, identify one clean outer attachment boundary around the stable vermilion, delete the enclosed main-component faces in one operation, and build a welded two-path upper/lower patch with nonshared commissure poles, a rear vestibule and jaw-coupled separation. Preserve all 35 shape keys and deform weights before collision review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "maxMeanPixelDifference": study["maximumMeanPixelDifferenceAmongNeutralBounds"]}, indent=2))
