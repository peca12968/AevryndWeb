import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
PREVIOUS = ASSETS / "reviews/v249r467-runtime-soft-rear-fan-cards/01-front-f01.png"
CANDIDATE = ASSETS / "reviews/v249r468-runtime-balanced-brunette/01-front-f01.png"
REPORT = ASSETS / "female-v249-mainline-r468.hair-value-audit.json"


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def mean_region(path, bounds):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = list(image.pixels[:])
    x0, y0, x1, y1 = bounds
    values = []
    for y in range(round(y0 * height), round(y1 * height)):
        for x in range(round(x0 * width), round(x1 * width)):
            offset = 4 * (y * width + x)
            values.append(luminance(pixels[offset:offset + 3]))
    bpy.data.images.remove(image)
    return sum(values) / len(values)


regions = {
    "central_skin": (0.38, 0.32, 0.62, 0.62),
    "left_hair_mass": (0.08, 0.10, 0.28, 0.72),
    "right_hair_mass": (0.72, 0.10, 0.92, 0.72),
    "crown_hair": (0.28, 0.82, 0.72, 0.96),
}
measurements = {
    "r467": {name: mean_region(PREVIOUS, bounds) for name, bounds in regions.items()},
    "r468": {name: mean_region(CANDIDATE, bounds) for name, bounds in regions.items()},
}
deltas = {
    name: 100.0 * (measurements["r468"][name] / measurements["r467"][name] - 1.0)
    for name in regions
}
report = {
    "previous": str(PREVIOUS),
    "candidate": str(CANDIDATE),
    "space": "scene-linear Rec.709 luminance",
    "normalizedRegions": regions,
    "measurements": measurements,
    "deltaPercent": deltas,
    "materialChange": "2.0x card base-color value control; alpha, geometry, rig weights and collision envelope unchanged from r467",
    "gates": {
        "centralSkinStableWithinOnePercent": abs(deltas["central_skin"]) <= 1.0,
        "leftHairMassAtLeastTenPercentBrighter": deltas["left_hair_mass"] >= 10.0,
        "rightHairMassAtLeastTenPercentBrighter": deltas["right_hair_mass"] >= 10.0,
    },
}
report["status"] = "PASS" if all(report["gates"].values()) else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R468_HAIR_VALUE=" + json.dumps(report, sort_keys=True))
