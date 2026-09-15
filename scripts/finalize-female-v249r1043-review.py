import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets-source" / "aevrynd-character"
TEMP_ROOT = ROOT.parent / "Temp" / "female-realism"
REFERENCE = TEMP_ROOT / "v249r1039-lip-material-sweep" / "b-natural-vermilion-face-front.png"
SELECTED = TEMP_ROOT / "v249r1043-split-lip-grid" / "face-front.png"
AUDIT = ASSET_ROOT / "female-v249-mainline-r1043-split-lip-grid-tone-audit.json"
REVIEW_DIR = ASSET_ROOT / "reviews" / "v249r1043-split-lip-grid"

CROPS = {
    "leftCheek": (210, 500, 340, 650),
    "rightCheek": (660, 500, 790, 650),
    "forehead": (400, 140, 600, 280),
}


def srgb_to_linear(value):
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def crop_luminance(path, bounds):
    image = Image.open(path).convert("RGB")
    pixels = image.crop(bounds).get_flattened_data()
    total = 0.0
    count = 0
    for red, green, blue in pixels:
        total += 0.2126 * srgb_to_linear(red) + 0.7152 * srgb_to_linear(green) + 0.0722 * srgb_to_linear(blue)
        count += 1
    return total / count


reference_values = {name: crop_luminance(REFERENCE, bounds) for name, bounds in CROPS.items()}
selected_values = {name: crop_luminance(SELECTED, bounds) for name, bounds in CROPS.items()}
drift = {
    name: (selected_values[name] / reference_values[name] - 1.0) * 100.0
    for name in CROPS
}
maximum = max(abs(value) for value in drift.values())
audit = {
    "revision": "v249r1043",
    "reference": "r1039 b-natural-vermilion fixed-light face-front",
    "selected": "r1043 split upper/lower horizontal lip-grid study",
    "crops": {name: list(bounds) for name, bounds in CROPS.items()},
    "referenceLuminance": reference_values,
    "selectedLuminance": selected_values,
    "selectedRelativeDriftPercent": drift,
    "maximumAbsoluteDriftPercent": maximum,
    "gatePercent": 1.0,
    "status": "PASS_NO_GLOBAL_DARKENING" if maximum <= 1.0 else "FAIL_TONE_DRIFT",
    "websiteStatus": "Website v83 remains unchanged and 5.56% darker in embedded skin base color than the committed Blender mainline.",
}
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
items = [
    (TEMP_ROOT / "v249r1033-lower-lip-rim-turn-sweep" / "b-safe-turn-mouth-front.png", "r1033 retained | 39/100"),
    (TEMP_ROOT / "v249r1042-full-perioral-patch" / "mouth-front.png", "r1042 annulus rejected | 18/100"),
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "mouth-front.png", "r1043 split grid | 17/100"),
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "mouth-oblique.png", "r1043 oblique"),
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "face-front.png", "r1043 full face"),
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "open.png", "r1043 mouth-open probe"),
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "smile.png", "r1043 smile probe"),
]
cell_width, cell_height, label_height = 560, 340, 42
sheet = Image.new("RGB", (cell_width * 4, (cell_height + label_height) * 2 + 72), (24, 24, 24))
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=22)
draw.text((24, 20), "Aevrynd v249r1043 strict mouth review | TECHNICAL PASS / VISUAL REJECT", fill=(240, 240, 240), font=font)
for index, (path, label) in enumerate(items):
    image = Image.open(path).convert("RGB")
    fitted = ImageOps.fit(image, (cell_width, cell_height), method=Image.Resampling.LANCZOS)
    column, row = index % 4, index // 4
    left, top = column * cell_width, 72 + row * (cell_height + label_height)
    sheet.paste(fitted, (left, top))
    draw.rectangle((left, top + cell_height, left + cell_width, top + cell_height + label_height), fill=(36, 36, 36))
    draw.text((left + 12, top + cell_height + 9), label, fill=(235, 235, 235), font=font)
sheet.save(REVIEW_DIR / "contact-sheet-r1043.jpg", quality=94, subsampling=0)

readme = f"""# v249 r1043 split lip-grid review

r1043 replaces the complete r1039 mouth region with separate upper and lower horizontal quad grids joined by two shared commissure poles. It is a technical topology experiment and is visually rejected.

- The deterministic build removes 832 faces and adds 574 vertices plus 576 faces. All 35 shape keys remain index-compatible and every new vertex carries at least four deform groups.
- Frames 1/20/33/61 plus mouth-open and smile pass with zero non-adjacent body self-collision and zero overlap against all six owned oral layers.
- Strict mouth quality is 17/100, below r1042 at 18/100 and retained r1033 at 39/100. The raw outer boundary creates repeated pinch spikes; both lip grids read as inflated slabs; the shallow slit exposes planar oral layers; and the expression probes show no credible jaw-coupled motion.
- Fixed-crop drift from r1039 is {drift['leftCheek']:+.6f}% left cheek, {drift['rightCheek']:+.6f}% right cheek and {drift['forehead']:+.6f}% forehead. The plus-or-minus 1% tone gate {'passes' if maximum <= 1.0 else 'fails'}.
- Website promotion is forbidden. r1033 remains the retained mouth and face candidate, and website v83 remains unchanged.

The full-perioral replacement route is closed. The next build must preserve the stable r1033 outer facial surface and reconstruct only the inner vermilion, wetline and commissures with local curvature-constrained loops, deeper oral presentation and visibly distinct mouth-open and smile deformation.
"""
(REVIEW_DIR / "README.md").write_text(readme, encoding="utf-8")

print(json.dumps({"audit": str(AUDIT), "review": str(REVIEW_DIR / "contact-sheet-r1043.jpg"), "toneStatus": audit["status"], "maxDriftPercent": maximum}, indent=2))
