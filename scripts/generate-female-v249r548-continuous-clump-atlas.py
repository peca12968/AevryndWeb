import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEXTURES = ASSETS / "textures"
COLOUR_ALPHA = TEXTURES / "aevrynd-owned-hair-continuous-clump-colour-alpha-r548.png"
NORMAL = TEXTURES / "aevrynd-owned-hair-continuous-clump-normal-r548.png"
ROUGHNESS = TEXTURES / "aevrynd-owned-hair-continuous-clump-roughness-r548.png"
REPORT = ASSETS / "female-v249-mainline-continuous-clump-atlas-r548.build.json"
SIZE = 1024
SLOT = SIZE // 4
SEED = 249548
random.seed(SEED)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


alpha = Image.new("L", (SIZE, SIZE), 0)
normal = Image.new("RGB", (SIZE, SIZE), (128, 128, 255))
roughness = Image.new("L", (SIZE, SIZE), 178)
ad = ImageDraw.Draw(alpha)
nd = ImageDraw.Draw(normal)
rd = ImageDraw.Draw(roughness)

slot_specs = (
    {"width": 0.82, "lean": -0.10, "wave": 0.035, "forks": 5},
    {"width": 0.72, "lean": 0.08, "wave": 0.050, "forks": 4},
    {"width": 0.62, "lean": -0.05, "wave": 0.070, "forks": 4},
    {"width": 0.52, "lean": 0.13, "wave": 0.085, "forks": 3},
)

for slot_index, spec in enumerate(slot_specs):
    left = slot_index * SLOT
    center = left + SLOT * 0.5
    phase = random.uniform(0.0, math.tau)
    ys = list(range(SIZE - 2, 4, -5))
    centres = []
    widths = []
    for y in ys:
        t = (SIZE - 2 - y) / (SIZE - 7)
        sway = math.sin(phase + t * math.pi * 1.35) * SLOT * spec["wave"] * math.sin(math.pi * t)
        centre_x = center + SLOT * spec["lean"] * t + sway
        root_open = 0.70 + 0.30 * clamp(t / 0.10)
        tip_close = (1.0 - clamp((t - 0.67) / 0.33)) ** 0.62
        irregular = 1.0 + 0.055 * math.sin(t * 31.0 + phase) + 0.035 * math.sin(t * 67.0 + phase * 0.6)
        half = SLOT * spec["width"] * 0.5 * root_open * tip_close * irregular
        centres.append(centre_x)
        widths.append(max(1.2, half))
    polygon = [(c - w, y) for c, w, y in zip(centres, widths, ys)]
    polygon += [(c + w, y) for c, w, y in reversed(list(zip(centres, widths, ys)))]
    ad.polygon(polygon, fill=225 - slot_index * 5)

    # Carve short internal separations that begin inside the clump and open only
    # near the tip. This preserves a continuous opaque core instead of creating
    # the full-length parallel strokes that produced the r544 fishbone pattern.
    for fork in range(spec["forks"]):
        start_t = random.uniform(0.44, 0.72)
        side = -1 if fork % 2 == 0 else 1
        points = []
        for step in range(22):
            t = start_t + (1.0 - start_t) * step / 21.0
            idx = min(len(centres) - 1, round(t * (len(centres) - 1)))
            y = ys[idx]
            opening = ((t - start_t) / (1.0 - start_t)) ** 1.45
            x = centres[idx] + side * widths[idx] * (0.18 + 0.76 * opening)
            x += math.sin(step * 0.72 + fork) * (0.8 + opening * 1.8)
            points.append((x, y))
        ad.line(points, fill=0, width=2 + (fork % 2))

    # Fine detail is confined to the boundary and final third; the centre stays
    # visually solid at game distance while the silhouette retains loose tips.
    for strand in range(34 - slot_index * 4):
        side = -1 if strand % 2 == 0 else 1
        offset = random.uniform(0.72, 1.02)
        start_t = random.uniform(0.08, 0.52)
        end_t = random.uniform(0.78, 1.0)
        points = []
        for step in range(18):
            t = start_t + (end_t - start_t) * step / 17.0
            idx = min(len(centres) - 1, round(t * (len(centres) - 1)))
            x = centres[idx] + side * widths[idx] * offset
            x += math.sin(step * 0.63 + strand) * 1.4
            points.append((x, ys[idx]))
        ad.line(points, fill=random.randint(105, 185), width=random.choice((1, 2)))

    # Tangent response follows the same curved clump axis.
    for idx in range(len(centres) - 1):
        dx = centres[idx + 1] - centres[idx]
        dy = ys[idx + 1] - ys[idx]
        tangent_x = clamp(dx / max(1.0, abs(dy)), -0.35, 0.35)
        nx = int(128 + tangent_x * 90)
        x0, x1 = centres[idx] - widths[idx], centres[idx] + widths[idx]
        nd.line((x0, ys[idx], x1, ys[idx]), fill=(nx, 128, 255), width=6)
        rd.line((x0, ys[idx], x1, ys[idx]), fill=154 + ((idx + slot_index * 7) % 25), width=6)

alpha = alpha.filter(ImageFilter.GaussianBlur(0.55))
normal = normal.filter(ImageFilter.GaussianBlur(1.2))
roughness = roughness.filter(ImageFilter.GaussianBlur(1.0))

colour = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
cp = colour.load()
ap = alpha.load()
rp = roughness.load()
for y in range(SIZE):
    t = (SIZE - 1 - y) / (SIZE - 1)
    for x in range(SIZE):
        slot_index = min(3, x // SLOT)
        variation = 4.5 * math.sin(x * 0.021 + y * 0.004 + slot_index * 1.4)
        root_dark = -9.0 * (1.0 - t) ** 2
        tip_light = 4.0 * t
        cp[x, y] = (
            int(clamp(91 + variation + root_dark + tip_light, 0, 255)),
            int(clamp(48 + variation * 0.46 + root_dark * 0.45 + tip_light * 0.5, 0, 255)),
            int(clamp(32 + variation * 0.28 + root_dark * 0.28 + tip_light * 0.35, 0, 255)),
            ap[x, y],
        )
        rp[x, y] = int(clamp(rp[x, y] + 4 * math.sin(x * 0.015 + y * 0.009), 120, 210))

TEXTURES.mkdir(parents=True, exist_ok=True)
colour.save(COLOUR_ALPHA)
normal.save(NORMAL)
roughness.save(ROUGHNESS)
histogram = alpha.histogram()
opaque_pixels = sum(histogram[9:])
report = {
    "outputs": {"colourAlpha": str(COLOUR_ALPHA), "normal": str(NORMAL), "roughness": str(ROUGHNESS)},
    "size": [SIZE, SIZE],
    "slots": 4,
    "slotSpecs": slot_specs,
    "seed": SEED,
    "alphaCoverageAbove8Percent": opaque_pixels * 100.0 / (SIZE * SIZE),
    "ownership": "deterministic Aevrynd procedural maps; no external source pixels",
    "intent": "continuous irregular clump cores with internal breakup, boundary fibres and separated tapered tips",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R548_CONTINUOUS_CLUMP_ATLAS=" + json.dumps(report, sort_keys=True))
