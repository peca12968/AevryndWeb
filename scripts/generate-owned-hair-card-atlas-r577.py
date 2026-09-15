from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets-source/aevrynd-character/textures/aevrynd-r577-independent-lock-atlas.png"
SIZE = 1024
SLOTS = 4
SCALE = 2


def make_slot(slot: int) -> Image.Image:
    width = SIZE // SLOTS
    canvas = Image.new("RGBA", (width * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    soft = Image.new("L", canvas.size, 0)
    soft_draw = ImageDraw.Draw(soft)
    rng = random.Random(57700 + slot)
    strand_count = (28, 34, 31, 37)[slot]
    centre = width * SCALE * (0.48 + (slot - 1.5) * 0.012)

    paths = []
    for strand in range(strand_count):
        root_rank = (strand + 0.5) / strand_count - 0.5
        root_x = centre + root_rank * width * SCALE * 0.34 + rng.uniform(-3, 3) * SCALE
        tip_x = centre + root_rank * width * SCALE * (0.76 + 0.08 * slot)
        tip_x += rng.uniform(-15, 15) * SCALE
        tip_y = rng.uniform(18, 170) * SCALE
        phase = rng.uniform(0, math.tau)
        wave = rng.uniform(2.5, 7.0) * SCALE
        points = []
        samples = 72
        for sample in range(samples):
            t = sample / (samples - 1)
            y = (SIZE * SCALE - 8 * SCALE) * (1.0 - t) + tip_y * t
            fan = t * t * (3.0 - 2.0 * t)
            x = root_x * (1.0 - fan) + tip_x * fan
            x += math.sin(phase + t * math.pi * (1.25 + 0.12 * slot)) * wave * math.sin(math.pi * t)
            points.append((x, y))
        paths.append(points)

    for points in paths:
        soft_draw.line(points, fill=52, width=5 * SCALE, joint="curve")
    soft = soft.filter(ImageFilter.GaussianBlur(2.2 * SCALE))
    warmth = Image.new("RGBA", canvas.size, (92, 42, 24, 0))
    warmth.putalpha(soft)
    canvas = Image.alpha_composite(canvas, warmth)

    draw = ImageDraw.Draw(canvas)
    colours = ((126, 66, 40), (111, 50, 29), (143, 77, 47), (101, 43, 25))
    for index, points in enumerate(paths):
        alpha = 118 + (index * 37 + slot * 19) % 86
        colour = colours[(index + slot) % len(colours)] + (alpha,)
        draw.line(points, fill=colour, width=(1 if index % 4 else 2) * SCALE, joint="curve")
    return canvas.resize((width, SIZE), Image.Resampling.LANCZOS)


atlas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
for slot in range(SLOTS):
    atlas.alpha_composite(make_slot(slot), (slot * (SIZE // SLOTS), 0))
OUT.parent.mkdir(parents=True, exist_ok=True)
atlas.save(OUT, optimize=True)
print(OUT)
