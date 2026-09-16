"""Finalize the failed direct surface-sampling experiment."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1056-sampled-lip-surface-sweep"
REVIEW_DIR = ASSETS / "reviews/v249r1056-sampled-lip-surface"
STUDY = ASSETS / "female-v249-mainline-r1056-sampled-lip-surface-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
variants = ("a-exact-surface", "b-subtle-forward", "c-defined-forward")
states = ("neutral", "mouth-open", "smile")
sheet = Image.new("RGB", (1650, 1150), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
draw.text((22, 16), "Aevrynd v249r1056 direct r1033 surface sampling | STRICT REJECT", fill=(240, 240, 240))
for row, variant in enumerate(variants):
    draw.text((20, 72 + row * 350), variant, fill=(240, 240, 240))
    for column, state in enumerate(states):
        image = Image.open(RENDER_DIR / f"{variant}-{state}.png").convert("RGB")
        image.thumbnail((530, 310), Image.Resampling.LANCZOS)
        x = 20 + column * 545
        y = 100 + row * 350
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 8), state, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1056.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 3,
    "retainedR1033Score100": 39,
    "finding": "Direct camera-ray sampling records 547 hits and 61 misses per variant, but the hit set includes folded rear surfaces. The new rows reproduce those hidden depth discontinuities as visible spikes and holes.",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "REJECT_SELF_OVERLAPPED_SOURCE_CANNOT_BE_DIRECTLY_DEPTH_SAMPLED",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1056 direct retained-surface ray sampling"
current["latestMouthRejectedReason"] = "r1056 rebuilds 608 vertices from 547 source-surface ray hits and 61 misses while preserving all 35 shape keys. Because the r1033 source is self-overlapped, rays sample folded rear faces and reproduce them as visible spikes, holes and floating shelves. Strict score falls to 3/100; direct depth sampling is closed."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1056-sampled-lip-surface-sweep.study.json; reviews/v249r1056-sampled-lip-surface/contact-sheet-r1056.jpg"
current["latestMouthTopologyStatus"] = "R1056_DIRECT_SURFACE_SAMPLING_REJECT_SCORE_3; no Blend candidate saved and website v83 unchanged."
current["nextFaceTopologyWork"] = "Construct a clean non-self-intersecting proxy lip surface from sparse stable r1033 landmarks and anatomical upper/lower profiles. Project the replacement rows onto that proxy, not the defective body BVH, then transfer all 35 shape keys and weights before collision review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "score": study["strictMouthScore100"]}, indent=2))
