import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets-source" / "aevrynd-character"
TEMP_ROOT = ROOT.parent / "Temp" / "female-realism"
REFERENCE = TEMP_ROOT / "v249r1033-lower-lip-rim-turn-sweep" / "b-safe-turn-face-front.png"
SELECTED = TEMP_ROOT / "v249r1044-local-inner-lip" / "face-front.png"
AUDIT = ASSET_ROOT / "female-v249-mainline-r1044-local-inner-lip-tone-audit.json"
REVIEW_DIR = ASSET_ROOT / "reviews" / "v249r1044-local-inner-lip"
CROPS = {
    "leftCheek": (210, 500, 340, 650),
    "rightCheek": (660, 500, 790, 650),
    "forehead": (400, 140, 600, 280),
}


def srgb_to_linear(value):
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def crop_luminance(path, bounds):
    pixels = Image.open(path).convert("RGB").crop(bounds).get_flattened_data()
    values = [
        0.2126 * srgb_to_linear(red) + 0.7152 * srgb_to_linear(green) + 0.0722 * srgb_to_linear(blue)
        for red, green, blue in pixels
    ]
    return sum(values) / len(values)


reference_values = {name: crop_luminance(REFERENCE, bounds) for name, bounds in CROPS.items()}
selected_values = {name: crop_luminance(SELECTED, bounds) for name, bounds in CROPS.items()}
drift = {name: (selected_values[name] / reference_values[name] - 1.0) * 100.0 for name in CROPS}
maximum = max(abs(value) for value in drift.values())
audit = {
    "revision": "v249r1044",
    "reference": "retained r1033 b-safe-turn fixed-light face-front",
    "selected": "r1044 local inner-lip aperture study",
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
    (TEMP_ROOT / "v249r1043-split-lip-grid" / "mouth-front.png", "r1043 rejected | 17/100"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "mouth-front.png", "r1044 local aperture | 30/100"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "mouth-oblique.png", "r1044 oblique"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "face-front.png", "r1044 full face"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "mouth-no-oral-layers.png", "r1044 inherited fold isolation"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "open.png", "r1044 mouth-open probe"),
    (TEMP_ROOT / "v249r1044-local-inner-lip" / "smile.png", "r1044 smile probe"),
]
cell_width, cell_height, label_height = 560, 340, 42
sheet = Image.new("RGB", (cell_width * 4, (cell_height + label_height) * 2 + 72), (24, 24, 24))
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=22)
draw.text((24, 20), "Aevrynd v249r1044 local inner-lip review | TECHNICAL PASS / VISUAL REJECT", fill=(240, 240, 240), font=font)
for index, (path, label) in enumerate(items):
    fitted = ImageOps.fit(Image.open(path).convert("RGB"), (cell_width, cell_height), method=Image.Resampling.LANCZOS)
    column, row = index % 4, index // 4
    left, top = column * cell_width, 72 + row * (cell_height + label_height)
    sheet.paste(fitted, (left, top))
    draw.rectangle((left, top + cell_height, left + cell_width, top + cell_height + label_height), fill=(36, 36, 36))
    draw.text((left + 12, top + cell_height + 9), label, fill=(235, 235, 235), font=font)
sheet.save(REVIEW_DIR / "contact-sheet-r1044.jpg", quality=94, subsampling=0)

readme = f"""# v249 r1044 local inner-lip review

r1044 returns to retained r1033 and limits the opening to a 20-by-0.8 mm inner-lip band. It preserves the outer face, adds three attached 36-vertex support rings and rebuilds six explicitly named Aevrynd-owned oral layers.

- The deterministic build removes 20 main faces, four residual candidate faces and 326 hidden faces; it adds 108 weighted vertices and 108 faces. All 35 shape keys remain compatible and every new vertex carries at least five deform groups.
- Frames 1/20/33/61 plus mouth-open and smile pass with zero non-adjacent body self-collision and zero body-to-oral-layer overlap.
- Strict mouth quality is 30/100, below retained r1033 at 39/100. The stable outer lip survives, but inherited folded faces from the main head component remain visible through the slit. Ray-guided deletion exposes deeper fragments and material reassignment creates hanging tabs, so both diagnostics are rejected.
- Fixed-crop drift from r1033 is {drift['leftCheek']:+.6f}% left cheek, {drift['rightCheek']:+.6f}% right cheek and {drift['forehead']:+.6f}% forehead. The plus-or-minus 1% tone gate {'passes' if maximum <= 1.0 else 'fails'}.
- Website promotion is forbidden. r1033 remains the retained mouth and face candidate.

The next mouth build must start from a clean contiguous oral vestibule with explicit upper and lower inner-lip paths, then transfer the retained r1033 outer facial surface onto it. Excavating or recoloring the inherited folded head is closed.
"""
(REVIEW_DIR / "README.md").write_text(readme, encoding="utf-8")
print(json.dumps({"audit": str(AUDIT), "review": str(REVIEW_DIR / "contact-sheet-r1044.jpg"), "toneStatus": audit["status"], "maxDriftPercent": maximum}, indent=2))
