import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = ASSETS / "reviews/v249r520-natural-eye-ratio-11shot/08-face-front.png"
CANDIDATE = ASSETS / "reviews/v249r522-natural-commissures-11shot/08-face-front.png"
REPORT = ASSETS / "female-v249-mainline-natural-commissures-r522.tone-contract-audit.json"
REGIONS = {
    "forehead": (0.38, 0.64, 0.62, 0.78),
    "leftCheek": (0.31, 0.31, 0.43, 0.47),
    "rightCheek": (0.57, 0.31, 0.69, 0.47),
    "chin": (0.43, 0.17, 0.57, 0.27),
}


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


measurements = {
    label: {name: mean(path, bounds) for name, bounds in REGIONS.items()}
    for label, path in (("baseline", BASELINE), ("candidate", CANDIDATE))
}
deltas = {
    name: 100.0 * (measurements["candidate"][name] / measurements["baseline"][name] - 1.0)
    for name in REGIONS
}
report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "space": "scene-linear Rec.709 luminance",
    "regions": REGIONS,
    "measurements": measurements,
    "deltaPercent": deltas,
    "gate": "all fixed skin regions within 1 percent",
    "status": "PASS" if all(abs(value) <= 1.0 for value in deltas.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R522_TONE=" + json.dumps({"status": report["status"], "deltaPercent": deltas}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
