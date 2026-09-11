import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parent / "Temp/female-realism/v249r358-corrected-forehead-roi-prune-sweep/a-current-face.png"
PREVIOUS = ROOT.parent / "Temp/female-realism/v249r371-perceptual-contrast-groom/01-front-f01.png"
CANDIDATE = ROOT.parent / "Temp/female-realism/v249r398-runtime-sparse-baby-hairs/01-front-f01.png"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r398.perceptual-contrast-audit.json"


def linear_luminance(rgb):
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
            values.append(linear_luminance(pixels[offset:offset + 3]))
    bpy.data.images.remove(image)
    return sum(values) / len(values)


# The central skin patch avoids hair, eyes, nostrils and lips.  The upper band
# deliberately includes forehead and hairline so the shadow/readability change
# is measured separately from the skin shader.
regions = {
    "central_skin": (0.38, 0.32, 0.62, 0.62),
    "forehead_hairline_context": (0.25, 0.61, 0.75, 0.86),
    "whole_character_frame": (0.08, 0.05, 0.92, 0.95),
}
images = {"r358_reference": REFERENCE, "r371_baseline": PREVIOUS, "r398_candidate": CANDIDATE}
measurement = {
    image_name: {region: mean_region(path, bounds) for region, bounds in regions.items()}
    for image_name, path in images.items()
}

central_ref = measurement["r358_reference"]["central_skin"]
central_old = measurement["r371_baseline"]["central_skin"]
central_new = measurement["r398_candidate"]["central_skin"]
context_old = measurement["r371_baseline"]["forehead_hairline_context"]
context_new = measurement["r398_candidate"]["forehead_hairline_context"]
whole_old = measurement["r371_baseline"]["whole_character_frame"]
whole_new = measurement["r398_candidate"]["whole_character_frame"]
report = {
    "reference": str(REFERENCE),
    "previous": str(PREVIOUS),
    "candidate": str(CANDIDATE),
    "space": "scene-linear Rec.709 luminance",
    "normalizedRegions": regions,
    "measurements": measurement,
    "historicalReferenceCaveat": "r358 uses a different camera crop; its normalized fixed region is recorded for context only and is not a pass/fail comparator.",
    "centralSkinDeltaFromR371Percent": 100.0 * (central_new / central_old - 1.0),
    "hairlineContextDeltaFromR371Percent": 100.0 * (context_new / context_old - 1.0),
    "wholeFrameDeltaFromR371Percent": 100.0 * (whole_new / whole_old - 1.0),
    "gate": {
        "centralSkinStableWithinOnePercentOfR371": abs(central_new / central_old - 1.0) <= 0.01,
        "hairlineContextNoMoreThanTwoPercentDarkerThanR371": context_new / context_old >= 0.98,
        "wholeFrameNotDarkerThanR371": whole_new / whole_old >= 1.0,
    },
}
report["status"] = "PASS" if all(report["gate"].values()) else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R398_PERCEPTUAL_CONTRAST=" + json.dumps(report, sort_keys=True))


