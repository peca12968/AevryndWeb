"""Finalize the r1065 confined weighted-normal rejection."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1065-weighted-normal.study.json"
SOURCE = ROOT.parent / "Temp/female-realism/v249r1065-weighted-normal"
REVIEW_DIR = ASSETS / "reviews/v249r1065-weighted-normal"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
names = (("a-control", "control"), ("b-weight10", "weight 10"), ("c-weight30", "weight 30"), ("d-weight50", "weight 50"), ("e-weight100", "weight 100"))
sheet = Image.new("RGB", (2020, 440), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1065 | confined weighted normals | VISUAL REJECT", fill=(242, 242, 242))
control = Image.open(SOURCE / "a-control-front.png").convert("RGB")
differences = {}
for index, (filename, label) in enumerate(names):
    image = Image.open(SOURCE / f"{filename}-front.png").convert("RGB")
    difference = ImageChops.difference(control, image)
    differences[filename] = sum(ImageStat.Stat(difference).mean) / 3.0
    image.thumbnail((390, 360), Image.Resampling.LANCZOS)
    x = 20 + index * 400
    sheet.paste(image, (x, 48))
    draw.rectangle((x + 5, 53, x + 160, 78), fill=(18, 18, 18))
    draw.text((x + 10, 58), label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1065.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 38,
    "review": str(review),
    "meanAbsolutePixelDifferenceFromControl255": differences,
    "finding": "Weights 10, 30, 50 and 100 all produce the same 0.001458/255 mean difference from control, consistent with render jitter. The bright edge is unchanged, so a post-subdivision Weighted Normal modifier does not control this evaluated lip transition.",
    "candidateStatus": "VISUAL_REJECT_WEIGHTED_NORMAL_INEFFECTIVE",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")
current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1065-weighted-normal.study.json; reviews/v249r1065-weighted-normal/contact-sheet-r1065.jpg"
current["latestMouthTopologyStatus"] = "R1065_VISUAL_REJECT_WEIGHTED_NORMAL_INEFFECTIVE; weights 10/30/50/100 confined to the measured 85-vertex core and 90 support vertices are visually identical, with only 0.001458/255 mean pixel drift from control. r1061 remains the expression/deformation technical candidate at 38/100."
current["latestMouthReview"] = "reviews/v249r1065-weighted-normal/contact-sheet-r1065.jpg"
current["nextFaceTopologyWork"] = "Build r1066 from r1061 as an explicit support-geometry study. Test a narrow two- or three-segment bevel/support ring on the measured lower-inner edge, keep it procedural until export verification, and transfer/derive the full deformation contract before collision promotion."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["candidateStatus"], "differences": differences}, indent=2))
