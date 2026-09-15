import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
OUT = ASSETS / "textures/aevrynd-owned-hair-atlas-r543.png"
REPORT = ASSETS / "female-v249-mainline-owned-hair-atlas-r543.build.json"
SIZE = 1024
SLOT = SIZE // 4
random.seed(249543)

image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(image, "RGBA")
slot_specs = (
    (54, 0.72, 2.2),
    (42, 0.64, 3.4),
    (32, 0.56, 4.8),
    (24, 0.48, 6.2),
)
for slot_index, (fibres, base_alpha, wave_px) in enumerate(slot_specs):
    left = slot_index * SLOT
    for fibre in range(fibres):
        root_x = left + 8 + (SLOT - 16) * (fibre + 0.5) / fibres
        root_x += random.uniform(-2.4, 2.4)
        phase = random.random() * math.tau
        frequency = random.uniform(0.72, 1.22)
        lean = random.uniform(-11.0, 11.0)
        tip_release = random.uniform(-8.0, 8.0)
        alpha = int(255 * base_alpha * random.uniform(0.78, 1.0))
        colour = (
            int(random.uniform(92, 120)),
            int(random.uniform(48, 67)),
            int(random.uniform(31, 46)),
            alpha,
        )
        points = []
        segments = 40
        for segment in range(segments + 1):
            t = segment / segments
            y = SIZE - 1 - t * (SIZE - 2)
            wave = math.sin(phase + t * math.tau * frequency) * wave_px * (math.sin(math.pi * t) ** 1.2)
            x = root_x + lean * t + wave + tip_release * max(0.0, (t - 0.70) / 0.30) ** 2
            points.append((x, y))
        draw.line(points, fill=colour, width=2 if fibre % 7 == 0 else 1)
    # A restrained warm highlight breaks a flat single-value card mass.
    for highlight in range(max(3, fibres // 8)):
        x = left + SLOT * (0.24 + 0.52 * random.random())
        draw.line([(x, SIZE - 1), (x + random.uniform(-5, 5), 4)], fill=(154, 93, 62, 74), width=1)

# Only the colour/alpha transition is softened; geometry controls the silhouette.
blurred = image.filter(ImageFilter.GaussianBlur(radius=0.32))
OUT.parent.mkdir(parents=True, exist_ok=True)
blurred.save(OUT)
report = {
    "output": str(OUT),
    "size": [SIZE, SIZE],
    "slots": 4,
    "fibresPerSlot": [spec[0] for spec in slot_specs],
    "seed": 249543,
    "ownership": "deterministic Aevrynd procedural texture; no external source pixels",
    "channels": "sRGB brown colour plus authored alpha",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R543_ATLAS=" + json.dumps(report, sort_keys=True))
