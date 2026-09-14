import json
import math
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets-source/aevrynd-character/textures/aevrynd-female-lip-normal-v1.png"
SIZE = 1024
SEED = 488

axis = (np.arange(SIZE, dtype=np.float32) + 0.5) / SIZE
uu, vv = np.meshgrid(axis, axis)
rng = np.random.default_rng(SEED)
noise = rng.standard_normal((SIZE, SIZE), dtype=np.float32)
for _ in range(34):
    noise = (
        noise
        + np.roll(noise, 1, 0)
        + np.roll(noise, -1, 0)
        + np.roll(noise, 1, 1)
        + np.roll(noise, -1, 1)
    ) / 5
noise = (noise - noise.min()) / (noise.max() - noise.min()) - 0.5

# Narrow, mostly vertical grooves with a mild fan toward the corners. A second
# finer family breaks repetition without turning the surface into random noise.
coordinate = (
    uu
    + 0.20 * (uu - 0.5) * (vv - 0.5)
    + 0.008 * np.sin(2 * math.pi * (2.1 * vv + 0.17))
    + 0.010 * noise
)
major_phase = 2 * math.pi * (18.0 * coordinate)
minor_phase = 2 * math.pi * (33.0 * coordinate + 0.21 * np.sin(2 * math.pi * vv))
major_grooves = -np.maximum(np.cos(major_phase), 0.0) ** 5
minor_grooves = -np.maximum(np.cos(minor_phase), 0.0) ** 4
amplitude = 0.82 + 0.12 * np.sin(2 * math.pi * (3.1 * uu + 1.3 * vv)) + 0.08 * noise
height = amplitude * (major_grooves + 0.22 * minor_grooves)
gradient_x = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
gradient_y = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
normal_x = -gradient_x * 2.10
normal_y = -gradient_y * 1.00
normal_z = np.ones_like(normal_x)
length = np.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z)
rgb = np.stack(
    (
        normal_x / length * 0.5 + 0.5,
        normal_y / length * 0.5 + 0.5,
        normal_z / length * 0.5 + 0.5,
    ),
    axis=-1,
)
rgb = np.round(np.clip(rgb, 0, 1) * 255) / 255
rgba = np.concatenate((rgb, np.ones((SIZE, SIZE, 1), dtype=np.float32)), axis=-1)

OUT.parent.mkdir(parents=True, exist_ok=True)
image = bpy.data.images.new(
    "aevrynd-female-lip-normal-v1",
    width=SIZE,
    height=SIZE,
    alpha=False,
    float_buffer=False,
)
image.colorspace_settings.name = "Non-Color"
image.pixels.foreach_set(rgba.reshape(-1))
image.filepath_raw = str(OUT)
image.file_format = "PNG"
image.save()

report = {
    "asset": str(OUT),
    "resolution": [SIZE, SIZE],
    "seed": SEED,
    "fieldCoveragePercent": 100.0,
    "normalMin": [float(value) for value in rgb.min((0, 1))],
    "normalMax": [float(value) for value in rgb.max((0, 1))],
    "normalMean": [float(value) for value in rgb.mean((0, 1))],
    "maskContract": "actual upper/lower vermilion POINT color attributes in skin shader",
    "bytes": OUT.stat().st_size,
    "license": "Aevrynd-owned deterministic procedural generation; no external texture input",
}
print("AEVRYND_LIP_NORMAL_V1=" + json.dumps(report, sort_keys=True))
