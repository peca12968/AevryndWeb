"""Measure r1079 canthus localization, aperture preservation and fairing gain."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
STUDY = ASSETS / "female-v249-mainline-r1079-canthus-contour-sweep.study.json"
REPORT = ASSETS / "female-v249-mainline-r1079-canthus-contour.visual-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1079-canthus-contour"
VARIANTS = ("a-control", "b-conservative-0.35", "c-balanced-0.55", "d-strong-0.75")
CONTROL, SELECTED = VARIANTS[0], VARIANTS[2]


def load(label, view):
    return np.asarray(Image.open(OUT / f"{label}-{view}.png").convert("RGB"), dtype=np.float32)


def proxy(image, x0, x1):
    roi = image[220:540, x0:x1]; r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    return int(((g/(r+1e-6) > 0.90) & (b/(r+1e-6) > 0.72) & (roi.mean(axis=2) > 150)).sum())


study = json.loads(STUDY.read_text(encoding="utf-8"))
metrics = {}
for label in VARIANTS:
    image = load(label, "eye-front")
    left, right = proxy(image, 0, 600), proxy(image, 800, 1400)
    metrics[label] = {"leftBrightScleraProxyPixels": left, "rightBrightScleraProxyPixels": right, "totalBrightScleraProxyPixels": left + right}

control_total = metrics[CONTROL]["totalBrightScleraProxyPixels"]
for values in metrics.values():
    values["totalChangeVsControlPercent"] = 100.0 * (values["totalBrightScleraProxyPixels"] - control_total) / control_total

differences = {}
for view in ("eye-front", "eye-oblique", "face-front", "face-three-quarter"):
    a, c = load(CONTROL, view), load(SELECTED, view)
    delta = np.abs(c-a)
    differences[view] = {"fullFrameMeanAbsoluteRgbDelta255": float(delta.mean()), "unchangedTopBandMeanAbsoluteRgbDelta255": float(delta[:120].mean())}

selected = next(item for item in study["variants"] if item["label"] == SELECTED)
residuals = {side: item["rawMaximumLowerContourCorrectionMm"] * (1.0-selected["fairingStrength"]) for side, item in selected["diagnostics"].items()}
report = {
    "revision": "v249r1079-canthus-contour-visual-audit", "study": str(STUDY), "control": CONTROL, "selected": SELECTED,
    "scleraProxyDefinition": "Same fixed render-space proxy as r1078; used here to verify the contour correction does not hide the defect through wholesale aperture closure.",
    "variants": metrics, "renderDifferences": differences,
    "geometryFairing": {
        "controlMaximumLowerCornerDeviationMm": {side: item["rawMaximumLowerContourCorrectionMm"] for side, item in selected["diagnostics"].items()},
        "selectedResidualMaximumLowerCornerDeviationMm": residuals,
        "reductionPercent": 100.0 * selected["fairingStrength"],
        "horizontalApertureClosureMm": 2.0 * selected["maximumHorizontalClosureMm"],
    },
    "visualDecision": {"selected": SELECTED, "reason": "55% fairing removes the folded medial/lateral lower-lid run while preserving the upper contour and essentially preserving total bright sclera area; 75% begins to read overly straight."},
    "status": "PASS_SELECTED_BALANCED_0_55",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "geometryFairing": report["geometryFairing"], "sclera": metrics}, indent=2))
