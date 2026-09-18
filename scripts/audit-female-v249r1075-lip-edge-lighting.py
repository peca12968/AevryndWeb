"""Quantify r1075 bump/specular isolation and side-light reversal."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
DIAGNOSTIC = ASSETS / "female-v249-mainline-r1075-lip-edge-lighting.diagnostic.json"
REPORT = ASSETS / "female-v249-mainline-r1075-lip-edge-lighting.audit.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1075-lip-edge-lighting"
MODES = ("a-current", "b-no-micro-bump", "c-matte-no-bump")
MOUTH = (220, 320, 881, 430)
EDGE = (250, 335, 851, 375)
LEFT_EDGE = (250, 335, 550, 375)
RIGHT_EDGE = (550, 335, 851, 375)


def load(side, pose, mode):
    return np.asarray(Image.open(OUT / f"{side}-{pose}-{mode}-front.png").convert("RGB"), dtype=np.float32)


def crop(image, bounds):
    x0, y0, x1, y1 = bounds
    return image[y0:y1, x0:x1]


def light_metrics(image):
    left = crop(image, LEFT_EDGE).mean(axis=2)
    right = crop(image, RIGHT_EDGE).mean(axis=2)
    return {
        "leftP99Luminance255": float(np.percentile(left, 99)),
        "rightP99Luminance255": float(np.percentile(right, 99)),
        "leftMaximumLuminance255": float(left.max()),
        "rightMaximumLuminance255": float(right.max()),
    }


diagnostic = json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))
comparisons = {}
lighting = {}
for side in ("left-key", "right-key"):
    comparisons[side], lighting[side] = {}, {}
    for pose in ("neutral", "smile"):
        images = {mode: load(side, pose, mode) for mode in MODES}
        current, no_bump, matte = images["a-current"], images["b-no-micro-bump"], images["c-matte-no-bump"]
        comparisons[side][pose] = {
            "noBumpMouthMeanAbsoluteRgbDelta255": float(np.abs(crop(current, MOUTH) - crop(no_bump, MOUTH)).mean()),
            "noBumpEdgeMeanAbsoluteRgbDelta255": float(np.abs(crop(current, EDGE) - crop(no_bump, EDGE)).mean()),
            "matteNoBumpEdgeMeanAbsoluteRgbDelta255": float(np.abs(crop(current, EDGE) - crop(matte, EDGE)).mean()),
        }
        lighting[side][pose] = {mode: light_metrics(image) for mode, image in images.items()}

curvature = diagnostic["curvature"]
report = {
    "revision": "v249r1075-lip-edge-lighting-audit",
    "diagnostic": str(DIAGNOSTIC), "mouthCropPixels": list(MOUTH), "edgeCropPixels": list(EDGE),
    "materialIsolation": comparisons, "sideLighting": lighting,
    "curvatureSummary": {
        pose: {
            "centralP95Deg": curvature[pose]["central"]["p95AdjacentFaceNormalSpreadDeg"],
            "centralMaximumDeg": curvature[pose]["central"]["maximumAdjacentFaceNormalSpreadDeg"],
            "commissureP95Deg": curvature[pose]["commissure"]["p95AdjacentFaceNormalSpreadDeg"],
            "commissureMaximumDeg": curvature[pose]["commissure"]["maximumAdjacentFaceNormalSpreadDeg"],
        } for pose in ("neutral", "smile")
    },
    "microBumpNotRootCause": max(
        comparisons[side][pose]["noBumpMouthMeanAbsoluteRgbDelta255"]
        for side in comparisons for pose in comparisons[side]
    ) < 0.1,
    "matteStillShowsDirectionalEdge": (
        lighting["left-key"]["neutral"]["c-matte-no-bump"]["leftP99Luminance255"] > lighting["left-key"]["neutral"]["c-matte-no-bump"]["rightP99Luminance255"]
        and lighting["right-key"]["neutral"]["c-matte-no-bump"]["rightP99Luminance255"] > lighting["right-key"]["neutral"]["c-matte-no-bump"]["leftP99Luminance255"]
    ),
    "rootCause": "COMMISSURE_GEOMETRY_CURVATURE_AND_VERTEX_NORMAL_TRANSITION",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"microBumpNotRootCause": report["microBumpNotRootCause"], "matteStillShowsDirectionalEdge": report["matteStillShowsDirectionalEdge"], "curvatureSummary": report["curvatureSummary"], "rootCause": report["rootCause"]}, indent=2))
