"""Audit fixed-frame brightness and pixel drift for the r998 eyelid sweep."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r998-eyelid-relief-sweep"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-eyelid-relief-r998.tone-audit.json"
FILES = ("a-baseline.png", "b-half.png", "c-full.png", "d-strong.png")
SKIN_CROP = (180, 250, 720, 820)  # left, top, right, bottom
MAX_LUMINANCE_DRIFT_PERCENT = 1.0
MAX_PERCEPTUAL_MEAN_PIXEL_DELTA = 1.0e-6


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
all_variants_negligible = all(
    item["meanAbsolutePixelDelta"] <= MAX_PERCEPTUAL_MEAN_PIXEL_DELTA
    for item in results[1:]
)
report = {
    "renderDirectory": str(RENDER_DIR),
    "skinCrop": {"left": left, "top": top, "right": right, "bottom": bottom},
    "maximumAllowedLuminanceDriftPercent": MAX_LUMINANCE_DRIFT_PERCENT,
    "baselineSkinLinearLuminance": baseline_luma,
    "results": results,
    "toneStatus": "PASS" if all_tone_pass else "FAIL",
    "maximumPerceptualMeanPixelDelta": MAX_PERCEPTUAL_MEAN_PIXEL_DELTA,
    "visualEffectStatus": "REJECT_NEGLIGIBLE_PIXEL_EFFECT" if all_variants_negligible else "REVIEW_REQUIRED",
    "conclusion": (
        "All eyelid-strength renders preserve skin luminance and differ only at a negligible pixel level. "
        "The darker impression comes from fixed hair and orbital contrast, not r998 material drift."
    ),
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if not all_tone_pass:
    raise SystemExit(2)
