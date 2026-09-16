"""Finalize the r1051 two-path rejection and r1052 dilation evidence."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1051-two-path-lip-sweep"
REVIEW_DIR = ASSETS / "reviews/v249r1051-two-path-lip"
STUDY = ASSETS / "female-v249-mainline-r1051-two-path-lip-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
variants = ("a-restrained", "b-balanced", "c-projected")
states = ("neutral", "mouth-open", "smile")
sheet = Image.new("RGB", (1650, 1150), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
draw.text((22, 16), "Aevrynd v249r1051 | welded two-path lip | STRICT REJECT", fill=(240, 240, 240))
for row, variant in enumerate(variants):
    draw.text((20, 72 + row * 350), variant, fill=(240, 240, 240))
    for column, state in enumerate(states):
        image = Image.open(RENDER_DIR / f"{variant}-{state}.png").convert("RGB")
        image.thumbnail((530, 310), Image.Resampling.LANCZOS)
        x = 20 + column * 545
        y = 100 + row * 350
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 8), state, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1051.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 12,
    "retainedR1033Score100": 39,
    "finding": "All three welded profiles remove the old broad lip surface but expose a serrated white upper attachment seam, black lower internal tabs and a planar cavity. Mouth-open changes the gap but does not recover natural orbicularis volume.",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "REJECT_SERRATED_ATTACHMENT_AND_INHERITED_INTERNAL_TABS",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1051 76-edge welded two-path profile sweep; r1052 0-16-ring guarded topology dilation"
current["latestMouthRejectedReason"] = "r1051 preserves all 35 shape keys and welds 228 new vertices to the measured 76-edge seam, but all projection bounds expose a serrated white upper seam, black inherited lower tabs and a planar cavity; strict score 12/100. r1052 proves guarded topology dilation grows 296 faces to 808 without collapsing the inherited inner loop, so uniform dilation cannot isolate a clean one-loop patch."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1051-mouth-depth-enclosure.inspect.json; female-v249-mainline-r1051-mouth-boundary-diagnostic.study.json; female-v249-mainline-r1051-two-path-lip-sweep.study.json; reviews/v249r1051-two-path-lip/contact-sheet-r1051.jpg; female-v249-mainline-r1052-mouth-topology-dilation.inspect.json"
current["latestMouthTopologyStatus"] = "R1051_TWO_PATH_VISUAL_REJECT_SCORE_12_R1052_DILATION_REJECT; no Blend candidate saved and website v83 unchanged."
current["nextFaceTopologyWork"] = "Return to r1033. Replace the single steep transition with several curvature-limited rows, then ray-classify only inherited body faces that lie in front of a bounded rear vestibule wall. Delete those front occluders before rendering; retain all 35 shape keys and validate self-collision before any candidate save."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "score": study["strictMouthScore100"]}, indent=2))
