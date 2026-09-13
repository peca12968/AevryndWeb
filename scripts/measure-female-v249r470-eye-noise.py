import json
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BEFORE = ASSETS / "reviews/v249r469-natural-iris/01-eye-close-f01.png"
AFTER = ASSETS / "reviews/v249r470-clean-cornea/01-eye-close-f01.png"
REPORT = ASSETS / "female-v249-mainline-r469-r470.eye-material-audit.json"
CENTERS = ((282, 327), (918, 327))
RADIUS = 58


def load_luminance(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    rgba = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
    bpy.data.images.remove(image)
    return rgba[..., 0] * 0.2126 + rgba[..., 1] * 0.7152 + rgba[..., 2] * 0.0722


def metrics(path):
    values = load_luminance(path)
    height, width = values.shape
    local_mean = (
        values
        + np.roll(values, 1, 0) + np.roll(values, -1, 0)
        + np.roll(values, 1, 1) + np.roll(values, -1, 1)
    ) / 5.0
    highpass = np.abs(values - local_mean)
    yy, xx = np.mgrid[:height, :width]
    per_eye = []
    for cx, cy in CENTERS:
        distance = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        iris = (distance < RADIUS) & (distance > 15)
        lower_stroma = iris & (yy < cy - 2)
        per_eye.append({
            "meanLuminance": float(values[iris].mean()),
            "meanHighpass": float(highpass[iris].mean()),
            "lowerStromaMeanHighpass": float(highpass[lower_stroma].mean()),
            "lowerStromaP95Highpass": float(np.percentile(highpass[lower_stroma], 95)),
        })
    return per_eye


before = metrics(BEFORE)
after = metrics(AFTER)
before_lower = sum(item["lowerStromaMeanHighpass"] for item in before) / len(before)
after_lower = sum(item["lowerStromaMeanHighpass"] for item in after) / len(after)
reduction = 100.0 * (1.0 - after_lower / before_lower)
report = {
    "before": str(BEFORE),
    "after": str(AFTER),
    "measurement": "mean absolute five-sample local luminance residual in the lower iris stroma, excluding the embedded pupil",
    "irisCentersPxBottomOrigin": [list(center) for center in CENTERS],
    "irisRadiusPx": RADIUS,
    "beforePerEye": before,
    "afterPerEye": after,
    "lowerStromaHighFrequencyReductionPercent": reduction,
    "geometryParityAudit": "female-v249-mainline-clean-cornea-r470.collision-audit.json",
    # A 70% bound removes the stochastic screen-door field while retaining
    # deliberate low-frequency stroma fibers, which also contribute residuals.
    "gate": {"atLeastSeventyPercentArtifactReduction": reduction >= 70.0},
}
report["status"] = "PASS" if all(report["gate"].values()) else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R470_EYE_NOISE=" + json.dumps(report, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
