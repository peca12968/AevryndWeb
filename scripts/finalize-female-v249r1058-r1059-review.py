"""Finalize the high-density and low-density smooth mouth-cut studies."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
REVIEW_DIR = ASSETS / "reviews/v249r1058-r1059-smooth-mouth-cut"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

rows = (
    ("r1058 evaluated 217k mesh", ROOT.parent / "Temp/female-realism/v249r1058-smooth-mouth-boolean"),
    ("r1059 low-density 14k mesh", ROOT.parent / "Temp/female-realism/v249r1059-lowpoly-mouth-boolean"),
)
variants = ("a-compact", "b-balanced", "c-broad")
sheet = Image.new("RGB", (1650, 820), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
draw.text((22, 16), "Aevrynd v249r1058-r1059 smooth mouth cut | TOPOLOGY DIRECTION PASS", fill=(240, 240, 240))
for row, (label, directory) in enumerate(rows):
    draw.text((20, 66 + row * 365), label, fill=(240, 240, 240))
    for column, variant in enumerate(variants):
        image = Image.open(directory / f"{variant}-front.png").convert("RGB")
        image.thumbnail((530, 320), Image.Resampling.LANCZOS)
        x = 20 + column * 545
        y = 92 + row * 365
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 8), variant, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1058-r1059.jpg"
sheet.save(review, quality=94, subsampling=0)

r1058_path = ASSETS / "female-v249-mainline-r1058-smooth-mouth-boolean.study.json"
r1058 = json.loads(r1058_path.read_text(encoding="utf-8"))
r1058.update({
    "strictMouthScore100": 36,
    "finding": "After correcting evaluation order, all three high-density cuts eliminate the self-overlapped mouth stack and render a continuous cavity edge. The mesh is 217k vertices and has no transferable shape-key contract.",
    "review": str(review),
    "status": "TOPOLOGY_DIRECTION_PASS_HIGH_DENSITY_NO_DEFORMATION_CONTRACT",
})
r1058_path.write_text(json.dumps(r1058, indent=2), encoding="utf-8")

r1059_path = ASSETS / "female-v249-mainline-r1059-lowpoly-mouth-boolean.study.json"
r1059 = json.loads(r1059_path.read_text(encoding="utf-8"))
r1059.update({
    "strictMouthScore100": 34,
    "retainedR1033Score100": 39,
    "selectedTopologyTransferStudy": "aevrynd-female-cc0-smooth-mouth-cut-r1059-study.blend",
    "selectedVariant": "a-compact",
    "finding": "With subdivision disabled and the active armature pose baked into the diagnostic duplicate, the compact cut produces a clean continuous mouth region at 14,005 vertices and 13,745 faces. It remains a static transfer study without shape keys or runtime rig.",
    "review": str(review),
    "status": "TOPOLOGY_TRANSFER_STUDY_SELECTED_NOT_A_RUNTIME_CANDIDATE",
})
r1059_path.write_text(json.dumps(r1059, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1058-smooth-mouth-boolean.study.json; female-v249-mainline-r1059-lowpoly-mouth-boolean.study.json; reviews/v249r1058-r1059-smooth-mouth-cut/contact-sheet-r1058-r1059.jpg"
current["latestMouthTopologyStatus"] = "R1058_R1059_SMOOTH_CUT_DIRECTION_PASS; compact low-density study has 14,005 vertices and 13,745 faces with the self-overlapped mouth stack removed. Visual score 34/100, below retained r1033 39, and no shape keys/rig contract yet."
current["latestMouthTopologyTransferStudy"] = "aevrynd-female-cc0-smooth-mouth-cut-r1059-study.blend"
current["latestMouthReview"] = "reviews/v249r1058-r1059-smooth-mouth-cut/contact-sheet-r1058-r1059.jpg"
current["nextFaceTopologyWork"] = "Rebuild the compact r1059 cut in source Basis space, map every resulting vertex to a source Basis triangle, transfer interpolated deltas for all 35 shape keys and deform weights, restore the Armature and subdivision modifiers, then run neutral/open/smile and four-frame self-collision gates."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "study": r1059["selectedTopologyTransferStudy"], "status": r1059["status"]}, indent=2))
