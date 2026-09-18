"""Measure r1072 rim suppression and fixed-crop tone isolation."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
STUDY = ASSETS / "female-v249-mainline-r1072-continuous-inner-rim-mask.study.json"
REPORT = ASSETS / "female-v249-mainline-r1072-continuous-inner-rim-mask.tone-audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1072-continuous-inner-rim"
CONTROL = "a-control"
SELECTED = "e-balanced-1.35mm"
CROPS = {
    "rim": (250, 336, 851, 365),
    "mouth": (220, 320, 881, 451),
    "leftCheek": (80, 200, 240, 500),
    "rightCheek": (860, 200, 1020, 500),
    "upperFace": (300, 40, 800, 250),
}


def load(label, pose):
    return np.asarray(Image.open(OUT / f"{label}-{pose}.png").convert("RGB"), dtype=np.float32)


def metrics(image, control, crop):
    x0, y0, x1, y1 = crop
    sample = image[y0:y1, x0:x1]
    reference = control[y0:y1, x0:x1]
    luminance = sample.mean(axis=2)
    return {
        "meanLuminance255": float(luminance.mean()),
        "p95Luminance255": float(np.percentile(luminance, 95)),
        "p99Luminance255": float(np.percentile(luminance, 99)),
        "maximumLuminance255": float(luminance.max()),
        "meanAbsoluteRgbDelta255": float(np.abs(sample - reference).mean()),
    }


study = json.loads(STUDY.read_text(encoding="utf-8"))
labels = [item["label"] for item in study["variants"]]
front_control = load(CONTROL, "neutral-front")
front = {
    label: {name: metrics(load(label, "neutral-front"), front_control, crop) for name, crop in CROPS.items()}
    for label in labels
}
pose_deltas = {}
for pose in ("neutral-oblique", "open"):
    control = load(CONTROL, pose)
    selected = load(SELECTED, pose)
    pose_deltas[pose] = {
        "fullFrameMeanAbsoluteRgbDelta255": float(np.abs(selected - control).mean()),
        "mouthCropMeanAbsoluteRgbDelta255": metrics(selected, control, CROPS["mouth"])["meanAbsoluteRgbDelta255"],
    }
control_rim = front[CONTROL]["rim"]
selected_rim = front[SELECTED]["rim"]
report = {
    "revision": "v249r1072-continuous-inner-rim-mask-tone-audit",
    "study": str(STUDY),
    "control": CONTROL,
    "selected": SELECTED,
    "cropsPixels": {name: list(crop) for name, crop in CROPS.items()},
    "frontMetrics": front,
    "selectedPoseDeltas": pose_deltas,
    "selectedRimChange": {
        "meanLuminanceDelta255": selected_rim["meanLuminance255"] - control_rim["meanLuminance255"],
        "p99LuminanceDelta255": selected_rim["p99Luminance255"] - control_rim["p99Luminance255"],
        "maximumLuminanceDelta255": selected_rim["maximumLuminance255"] - control_rim["maximumLuminance255"],
    },
    "fixedCropIsolationPass": all(front[SELECTED][name]["meanAbsoluteRgbDelta255"] <= 0.001 for name in ("leftCheek", "rightCheek", "upperFace")),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"selectedRimChange": report["selectedRimChange"], "fixedCropIsolationPass": report["fixedCropIsolationPass"], "poseDeltas": pose_deltas}, indent=2))
