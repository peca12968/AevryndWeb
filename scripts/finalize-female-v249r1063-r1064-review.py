"""Record the measured inner-edge fairing and inward-turn rejections."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
R1063 = ASSETS / "female-v249-mainline-r1063-inner-edge-fairing.study.json"
R1064 = ASSETS / "female-v249-mainline-r1064-inner-edge-turn.study.json"
REVIEW_DIR = ASSETS / "reviews/v249r1063-r1064-inner-edge"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
directories = (
    ROOT.parent / "Temp/female-realism/v249r1063-inner-edge-fairing",
    ROOT.parent / "Temp/female-realism/v249r1064-inner-edge-turn",
)
names = (
    ("a-control-neutral-front.png", "r1063 control"),
    ("b-quarter-neutral-front.png", "r1063 fair 0.25"),
    ("c-half-neutral-front.png", "r1063 fair 0.50"),
    ("d-three-quarter-neutral-front.png", "r1063 fair 0.75"),
    ("e-full-neutral-front.png", "r1063 fair 1.00"),
    ("a-control-neutral-front.png", "r1064 control"),
    ("b-0.5mm-neutral-front.png", "r1064 inward 0.5mm"),
    ("c-1.0mm-neutral-front.png", "r1064 inward 1.0mm"),
    ("d-1.5mm-neutral-front.png", "r1064 inward 1.5mm"),
    ("e-2.0mm-neutral-front.png", "r1064 inward 2.0mm"),
)
sheet = Image.new("RGB", (2020, 850), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1063-r1064 | measured lower-inner edge | VISUAL REJECT", fill=(242, 242, 242))
for index, (filename, label) in enumerate(names):
    directory = directories[0] if index < 5 else directories[1]
    image = Image.open(directory / filename).convert("RGB")
    image.thumbnail((390, 360), Image.Resampling.LANCZOS)
    x = 20 + (index % 5) * 400
    y = 48 + (index // 5) * 395
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 190, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1063-r1064.jpg"
sheet.save(review, quality=94, subsampling=0)

r1063 = json.loads(R1063.read_text(encoding="utf-8"))
r1063.update({"strictMouthScore100": 38, "review": str(review), "finding": "Depth-only Laplacian fairing of 85 measured high-dihedral vertices and 90 support vertices changes the surface by up to 0.8 mm but leaves the bright inner edge perceptually unchanged.", "candidateStatus": "VISUAL_REJECT_NO_PERCEPTUAL_GAIN", "websitePromotionApproved": False})
R1063.write_text(json.dumps(r1063, indent=2), encoding="utf-8")
r1064 = json.loads(R1064.read_text(encoding="utf-8"))
r1064.update({"strictMouthScore100": 36, "review": str(review), "finding": "Direct 0.5-2.0 mm inward turns deepen the cavity but preserve and increasingly widen the chalk-bright lower edge. Vertex depth alone cannot repair the evaluated shading transition.", "candidateStatus": "VISUAL_REJECT_BRIGHT_EDGE_WIDENS", "websitePromotionApproved": False})
R1064.write_text(json.dumps(r1064, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1063-lower-inner-edge.inspect.json; female-v249-mainline-r1063-inner-edge-fairing.study.json; female-v249-mainline-r1064-inner-edge-turn.study.json; reviews/v249r1063-r1064-inner-edge/contact-sheet-r1063-r1064.jpg"
current["latestMouthTopologyStatus"] = "R1063_R1064_VISUAL_REJECT; 76 edges/85 vertices with up to 83.975-degree source dihedral are measured. Depth fairing to 0.8 mm gives no perceptual gain; direct inward turns to 2.0 mm widen the chalk-bright edge. Neither crease nor sharp-edge attributes are present. r1061 remains the expression/deformation technical candidate at 38/100."
current["latestMouthReview"] = "reviews/v249r1063-r1064-inner-edge/contact-sheet-r1063-r1064.jpg"
current["nextFaceTopologyWork"] = "Build r1065 from r1061 as a shading-normal study: compare evaluated smooth normals against a locally relaxed reference and test explicit tangent-normal transfer confined to the 85 measured inner-edge vertices. Preserve geometry, 35 shape keys and collision contract; reject if the exported normal field is unstable or merely moves the highlight."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "r1063": r1063["candidateStatus"], "r1064": r1064["candidateStatus"]}, indent=2))
