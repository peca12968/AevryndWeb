import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEXTURES = ASSETS / "textures"
COLOUR_ALPHA = TEXTURES / "aevrynd-owned-hair-clump-colour-alpha-r544.png"
NORMAL = TEXTURES / "aevrynd-owned-hair-clump-normal-r544.png"
ROUGHNESS = TEXTURES / "aevrynd-owned-hair-clump-roughness-r544.png"
REPORT = ASSETS / "female-v249-mainline-dense-clump-atlas-r544.build.json"
SIZE = 1024
SLOT = SIZE // 4
SEED = 249544
random.seed(SEED)


def smooth_tip(value):
    value = max(0.0, min(1.0, (value - 0.64) / 0.36))
    return value * value * (3.0 - 2.0 * value)

alpha = Image.new("L", (SIZE, SIZE), 0)
alpha_draw = ImageDraw.Draw(alpha)
normal = Image.new("RGB", (SIZE, SIZE), (128, 128, 255))
normal_draw = ImageDraw.Draw(normal)
roughness = Image.new("L", (SIZE, SIZE), 170)
roughness_draw = ImageDraw.Draw(roughness)

slot_specs = (
    {"fibres": 112, "spread": 0.92, "wave": 3.0, "alpha": 225, "width": 3},
    {"fibres": 88, "spread": 0.84, "wave": 5.0, "alpha": 218, "width": 3},
    {"fibres": 66, "spread": 0.74, "wave": 7.0, "alpha": 210, "width": 4},
    {"fibres": 48, "spread": 0.62, "wave": 9.5, "alpha": 200, "width": 4},
)

for slot_index, spec in enumerate(slot_specs):
    slot_left = slot_index * SLOT
    center_x = slot_left + SLOT * 0.5
    usable = SLOT * spec["spread"]
    for fibre in range(spec["fibres"]):
        index = slot_index * 1000 + fibre
        root_unit = (fibre + 0.5) / spec["fibres"]
        root_x = center_x + (root_unit - 0.5) * usable + random.uniform(-1.8, 1.8)
        phase = random.random() * math.tau
        frequency = random.uniform(0.55, 1.10)
        lean = random.uniform(-12.0, 12.0)
        tip_fan = random.uniform(-18.0, 18.0) * (0.45 + slot_index * 0.18)
        points = []
        normals = []
        for segment in range(49):
            t = segment / 48.0
            y = SIZE - 2 - t * (SIZE - 4)
            envelope = math.sin(math.pi * t) ** 1.1
            wave = math.sin(phase + t * math.tau * frequency) * spec["wave"] * envelope
            fan = tip_fan * smooth_tip(t)
            x = root_x + lean * t + wave + fan
            points.append((x, y))
            dx = lean / SIZE + math.cos(phase + t * math.tau * frequency) * spec["wave"] * math.tau * frequency / SIZE
            normals.append(int(max(88, min(168, 128 + dx * 620))))
        strand_alpha = int(spec["alpha"] * random.uniform(0.82, 1.0))
        strand_width = spec["width"] + (1 if fibre % 9 == 0 else 0)
        alpha_draw.line(points, fill=strand_alpha, width=strand_width)
        for segment in range(len(points) - 1):
            normal_draw.line((points[segment], points[segment + 1]), fill=(normals[segment], 128, 255), width=strand_width)
        roughness_value = int(random.uniform(145, 190))
        roughness_draw.line(points, fill=roughness_value, width=strand_width + 1)
    # Dense root core and a softer interior coverage make each slot a clump,
    # while the individual tips remain separated by the fibre endpoints.
    core_width = int(usable * (0.72 - slot_index * 0.055))
    alpha_draw.rounded_rectangle(
        (center_x - core_width / 2, SIZE * 0.84, center_x + core_width / 2, SIZE - 1),
        radius=18,
        fill=210 - slot_index * 12,
    )

alpha = alpha.filter(ImageFilter.GaussianBlur(0.65))
colour = Image.new("RGBA", (SIZE, SIZE), (103, 55, 37, 0))
colour_pixels = colour.load()
alpha_pixels = alpha.load()
roughness_pixels = roughness.load()
for y in range(SIZE):
    longitudinal = y / (SIZE - 1)
    for x in range(SIZE):
        slot_index = min(3, x // SLOT)
        low_frequency = math.sin(x * 0.031 + y * 0.006 + slot_index * 1.7)
        highlight = 8.0 * max(0.0, low_frequency) * (0.35 + 0.65 * longitudinal)
        colour_pixels[x, y] = (int(98 + highlight), int(51 + highlight * 0.55), int(34 + highlight * 0.38), alpha_pixels[x, y])
        roughness_pixels[x, y] = max(120, min(210, roughness_pixels[x, y] + int(7 * math.sin(x * 0.017 + y * 0.011))))

TEXTURES.mkdir(parents=True, exist_ok=True)
colour.save(COLOUR_ALPHA)
normal.save(NORMAL)
roughness.save(ROUGHNESS)
report = {
    "outputs": {"colourAlpha": str(COLOUR_ALPHA), "normal": str(NORMAL), "roughness": str(ROUGHNESS)},
    "size": [SIZE, SIZE],
    "slots": 4,
    "slotSpecs": slot_specs,
    "seed": SEED,
    "ownership": "deterministic Aevrynd procedural maps; no external source pixels",
    "intent": "dense clump coverage matched to runtime cards, with separated tips and tangent-direction surface response",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R544_DENSE_CLUMP_ATLAS=" + json.dumps(report, sort_keys=True))
