"""Finalize post- and pre-subdivision support-bevel rejections."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
R1066 = ASSETS / "female-v249-mainline-r1066-support-bevel.study.json"
R1067 = ASSETS / "female-v249-mainline-r1067-presubdiv-support.study.json"
REVIEW_DIR = ASSETS / "reviews/v249r1066-r1067-support-geometry"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
directories = (ROOT.parent / "Temp/female-realism/v249r1066-support-bevel", ROOT.parent / "Temp/female-realism/v249r1067-presubdiv-support")
rows = (
    (("a-control", "control"), ("b-0.10mm-s2", "0.10mm s2"), ("c-0.20mm-s2", "0.20mm s2"), ("d-0.35mm-s3", "0.35mm s3"), ("e-0.50mm-s3", "0.50mm s3")),
    (("a-control", "control"), ("b-0.10mm-s1", "0.10mm s1"), ("c-0.20mm-s1", "0.20mm s1"), ("d-0.35mm-s2", "0.35mm s2"), ("e-0.50mm-s2", "0.50mm s2")),
)
sheet = Image.new("RGB", (2020, 850), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1066-r1067 | support geometry | VISUAL / STABILITY REJECT", fill=(242, 242, 242))
for row, entries in enumerate(rows):
    for column, (filename, label) in enumerate(entries):
        image = Image.open(directories[row] / f"{filename}-front.png").convert("RGB")
        image.thumbnail((390, 360), Image.Resampling.LANCZOS)
        x, y = 20 + column * 400, 48 + row * 395
        sheet.paste(image, (x, y))
        draw.rectangle((x + 5, y + 5, x + 155, y + 30), fill=(18, 18, 18))
        draw.text((x + 10, y + 10), ("post-subdiv " if row == 0 else "pre-subdiv ") + label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1066-r1067.jpg"
sheet.save(review, quality=94, subsampling=0)

r1066 = json.loads(R1066.read_text(encoding="utf-8"))
r1066.update({"strictMouthScore100": 38, "review": str(review), "finding": "Post-subdivision bevel widths 0.10-0.50 mm are visually negligible while increasing evaluated vertices from 216,636 to 230,976-243,382 and triangles from 432,912 to 461,592-486,404.", "candidateStatus": "VISUAL_AND_PERFORMANCE_REJECT", "websitePromotionApproved": False})
R1066.write_text(json.dumps(r1066, indent=2), encoding="utf-8")
r1067 = json.loads(R1067.read_text(encoding="utf-8"))
r1067.update({"strictMouthScore100": 35, "review": str(review), "finding": "Pre-subdivision support geometry changes the silhouette but creates paired lower-edge humps and retains the bright line. Blender 5.2.2 also terminates with EXCEPTION_ACCESS_VIOLATION on the second render of a beveled variant; one-render-per-load completes only as a diagnostic.", "candidateStatus": "VISUAL_AND_STABILITY_REJECT", "websitePromotionApproved": False})
R1067.write_text(json.dumps(r1067, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1066-support-bevel.study.json; female-v249-mainline-r1067-presubdiv-support.study.json; reviews/v249r1066-r1067-support-geometry/contact-sheet-r1066-r1067.jpg"
current["latestMouthTopologyStatus"] = "R1066_R1067_REJECT; post-subdivision bevel adds 6.6%-12.4% evaluated topology with negligible gain. Pre-subdivision bevel creates paired lower-edge humps, retains the bright rim and causes Blender 5.2.2 second-render access violation. r1061 remains the expression/deformation technical candidate at 38/100."
current["latestMouthReview"] = "reviews/v249r1066-r1067-support-geometry/contact-sheet-r1066-r1067.jpg"
current["nextFaceTopologyWork"] = "Stop modifier-based repair. Build r1068 as an explicit low-density lower-lip patch replacement around the measured 76-edge field, using a smooth resampled inner curve and two hand-authored support rows; transfer all 35 key deltas and normalized weights before any render or collision promotion."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "r1066": r1066["candidateStatus"], "r1067": r1067["candidateStatus"]}, indent=2))
