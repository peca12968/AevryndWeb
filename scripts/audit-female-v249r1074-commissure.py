"""Audit horizontal commissure convergence and non-mouth isolation for r1074."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
STUDY = ASSETS / "female-v249-mainline-r1074-commissure-falloff.study.json"
REPORT = ASSETS / "female-v249-mainline-r1074-commissure-falloff.tone-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1074-commissure-falloff"
CONTROL = "a-control"
BASELINE = "b-r1073-baseline"
SELECTED = "e-extend-2.50-radius-0.40"
CROPS = {
    "centralRim": (460, 336, 640, 365),
    "mouth": (220, 315, 881, 430),
    "leftCheek": (80, 200, 240, 500),
    "rightCheek": (860, 200, 1020, 500),
    "upperFace": (300, 40, 800, 250),
}
TARGETS = {"neutral-front": (818, 356), "open": (817, 367)}


def load(label, pose):
    return np.asarray(Image.open(OUT / f"{label}-{pose}.png").convert("RGB"), dtype=np.float32)


def crop(image, bounds):
    x0, y0, x1, y1 = bounds
    return image[y0:y1, x0:x1]


def luminance_metrics(image):
    lum = image.mean(axis=2)
    return {
        "meanLuminance255": float(lum.mean()),
        "p99Luminance255": float(np.percentile(lum, 99)),
        "maximumLuminance255": float(lum.max()),
    }


study = json.loads(STUDY.read_text(encoding="utf-8"))
labels = [item["label"] for item in study["variants"]]
poses = ("neutral-front", "neutral-oblique", "open")
variant_metrics = {}
for label in labels:
    variant_metrics[label] = {}
    for pose in poses:
        image, baseline = load(label, pose), load(BASELINE, pose)
        variant_metrics[label][pose] = {
            "mouth": luminance_metrics(crop(image, CROPS["mouth"])),
            "centralRim": luminance_metrics(crop(image, CROPS["centralRim"])),
            "mouthMeanAbsoluteRgbDeltaFromR1073": float(np.abs(crop(image, CROPS["mouth"]) - crop(baseline, CROPS["mouth"])).mean()),
        }

target_metrics = {}
for pose, (x, y) in TARGETS.items():
    target_metrics[pose] = {}
    for label in labels:
        image = load(label, pose)
        target_metrics[pose][label] = {
            "pixelRgb255": [float(value) for value in image[y, x]],
            "pixelMean255": float(image[y, x].mean()),
            "localPatchP99Luminance255": float(np.percentile(image[y - 6:y + 7, x - 10:x + 11].mean(axis=2), 99)),
        }

front_baseline, front_selected = load(BASELINE, "neutral-front"), load(SELECTED, "neutral-front")
isolation = {
    name: float(np.abs(crop(front_selected, bounds) - crop(front_baseline, bounds)).mean())
    for name, bounds in CROPS.items() if name in ("centralRim", "leftCheek", "rightCheek", "upperFace")
}

horizontal_bins = []
base_lum, selected_lum = front_baseline.mean(axis=2), front_selected.mean(axis=2)
for x0, x1 in zip(np.linspace(220, 881, 12, dtype=int)[:-1], np.linspace(220, 881, 12, dtype=int)[1:]):
    bounds = (int(x0), 330, int(x1), 410)
    b, s = crop(base_lum[:, :, None], bounds)[:, :, 0], crop(selected_lum[:, :, None], bounds)[:, :, 0]
    horizontal_bins.append({
        "xPixels": [int(x0), int(x1)],
        "r1073P99Luminance255": float(np.percentile(b, 99)),
        "selectedP99Luminance255": float(np.percentile(s, 99)),
        "meanAbsoluteLuminanceDelta255": float(np.abs(s - b).mean()),
    })

report = {
    "revision": "v249r1074-commissure-falloff-tone-audit",
    "study": str(STUDY), "control": CONTROL, "baseline": BASELINE, "selected": SELECTED,
    "cropsPixels": {name: list(bounds) for name, bounds in CROPS.items()},
    "targetPixels": {pose: list(point) for pose, point in TARGETS.items()},
    "variantMetrics": variant_metrics, "targetMetrics": target_metrics,
    "selectedIsolationFromR1073": isolation, "frontHorizontalBins": horizontal_bins,
    "centralResponseUnchanged": isolation["centralRim"] <= 0.001,
    "fixedCropIsolationThresholdMeanAbsoluteRgb255": 0.005,
    "fixedCropIsolationPass": all(isolation[name] <= 0.005 for name in ("leftCheek", "rightCheek", "upperFace")),
    "selectedTargetChangeFromR1073": {
        pose: target_metrics[pose][SELECTED]["pixelMean255"] - target_metrics[pose][BASELINE]["pixelMean255"]
        for pose in TARGETS
    },
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ("selectedTargetChangeFromR1073", "selectedIsolationFromR1073", "centralResponseUnchanged", "fixedCropIsolationPass")}, indent=2))
