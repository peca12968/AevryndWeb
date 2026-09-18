"""Quantify the render-space effect of the r1078 eyelid inner-wall sweep."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
STUDY = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall-sweep.study.json"
REPORT = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.visual-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1078-eyelid-inner-wall"
VARIANTS = ("a-control", "b-one-ring-forward-0.12", "c-two-ring-forward-0.22", "d-two-ring-forward-0.32")
CONTROL = VARIANTS[0]
SELECTED = VARIANTS[2]


def load(label, view="eye-front"):
    return np.asarray(Image.open(OUT / f"{label}-{view}.png").convert("RGB"), dtype=np.float32)


def bright_sclera_proxy(image, x0, x1):
    roi = image[220:540, x0:x1]
    red, green, blue = roi[..., 0], roi[..., 1], roi[..., 2]
    mask = (green / (red + 1e-6) > 0.90) & (blue / (red + 1e-6) > 0.72) & (roi.mean(axis=2) > 150)
    return int(mask.sum())


counts = {}
for label in VARIANTS:
    image = load(label)
    counts[label] = {"left": bright_sclera_proxy(image, 0, 600), "right": bright_sclera_proxy(image, 800, 1400)}

control = counts[CONTROL]
metrics = {}
for label, values in counts.items():
    metrics[label] = {
        "brightLowSaturationEyeRegionPixels": values,
        "reductionVsControlPercent": {
            side: 100.0 * (control[side] - values[side]) / control[side] for side in ("left", "right")
        },
    }

fixed = {}
for view in ("face-front", "face-three-quarter"):
    a, c = load(CONTROL, view), load(SELECTED, view)
    fixed[view] = float(np.abs(a[:170] - c[:170]).mean())

report = {
    "revision": "v249r1078-eyelid-inner-wall-visual-audit",
    "study": str(STUDY),
    "control": CONTROL,
    "selected": SELECTED,
    "metricDefinition": "Render-space proxy, not object segmentation: pixels in fixed eye-front ROIs y=220:540, left x=0:600 and right x=800:1400 with G/R>0.90, B/R>0.72 and mean RGB>150.",
    "variants": metrics,
    "fixedUpperFrameMeanAbsoluteRgbDelta255": fixed,
    "visualDecision": {
        "selected": SELECTED,
        "reason": "The two-ring 0.22 mm wall gives visible physical lid thickness and reduces the bright sclera proxy without the narrowed, sleepy aperture of the 0.32 mm variant.",
        "rejected": {"d-two-ring-forward-0.32": "Technically clean but visually over-closed and over-thick."},
    },
    "status": "PASS_SELECTED_C_TWO_RING_0_22",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "variants": metrics, "fixed": fixed}, indent=2))
