"""Create the r1081 visual audit/review and advance the local development ledger."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism/v249r1081-graded-hairline"
STUDY = ASSETS / "female-v249-mainline-r1081-graded-hairline-sweep.study.json"
AUDIT = ASSETS / "female-v249-mainline-r1081-graded-hairline.audit.json"
VISUAL = ASSETS / "female-v249-mainline-r1081-graded-hairline.visual-audit.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"
REVIEW_DIR = ASSETS / "reviews/v249r1081-graded-hairline"
REVIEW = REVIEW_DIR / "contact-sheet-r1081.jpg"
LEDGER = ROOT / "scripts/CHARACTER-REFINEMENT.md"


def roi_metrics(path, view):
    image = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    height, width = image.shape[:2]
    if view == "top":
        roi = image[int(.22 * height):int(.76 * height), int(.28 * width):int(.72 * width)]
    elif view == "hairline-top":
        roi = image[int(.18 * height):int(.86 * height), int(.25 * width):int(.75 * width)]
    else:
        roi = image[int(.28 * height):int(.90 * height), int(.22 * width):int(.78 * width)]
    luminance = roi.mean(axis=2)
    bright_scalp = (luminance > 150) & (roi[:, :, 0] > roi[:, :, 1] * 1.05)
    return {
        "roiPixels": int(luminance.size),
        "meanLuminance255": float(luminance.mean()),
        "brightScalpProxyPixels": int(bright_scalp.sum()),
        "veryBrightPixels": int((luminance > 180).sum()),
    }


views = ("front", "top", "hairline-front", "hairline-top")
variants = ("a-control", "c-graded-0.50")
tile = (560, 400)
label_height = 42
canvas = Image.new("RGB", (tile[0] * len(views), (tile[1] + label_height) * len(variants)), (24, 24, 24))
draw = ImageDraw.Draw(canvas)
for row, variant in enumerate(variants):
    for column, view in enumerate(views):
        source = TEMP / f"{variant}-{view}.png"
        image = Image.open(source).convert("RGB")
        image.thumbnail(tile)
        x = column * tile[0] + (tile[0] - image.width) // 2
        y = row * (tile[1] + label_height) + label_height + (tile[1] - image.height) // 2
        canvas.paste(image, (x, y))
        draw.text((column * tile[0] + 8, row * (tile[1] + label_height) + 11), f"{variant} | {view}", fill=(240, 240, 240))
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
canvas.save(REVIEW, quality=93, subsampling=0)

metrics = {}
for view in ("top", "hairline-top", "hairline-front"):
    metrics[view] = {
        variant: roi_metrics(TEMP / f"{variant}-{view}.png", view)
        for variant in variants
    }
control = metrics["hairline-top"]["a-control"]["brightScalpProxyPixels"]
selected = metrics["hairline-top"]["c-graded-0.50"]["brightScalpProxyPixels"]
reduction = 100.0 * (control - selected) / max(1, control)
visual = {
    "revision": "v249r1081-graded-hairline-visual-audit",
    "control": "a-control",
    "selected": "c-graded-0.50",
    "fixedRoiMetrics": metrics,
    "hairlineTopBrightScalpProxyReductionPercent": reduction,
    "strictHairlineScoreBefore100": 32,
    "strictHairlineScoreAfter100": 37,
    "strictFullHeadScoreBefore100": 41,
    "strictFullHeadScoreAfter100": 41,
    "visualFinding": "The selected bound removes the blown wide centre-part proxy and softens the frontal cap edge. Close inspection still shows sparse wire-like transition fibres, while the long groom remains a uniform curtain without validated secondary motion.",
    "status": "LOCAL_VISUAL_GAIN_HERO_FAIL",
}
VISUAL.write_text(json.dumps(visual, indent=2), encoding="utf-8")

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "audit": str(AUDIT),
    "visualAudit": str(VISUAL),
    "review": str(REVIEW),
    "strictHairlineScore100": 37,
    "strictFullHeadScore100": 41,
    "candidateStatus": "LOCAL_HAIRLINE_TRANSITION_PASS_VISUAL_PARTIAL_STATIC_ONLY",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
if audit.get("status") != "PASS":
    raise SystemExit("r1081 technical audit must pass before ledger finalization")
current = json.loads(CURRENT.read_text(encoding="utf-8"))
current.update({
    "latestTargetNativeHairTechnicalCandidate": "aevrynd-female-cc0-graded-hairline-r1081-study.blend",
    "latestTargetNativeHairAudit": "female-v249-mainline-r1081-graded-hairline.audit.json; female-v249-mainline-r1081-graded-hairline.visual-audit.json",
    "latestTargetNativeHairReview": "reviews/v249r1081-graded-hairline/contact-sheet-r1081.jpg",
    "latestTargetNativeHairStatus": "R1081_LOCAL_HAIRLINE_TRANSITION_PASS_VISUAL_PARTIAL_SCORE_37; selected 0.50 part pin plus 130 short owned fibres removes the blown wide part proxy and fades the frontal scalp edge. The 73,840-point groom is head-bone bound and maintains at least 1.60mm body clearance at frames 1/20/33/61 with zero penetrating points. It adds 3.57% curves and 1.43% points with no object, material-slot or draw-call increase. Long-hair clump hierarchy and secondary motion remain unqualified; website v83 is unchanged.",
    "nextFaceTopologyWork": "Use r1081 as the local head baseline. Start r1082 on skin response, the lowest strict subsystem at 36/100: add owned regional roughness, pore-scale breakup and restrained colour variation without darkening fixed face crops or increasing material slots. Keep hair motion as a separate collision-qualified workstream.",
    "latestFullHeadReview": "reviews/v249r1081-graded-hairline/contact-sheet-r1081.jpg",
    "latestFullHeadStatus": "R1081_STRICT_FULL_HEAD_41_OF_100_HERO_FAIL; hairline/scalp transition improves 32 to 37 by removing the bright wide part and hard frontal cap boundary. Skin remains 36 and is the next blocker; long hair mass and secondary motion remain below production quality. Website v83 is unchanged.",
})
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

heading = "### v249r1081 graded hairline and four-pose clearance"
entry = f"""

{heading}
- Traced the bright centre part to the opaque r976 scalp cap and early centre-guide fan, then tested part pinning, scalp response and short graded fibres. The selected 0.50 bound adds 130 owned 25-52 mm fibres inside the existing Curves object and lowers the scalp response without adding an object, material slot or draw call.
- The fixed hairline-top bright-scalp proxy falls {reduction:.2f}% from {control:,} to {selected:,} pixels. The frontal cap edge now fades into the forehead and the wide white centre strip is removed; the stronger 0.65 variant is rejected for excessive darkening and larger deformation.
- The groom grows from 3,640 curves / 72,800 points to 3,770 / 73,840, a 3.57% curve and 1.43% point increase. Body geometry, all 35 shape keys, weights, eye geometry/topology, scalp topology, object count and material-slot counts remain unchanged.
- The first audit exposed 6,119 posed penetrations because the inherited r981 groom was static. r1081 now binds groom and scalp to the head bone and builds a four-pose clearance envelope. Frames 1/20/33/61 test all 73,840 points with zero penetration and at least 1.60 mm signed body clearance.
- Strict hairline quality rises 32 to 37/100. Full-head quality remains 41/100 because the transition fibres still read thin at close range, the long groom remains a straight curtain and no secondary-motion pass is claimed. Website v83 remains unchanged; r1082 moves to skin response at 36/100.
"""
ledger = LEDGER.read_text(encoding="utf-8")
if heading not in ledger:
    LEDGER.write_text(ledger.rstrip() + entry + "\n", encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "visualAudit": str(VISUAL), "brightProxyReductionPercent": reduction, "status": "PASS"}, sort_keys=True))
