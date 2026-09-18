"""Package the r1075 side-light root-cause diagnostic."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
DIAGNOSTIC = ASSETS / "female-v249-mainline-r1075-lip-edge-lighting.diagnostic.json"
AUDIT = ASSETS / "female-v249-mainline-r1075-lip-edge-lighting.audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1075-lip-edge-lighting"
REVIEW_DIR = ASSETS / "reviews/v249r1075-lip-edge-lighting"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1075.jpg"

files = sorted(path for path in OUT.glob("*.png") if path.name.endswith(("front.png", "oblique.png")))
sheet = Image.new("RGB", (1800, 1800), (15, 15, 15))
draw = ImageDraw.Draw(sheet)
draw.text((20, 6), "Aevrynd v249r1075 | asymmetric lip-edge lighting diagnostic", fill=(242, 242, 242))
for index, path in enumerate(files):
    image = Image.open(path).convert("RGB")
    image.thumbnail((430, 390), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 4) * 445, 30 + (index // 4) * 430
    sheet.paste(image, (x, y))
    draw.rectangle((x, y, x + 425, y + 24), fill=(10, 10, 10))
    draw.text((x + 5, y + 5), path.stem, fill=(240, 240, 240))
sheet.save(REVIEW, quality=94, subsampling=0)

diagnostic = json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))
diagnostic.update({
    "audit": str(AUDIT), "review": str(REVIEW), "strictMouthScore100": 43,
    "diagnosticStatus": "ROOT_CAUSE_CONFIRMED_GEOMETRY_NORMAL_TRANSITION",
    "finding": "Removing the 0.045 micro-bump changes the mouth by at most 0.068/255 mean absolute RGB and does not remove the line. A matte zero-specular isolation still flips the bright edge with the key-light direction. Commissure adjacent-face normal spread reaches 88.04 degrees neutral and 88.74 degrees smiling versus 34.95/34.72 degrees centrally. Vertices 13523 and 13558 are the strongest asymmetric outliers.",
    "candidateStatus": "DIAGNOSTIC_PASS_NO_MODEL_PROMOTION",
    "websitePromotionApproved": False,
})
DIAGNOSTIC.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
research = "female-v249-mainline-r1075-lip-edge-lighting.diagnostic.json; female-v249-mainline-r1075-lip-edge-lighting.audit.json; reviews/v249r1075-lip-edge-lighting/contact-sheet-r1075.jpg"
if research not in current["latestMouthTopologyResearch"]:
    current["latestMouthTopologyResearch"] += "; " + research
current["latestMouthTopologyStatus"] = "R1075_DIAGNOSTIC_PASS_ROOT_CAUSE_GEOMETRY_NORMAL_TRANSITION_SCORE_43; removing micro-bump changes the mouth <=0.068/255 and a matte zero-specular render retains the directional edge. Commissure adjacent-face normal spread reaches 88.04 degrees neutral and 88.74 degrees smiling versus <=34.95 degrees centrally. Extreme asymmetric vertices 13523 and 13558 localize the next correction. No model or website promotion occurred."
current["latestMouthReview"] = "reviews/v249r1075-lip-edge-lighting/contact-sheet-r1075.jpg"
current["nextFaceTopologyWork"] = "Build r1076 from r1074: locally relax the left commissure curvature around vertices 13523 and 13558, include the mirrored right-side counterparts, apply the same Basis delta to all 35 shape keys so authored deformation deltas remain intact, then rerun side-light, smile, open-mouth, self-collision and attachment-overlap gates before considering promotion."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

refinement_path = ROOT / "scripts/CHARACTER-REFINEMENT.md"
entry = "### v249r1075 asymmetric lip-edge lighting diagnostic\n- Removing the 0.045 micro-bump changes the mouth by at most 0.068/255 mean absolute RGB; matte zero-specular isolation still shows a bright edge that flips with the light direction.\n- Commissure adjacent-face normal spread reaches 88.04 degrees neutral and 88.74 degrees smiling, while the central maximum stays below 34.96 degrees. Vertices 13523 and 13558 are the strongest asymmetric outliers. Root cause is geometry/vertex-normal transition; no model or website promotion occurred.\n"
refinement = refinement_path.read_text(encoding="utf-8")
if entry not in refinement:
    refinement_path.write_text(refinement.rstrip() + "\n\n" + entry, encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "score": 43, "rootCause": audit["rootCause"], "status": diagnostic["candidateStatus"]}, indent=2))
