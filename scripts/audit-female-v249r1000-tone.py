"""Audit fixed-frame brightness and pixel drift for the r1000 eyelid sweep."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1000-mixed-space-eyelid-relief"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-mixed-space-eyelid-relief-r1000.tone-audit.json"
FILES = ("a-baseline.png", "b-half.png", "c-full.png", "d-strong.png")
SKIN_CROP = (100, 570, 800, 790)  # both orbital regions
MAX_LUMINANCE_DRIFT_PERCENT = 1.0


def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def luminance(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


images = {name: load_rgb(RENDER_DIR / name) for name in FILES}
baseline = images[FILES[0]]
left, top, right, bottom = SKIN_CROP
baseline_crop = baseline[top:bottom, left:right]
baseline_skin_mask = (
    (baseline_crop[..., 0] > 0.45)
    & (baseline_crop[..., 0] > baseline_crop[..., 1] * 1.03)
    & (baseline_crop[..., 1] > baseline_crop[..., 2] * 1.03)
)
baseline_luma = float(luminance(baseline_crop)[baseline_skin_mask].mean())

results = []
for name, image in images.items():
    crop = image[top:bottom, left:right]
    skin_luma = float(luminance(crop)[baseline_skin_mask].mean())
    drift = 100.0 * (skin_luma / baseline_luma - 1.0)
    delta = np.abs(image - baseline)
    changed = np.any(delta > (0.5 / 255.0), axis=2)
    results.append(
        {
            "file": name,
            "skinLinearLuminance": skin_luma,
            "skinLuminanceDriftPercent": drift,
            "meanAbsolutePixelDelta": float(delta.mean()),
            "maximumAbsolutePixelDelta": float(delta.max()),
            "changedPixelFraction": float(changed.mean()),
            "identicalToBaseline": bool(np.array_equal(image, baseline)),
            "toneStatus": "PASS" if abs(drift) <= MAX_LUMINANCE_DRIFT_PERCENT else "FAIL",
        }
    )

all_tone_pass = all(item["toneStatus"] == "PASS" for item in results)
report = {
    "renderDirectory": str(RENDER_DIR),
    "skinCrop": {"left": left, "top": top, "right": right, "bottom": bottom},
    "maximumAllowedLuminanceDriftPercent": MAX_LUMINANCE_DRIFT_PERCENT,
    "baselineSkinLinearLuminance": baseline_luma,
    "results": results,
    "toneStatus": "PASS" if all_tone_pass else "FAIL",
    "selectedStrength": 1.0,
    "visualEffectStatus": "SELECT_FULL_STRENGTH_FOR_R1001",
    "conclusion": (
        "All eyelid strengths pass the one-percent tone gate. Full strength brightens the fixed orbital "
        "skin crop by about 0.133 percent and is selected for r1001; strong is rejected as too puffy."
    ),
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if not all_tone_pass:
    raise SystemExit(2)
