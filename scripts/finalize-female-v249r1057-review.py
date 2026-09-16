"""Finalize the analytic proxy-lip experiment."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1057-analytic-proxy-lip-sweep"
REVIEW_DIR = ASSETS / "reviews/v249r1057-analytic-proxy-lip"
STUDY = ASSETS / "female-v249-mainline-r1057-analytic-proxy-lip-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
variants = ("a-subtle-bulge", "b-balanced-bulge", "c-defined-bulge")
states = ("neutral", "mouth-open", "smile")
sheet = Image.new("RGB", (1650, 1150), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
draw.text((22, 16), "Aevrynd v249r1057 analytic proxy lip | STRICT REJECT", fill=(240, 240, 240))
for row, variant in enumerate(variants):
    draw.text((20, 72 + row * 350), variant, fill=(240, 240, 240))
    for column, state in enumerate(states):
        image = Image.open(RENDER_DIR / f"{variant}-{state}.png").convert("RGB")
        image.thumbnail((530, 310), Image.Resampling.LANCZOS)
        x = 20 + column * 545
        y = 100 + row * 350
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 8), state, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1057.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 6,
    "retainedR1033Score100": 39,
    "finding": "The analytic proxy removes source-BVH sampling noise, but the inherited serrated 76-edge seam and deeper undeleted main-component layers remain visible as alternating white shelves and black folds. Bulge strength does not solve the topology boundary.",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "REJECT_INHERITED_ATTACHMENT_BOUNDARY_AND_INTERNAL_STACK",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1057 analytic non-sampled proxy lip"
current["latestMouthRejectedReason"] = "r1057 builds eight smooth analytic rows with 0.5-1.5 mm convex bulge and preserves all 35 shape keys, avoiding the r1056 BVH defects. It still exposes the serrated 76-edge seam and inherited internal stack as white shelves and black folds. Strict score is 6/100; changing the surface formula while retaining the old attachment boundary is closed."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1057-analytic-proxy-lip-sweep.study.json; reviews/v249r1057-analytic-proxy-lip/contact-sheet-r1057.jpg"
current["latestMouthTopologyStatus"] = "R1057_ANALYTIC_PROXY_REJECT_SCORE_6; no Blend candidate saved and website v83 unchanged."
current["nextFaceTopologyWork"] = "Create a genuinely smooth cut boundary through the stable perioral surface instead of following existing jagged mesh edges. Split intersected source faces at that curve, delete the complete enclosed self-overlapped field, then weld a clean upper/lower patch to the new boundary with all 35 shape keys and weights."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "score": study["strictMouthScore100"]}, indent=2))
