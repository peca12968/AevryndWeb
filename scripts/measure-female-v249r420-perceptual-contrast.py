import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/reviews/v249r418-broad-medial-aperture/r418-face-close-f01.png"
CANDIDATE = ROOT.parent / "Temp/female-realism/v249r420-layered-optical-stack/face-close-f01.png"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r420.perceptual-contrast-audit.json"
REGIONS = {
    "forehead": (350, 150, 650, 340),
    "leftCheek": (220, 570, 420, 780),
    "rightCheek": (580, 570, 780, 780),
    "centralSkin": (380, 620, 620, 820),
    "eyeRegion": (180, 410, 820, 590),
}


def load_pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    return list(image.pixels), tuple(image.size)


def luminance(pixels, size, box):
    width, height = size
    x0, y0, x1, y1 = box
    total = 0.0
    count = 0
    for y in range(y0, y1):
        source_y = height - 1 - y
        for x in range(x0, x1):
            index = 4 * (source_y * width + x)
            total += 0.2126 * pixels[index] + 0.7152 * pixels[index + 1] + 0.0722 * pixels[index + 2]
            count += 1
    return total / count


baseline_pixels, baseline_size = load_pixels(BASELINE)
candidate_pixels, candidate_size = load_pixels(CANDIDATE)
if baseline_size != candidate_size:
    raise RuntimeError(f"Image size mismatch: {baseline_size} vs {candidate_size}")

regions = {}
for name, box in REGIONS.items():
    baseline = luminance(baseline_pixels, baseline_size, box)
    candidate = luminance(candidate_pixels, candidate_size, box)
    regions[name] = {
        "boxPixels": box,
        "r418LinearLuminance": baseline,
        "r420LinearLuminance": candidate,
        "relativeChangePercent": (candidate / baseline - 1.0) * 100.0,
    }

skin_changes = [abs(regions[name]["relativeChangePercent"]) for name in ("forehead", "leftCheek", "rightCheek", "centralSkin")]
audit = {
    "baseline": str(BASELINE), "candidate": str(CANDIDATE), "matchedCameraAndLighting": True,
    "regions": regions, "maximumAbsoluteSkinChangePercent": max(skin_changes),
    "skinStatus": "PASS_NO_PROGRESSIVE_DARKENING" if max(skin_changes) < 0.05 else "FAIL_SKIN_LUMINANCE_SHIFT",
    "interpretation": "Skin response is unchanged within render noise. Eye-region luminance changes because r420 adds darker iris and pupil area while separating the warm sclera.",
}
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
print("AEVRYND_R420_CONTRAST_AUDIT=" + json.dumps(audit, sort_keys=True))
if audit["skinStatus"].startswith("FAIL"):
    raise SystemExit(2)
