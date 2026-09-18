"""Create the r1082 visual audit/review and advance the local character ledger."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism/v249r1082-regional-skin"
STUDY = ASSETS / "female-v249-mainline-r1082-regional-skin-sweep.study.json"
AUDIT = ASSETS / "female-v249-mainline-r1082-regional-skin.audit.json"
VISUAL = ASSETS / "female-v249-mainline-r1082-regional-skin.visual-audit.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"
REVIEW_DIR = ASSETS / "reviews/v249r1082-regional-skin"
REVIEW = REVIEW_DIR / "contact-sheet-r1082.jpg"
LEDGER = ROOT / "scripts/CHARACTER-REFINEMENT.md"
CONTROL = "a-control"
SELECTED = "c-balanced"


def image_array(variant, view="skin-front"):
    return np.asarray(Image.open(TEMP / f"{variant}-{view}.png").convert("RGB"), dtype=np.float32)


regions = {
    "forehead": (420, 80, 780, 300),
    "leftCheek": (80, 580, 360, 900),
    "rightCheek": (840, 580, 1120, 900),
    "nose": (500, 560, 700, 900),
    "fullFace": (40, 70, 1160, 940),
}
control = image_array(CONTROL)
selected = image_array(SELECTED)
metrics = {}
for name, (x1, y1, x2, y2) in regions.items():
    before = control[y1:y2, x1:x2]
    after = selected[y1:y2, x1:x2]
    mask = (before.mean(axis=2) > 20) & ~((before[:, :, 2] > before[:, :, 0] * 1.15) & (before.mean(axis=2) > 80))
    before_luminance = before.mean(axis=2)[mask]
    after_luminance = after.mean(axis=2)[mask]
    metrics[name] = {
        "controlMeanLuminance255": float(before_luminance.mean()),
        "selectedMeanLuminance255": float(after_luminance.mean()),
        "driftPercent": float((after_luminance.mean() / before_luminance.mean() - 1.0) * 100.0),
        "meanAbsoluteRgbDelta255": float(np.abs(after - before).mean()),
    }

control_gray = Image.open(TEMP / f"{CONTROL}-skin-front.png").convert("L")
selected_gray = Image.open(TEMP / f"{SELECTED}-skin-front.png").convert("L")
x1, y1, x2, y2 = regions["forehead"]
control_low = np.asarray(control_gray.filter(ImageFilter.GaussianBlur(12)), dtype=np.float32)[y1:y2, x1:x2]
selected_low = np.asarray(selected_gray.filter(ImageFilter.GaussianBlur(12)), dtype=np.float32)[y1:y2, x1:x2]
low_frequency_reduction = (1.0 - selected_low.std() / control_low.std()) * 100.0

views = ("head-front", "head-three-quarter", "skin-front", "skin-oblique", "skin-opposite")
variants = (CONTROL, SELECTED)
tile = (430, 380)
label_height = 42
canvas = Image.new("RGB", (tile[0] * len(views), (tile[1] + label_height) * len(variants)), (22, 22, 22))
draw = ImageDraw.Draw(canvas)
for row, variant in enumerate(variants):
    for column, view in enumerate(views):
        image = Image.open(TEMP / f"{variant}-{view}.png").convert("RGB")
        image.thumbnail(tile)
        x = column * tile[0] + (tile[0] - image.width) // 2
        y = row * (tile[1] + label_height) + label_height + (tile[1] - image.height) // 2
        canvas.paste(image, (x, y))
        draw.text((column * tile[0] + 8, row * (tile[1] + label_height) + 11), f"{variant} | {view}", fill=(240, 240, 240))
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
canvas.save(REVIEW, quality=93, subsampling=0)

max_abs_drift = max(abs(item["driftPercent"]) for item in metrics.values())
visual = {
    "revision": "v249r1082-regional-skin-visual-audit",
    "control": CONTROL,
    "selected": SELECTED,
    "fixedRegionMetrics": metrics,
    "maximumAbsoluteLuminanceDriftPercent": max_abs_drift,
    "luminanceGatePercent": 1.0,
    "luminanceGateStatus": "PASS" if max_abs_drift <= 1.0 else "FAIL",
    "foreheadLowFrequencyVariationReductionPercent": float(low_frequency_reduction),
    "strictSkinScoreBefore100": 36,
    "strictSkinScoreAfter100": 38,
    "strictFullHeadScoreBefore100": 41,
    "strictFullHeadScoreAfter100": 42,
    "visualFinding": "The selected bound reduces the large cloud-like complexion patches and introduces restrained warm/cool and roughness zoning without darkening fixed regions. Pore response remains subtle at head distance, and the broad facial planes still read synthetic, so the result is a local material gain rather than hero skin.",
    "status": "LOCAL_SKIN_RESPONSE_GAIN_HERO_FAIL",
}
VISUAL.write_text(json.dumps(visual, indent=2), encoding="utf-8")
if visual["luminanceGateStatus"] != "PASS":
    raise SystemExit("r1082 fixed-region luminance gate failed")

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
if audit.get("status") != "PASS":
    raise SystemExit("r1082 technical audit must pass before finalization")
study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "audit": str(AUDIT),
    "visualAudit": str(VISUAL),
    "review": str(REVIEW),
    "strictSkinScore100": 38,
    "strictFullHeadScore100": 42,
    "candidateStatus": "LOCAL_REGIONAL_SKIN_PASS_VISUAL_PARTIAL_OFFLINE_ONLY",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current.update({
    "latestSkinTechnicalCandidate": "aevrynd-female-cc0-regional-skin-r1082-study.blend",
    "latestSkinCandidateStatus": f"R1082_LOCAL_REGIONAL_SKIN_PASS_VISUAL_PARTIAL_SCORE_38; selected bound contracts the inherited cloud-scale complexion contrast, adds a balanced scale-84 fine mottle, point-domain cheek/nose/temple colour and T-zone/cheek roughness, and a chained secondary micro-pore normal. Fixed forehead/cheek/nose/full-face luminance drift stays within {max_abs_drift:.3f}% and the candidate does not become globally darker. Geometry, 35 shape keys, weights, eyes, r1081 groom and bindings are identical; four frames retain zero hair penetration and >=1.60mm clearance. Nine shader nodes and two mesh attributes are added with no object, material-slot or draw-call increase. Website v83 is unchanged.",
    "latestSkinAudit": "female-v249-mainline-r1082-regional-skin.audit.json; female-v249-mainline-r1082-regional-skin.visual-audit.json",
    "latestSkinReview": "reviews/v249r1082-regional-skin/contact-sheet-r1082.jpg",
    "nextFaceTopologyWork": "Use r1082 as the local head baseline. Start r1083 on collision-qualified secondary hair motion because the explicit hair-motion requirement remains unfulfilled: preserve the r1081 1.60mm four-pose envelope, pin roots, add layered clump sway, prove settle and no penetration, then run a browser performance gate before any website promotion.",
    "latestFullHeadReview": "reviews/v249r1082-regional-skin/contact-sheet-r1082.jpg",
    "latestFullHeadStatus": "R1082_STRICT_FULL_HEAD_42_OF_100_HERO_FAIL; skin response improves 36 to 38 through smaller complexion variation, regional colour/roughness and layered pores without darkening. Hairline remains 37 and secondary hair motion is still unqualified; website v83 is unchanged.",
})
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

heading = "### v249r1082 regional skin response"
entry = f"""

{heading}
- The retained skin used one scale-34 colour noise field, uniform facial roughness and a weak scale-720 bump, producing large cloud-like patches and a smooth synthetic response. r1082 keeps the lip/commissure chain and adds explicit regional complexion, T-zone/cheek roughness, fine colour mottle and secondary micro-pore layers inside the existing material.
- The selected bound keeps the old macro field at scale 34 but contracts its endpoint contrast to 0.58, adds a balanced scale-84 fine mottle, raises primary pore strength from 0.045 to 0.058 and chains a 0.026 micro-pore normal. Two point-domain attributes affect 5,026 face/head vertices without moving geometry.
- Fixed-region luminance drift is capped at {max_abs_drift:.3f}%: forehead {metrics['forehead']['driftPercent']:+.3f}%, left cheek {metrics['leftCheek']['driftPercent']:+.3f}%, right cheek {metrics['rightCheek']['driftPercent']:+.3f}%, nose {metrics['nose']['driftPercent']:+.3f}% and full face {metrics['fullFace']['driftPercent']:+.3f}%. Forehead low-frequency variation falls {low_frequency_reduction:.2f}%, so the gain is not achieved by globally darkening the model.
- Body topology, all 35 shape keys, weights, eyes, r1081 groom/scalp geometry and head-bone bindings are bit-identical. Frames 1/20/33/61 test all 73,840 hair points with zero penetration and at least 1.60 mm body clearance. The edit adds nine shader nodes and two attributes with no object, material-slot or draw-call increase.
- Strict skin quality rises 36 to 38/100 and full-head quality reaches 42/100. Pores remain subtle at head distance and the facial planes are still broad and synthetic, so website v83 is unchanged. r1083 targets root-pinned, collision-qualified secondary hair motion.
"""
ledger = LEDGER.read_text(encoding="utf-8")
if heading not in ledger:
    LEDGER.write_text(ledger.rstrip() + entry + "\n", encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "visualAudit": str(VISUAL), "maxAbsDriftPercent": max_abs_drift, "status": "PASS"}, sort_keys=True))
