"""Measure r1076 localization and curvature improvement across six views."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
STUDY = ASSETS / "female-v249-mainline-r1076-commissure-curvature.study.json"
REPORT = ASSETS / "female-v249-mainline-r1076-commissure-curvature.visual-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1076-commissure-curvature"
CONTROL = "a-control"
SELECTED = "b-relax-0.15"
VIEWS = ("neutral-front", "neutral-oblique", "open-front", "smile-front", "left-key-front", "right-key-front")
MOUTH = (200, 300, 900, 450)
FIXED = {"upperFace": (300, 40, 800, 250), "leftCheek": (80, 200, 220, 500), "rightCheek": (880, 200, 1020, 500)}


def load(label, view):
    return np.asarray(Image.open(OUT / f"{label}-{view}.png").convert("RGB"), dtype=np.float32)


def crop(image, bounds):
    x0, y0, x1, y1 = bounds
    return image[y0:y1, x0:x1]


study = json.loads(STUDY.read_text(encoding="utf-8"))
control_study = next(item for item in study["variants"] if item["label"] == CONTROL)
selected_study = next(item for item in study["variants"] if item["label"] == SELECTED)
views = {}
for view in VIEWS:
    control, selected = load(CONTROL, view), load(SELECTED, view)
    difference = np.abs(selected - control)
    mean_difference = difference.mean(axis=2)
    y, x = np.unravel_index(np.argmax(mean_difference), mean_difference.shape)
    views[view] = {
        "fullFrameMeanAbsoluteRgbDelta255": float(difference.mean()),
        "mouthMeanAbsoluteRgbDelta255": float(np.abs(crop(selected, MOUTH) - crop(control, MOUTH)).mean()),
        "maximumChangedPixel": {
            "xy": [int(x), int(y)], "meanAbsoluteRgbDelta255": float(mean_difference[y, x]),
            "controlRgb255": [float(value) for value in control[y, x]],
            "selectedRgb255": [float(value) for value in selected[y, x]],
        },
    }

fixed = {}
control, selected = load(CONTROL, "neutral-front"), load(SELECTED, "neutral-front")
for name, bounds in FIXED.items():
    fixed[name] = float(np.abs(crop(selected, bounds) - crop(control, bounds)).mean())

report = {
    "revision": "v249r1076-commissure-curvature-visual-audit",
    "study": str(STUDY), "control": CONTROL, "selected": SELECTED,
    "views": views, "fixedCropMeanAbsoluteRgbDelta255": fixed,
    "fixedCropIsolationPass": all(value <= 0.001 for value in fixed.values()),
    "curvatureChange": {
        pose: {
            metric: selected_study["curvature"][pose]["commissure"][metric] - control_study["curvature"][pose]["commissure"][metric]
            for metric in ("meanDeg", "p95Deg", "maximumDeg")
        } for pose in ("neutral", "smile")
    },
    "centralCurvatureUnchanged": all(
        selected_study["curvature"][pose]["central"] == control_study["curvature"][pose]["central"]
        for pose in ("neutral", "smile")
    ),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ("curvatureChange", "centralCurvatureUnchanged", "fixedCropIsolationPass")}, indent=2))
