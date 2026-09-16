"""Finalize curvature, seam-damping and lower-occluder findings."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
REVIEW_DIR = ASSETS / "reviews/v249r1053-r1055-mouth"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

rows = (
    ("r1053 three-row curvature", ROOT.parent / "Temp/female-realism/v249r1053-curvature-vestibule-sweep", "a-soft"),
    ("r1054 five-row seam damping", ROOT.parent / "Temp/female-realism/v249r1054-seam-damping-sweep", "b-balanced"),
    ("r1055 remove 15 lower first-hit faces", ROOT.parent / "Temp/female-realism/v249r1055-lower-occluder-removal", "a-r1053-soft"),
)
states = ("neutral", "mouth-open", "smile")
sheet = Image.new("RGB", (1650, 1150), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
draw.text((22, 16), "Aevrynd v249r1053-r1055 mouth topology | STRICT REJECT", fill=(240, 240, 240))
for row, (label, directory, prefix) in enumerate(rows):
    draw.text((20, 72 + row * 350), label, fill=(240, 240, 240))
    for column, state in enumerate(states):
        image = Image.open(directory / f"{prefix}-{state}.png").convert("RGB")
        image.thumbnail((530, 310), Image.Resampling.LANCZOS)
        x = 20 + column * 545
        y = 100 + row * 350
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 8), state, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1053-r1055.jpg"
sheet.save(review, quality=94, subsampling=0)

updates = (
    (ASSETS / "female-v249-mainline-r1053-curvature-vestibule-sweep.study.json", 18, "REJECT_BRIGHT_SEAM_AND_LOWER_INTERNAL_TABS"),
    (ASSETS / "female-v249-mainline-r1054-seam-damping-sweep.study.json", 10, "REJECT_BROAD_WHITE_SHELF_AND_LOWER_INTERNAL_TABS"),
    (ASSETS / "female-v249-mainline-r1055-lower-occluder-removal.study.json", 8, "REJECT_DEEPER_FRAGMENT_STACK_EXPOSED"),
)
for path, score, status in updates:
    study = json.loads(path.read_text(encoding="utf-8"))
    study.update({
        "strictMouthScore100": score,
        "retainedR1033Score100": 39,
        "candidateBlendSaved": False,
        "websitePromotionApproved": False,
        "review": str(review),
        "status": status,
    })
    path.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1053 three-row curvature and bounded vestibule; r1054 five-row seam damping; r1055 measured lower first-hit removal"
current["latestMouthRejectedReason"] = "r1053 reduces the largest seam spikes but retains a bright upper shelf and black lower tabs (18/100). r1054 starts from the exact source seam and distributes smoothing over five rows, which broadens the white shelf (10/100). r1055 removes one measured 15-face lower first-hit pass and immediately exposes deeper coloured fragments (8/100). Masking, uniform damping and layer-by-layer excavation are closed."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1053-curvature-vestibule-sweep.study.json; female-v249-mainline-r1054-seam-damping-sweep.study.json; female-v249-mainline-r1055-lower-occluder-removal.study.json; reviews/v249r1053-r1055-mouth/contact-sheet-r1053-r1055.jpg"
current["latestMouthTopologyStatus"] = "R1053_R1055_VISUAL_REJECT_SCORES_18_10_8; all preserve 35 shape keys but fail anatomy; no Blend candidate saved and website v83 unchanged."
current["nextFaceTopologyWork"] = "Return to r1033 and sample its retained visible outer-lip surface as a geometric reference rather than projecting a parametric shelf. Build a new continuous interior patch behind that sampled surface, with a clean aperture and vestibule, then transfer all 35 shape keys and weights before visual and collision review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": current["latestMouthTopologyStatus"]}, indent=2))
