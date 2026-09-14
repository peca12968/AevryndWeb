from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / "assets-source/aevrynd-character/textures"
SOURCE = TEXTURES / "aevrynd-sclera-basecolor-v61.png"
VARIANTS = {
    "b-soft-warm": np.array([190.0, 180.0, 168.0], dtype=np.float32),
    "c-natural-warm": np.array([178.0, 168.0, 156.0], dtype=np.float32),
    "d-muted-warm": np.array([166.0, 157.0, 146.0], dtype=np.float32),
}


source = np.asarray(Image.open(SOURCE).convert("RGB"), dtype=np.float32)
height, width, _channels = source.shape
source_mean = source.mean(axis=(0, 1), keepdims=True)
deviation = (source - source_mean) * 0.82
x = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :, None]
y = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None, None]
edge = np.clip((np.abs(x) - 0.35) / 0.65, 0.0, 1.0) ** 1.6
low_frequency = (np.sin(x * 8.3 + y * 3.1) + np.sin(x * 3.7 - y * 6.2)) * 0.65
warm_edge = edge * np.array([4.0, -1.5, -3.0], dtype=np.float32)

for label, target_mean in VARIANTS.items():
    image = target_mean[None, None, :] + deviation + warm_edge + low_frequency
    image = np.clip(np.rint(image), 0, 255).astype(np.uint8)
    path = TEXTURES / f"aevrynd-sclera-basecolor-v496-{label}.png"
    Image.fromarray(image, mode="RGB").save(path, optimize=True)
    print(f"{label}: path={path} mean={image.mean(axis=(0, 1)).tolist()}")
