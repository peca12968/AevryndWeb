import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "assets-source" / "aevrynd-character" / "reviews" / "v249r505-rear-layer-replacement-sweep"
CANDIDATE_DIR = ROOT / "assets-source" / "aevrynd-character" / "reviews" / "v249r506-layered-rear-locks-build"
REPORT = ROOT / "assets-source" / "aevrynd-character" / "female-v249-mainline-layered-rear-locks-r506.tone-contract-audit.json"


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def mean(path, bounds):
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


front_regions = {
    "central_skin": (0.40, 0.38, 0.60, 0.64),
    "left_cheek": (0.31, 0.31, 0.43, 0.47),
    "right_cheek": (0.57, 0.31, 0.69, 0.47),
    "forehead": (0.38, 0.64, 0.62, 0.78),
}
measurements = {"baseline": {}, "candidate": {}}
for label, path in {
    "baseline": BASE_DIR / "a-r499-current-front.png",
    "candidate": CANDIDATE_DIR / "r506-layered-rear-locks-front.png",
}.items():
    measurements[label] = {name: mean(path, bounds) for name, bounds in front_regions.items()}

back_bounds = (0.30, 0.24, 0.70, 0.78)
measurements["baseline"]["rear_hair_context"] = mean(BASE_DIR / "a-r499-current-back.png", back_bounds)
measurements["candidate"]["rear_hair_context"] = mean(CANDIDATE_DIR / "r506-layered-rear-locks-back.png", back_bounds)
deltas = {
    name: 100.0 * (measurements["candidate"][name] / value - 1.0)
    for name, value in measurements["baseline"].items()
}
gate = {
    "skinRegionsWithinOnePercent": all(abs(deltas[name]) <= 1.0 for name in front_regions),
    "rearHairContextNoMoreThanFivePercentDarker": deltas["rear_hair_context"] >= -5.0,
}
report = {
    "baselineFront": str(BASE_DIR / "a-r499-current-front.png"),
    "candidateFront": str(CANDIDATE_DIR / "r506-layered-rear-locks-front.png"),
    "space": "scene-linear Rec.709 luminance",
    "normalizedRegions": {**front_regions, "rear_hair_context": back_bounds},
    "measurements": measurements,
    "deltaPercent": deltas,
    "gate": gate,
    "status": "PASS" if all(gate.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R506_TONE=" + json.dumps({"status": report["status"], "deltaPercent": deltas}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
