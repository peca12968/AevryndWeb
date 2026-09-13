import json
import math
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets-source/aevrynd-character/textures/aevrynd-iris-hazel-v5.png"
RNG = np.random.default_rng(236051)


def smoothstep(value):
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def texture(size=512):
    axis = (np.arange(size, dtype=np.float32) + 0.5) / size * 2.0 - 1.0
    x, y = np.meshgrid(axis, axis)
    radius = np.sqrt(x * x + y * y)
    angle = np.arctan2(y, x)

    broad = np.zeros_like(radius)
    fine = np.zeros_like(radius)
    for frequency, amplitude, phase, drift in (
        (37.0, 0.25, 0.5, 7.0),
        (71.0, 0.18, 2.0, -13.0),
        (127.0, 0.11, -0.8, 21.0),
    ):
        broad += amplitude * np.sin(angle * frequency + radius * drift + phase)
    for frequency, amplitude, phase, drift in (
        (181.0, 0.055, 1.1, -29.0),
        (263.0, 0.035, -1.9, 41.0),
    ):
        fine += amplitude * np.sin(angle * frequency + radius * drift + phase)

    grain = RNG.normal(0.0, 1.0, (size, size)).astype(np.float32)
    grain = (grain + np.roll(grain, 1, 0) + np.roll(grain, -1, 0) + np.roll(grain, 1, 1) + np.roll(grain, -1, 1)) / 5.0

    mix = smoothstep((radius - 0.30) / 0.58)
    inner = np.array((0.235, 0.112, 0.045), dtype=np.float32)
    outer = np.array((0.105, 0.145, 0.082), dtype=np.float32)
    color = inner[None, None, :] * (1.0 - mix[..., None]) + outer[None, None, :] * mix[..., None]

    fiber_gate = smoothstep((radius - 0.24) / 0.14) * (1.0 - smoothstep((radius - 0.86) / 0.10))
    modulation = 1.0 + fiber_gate * (0.23 * np.tanh(broad) + 0.075 * fine + 0.035 * grain)
    color *= modulation[..., None]

    # Dark, interrupted collarette structure. It never forms a bright closed ring.
    edge = 0.43 + 0.030 * np.sin(angle * 7.0 + 0.2) + 0.015 * np.sin(angle * 19.0 - 1.4)
    collarette = np.exp(-0.5 * ((radius - edge) / 0.027) ** 2)
    breaks = smoothstep((np.sin(angle * 5.0 + 0.8) + 0.35 * np.sin(angle * 13.0 - 0.6) + 0.20) / 0.75)
    color *= (1.0 - 0.14 * collarette * breaks)[..., None]

    # Sparse crypts break radial regularity without reading as painted dots.
    for _ in range(30):
        theta = RNG.uniform(-math.pi, math.pi)
        cr = RNG.uniform(0.34, 0.69)
        cx, cy = math.cos(theta) * cr, math.sin(theta) * cr
        tangent = -math.sin(theta) * (x - cx) + math.cos(theta) * (y - cy)
        normal = math.cos(theta) * (x - cx) + math.sin(theta) * (y - cy)
        crypt = np.exp(-0.5 * ((tangent / RNG.uniform(0.010, 0.022)) ** 2 + (normal / RNG.uniform(0.018, 0.045)) ** 2))
        color *= (1.0 - RNG.uniform(0.05, 0.11) * crypt[..., None])

    furrow_gate = smoothstep((radius - 0.67) / 0.08) * (1.0 - smoothstep((radius - 0.91) / 0.06))
    broken_furrow = (0.5 + 0.5 * np.sin(radius * 82.0 + 1.3 * np.sin(angle * 6.0)))
    broken_furrow *= smoothstep((np.sin(angle * 9.0 - 0.4) + 0.45) / 0.8)
    color *= (1.0 - 0.045 * broken_furrow * furrow_gate)[..., None]

    limbus_edge = 0.875 + 0.008 * np.sin(angle * 11.0 + 0.7)
    limbus = smoothstep((radius - limbus_edge) / 0.11)
    color *= (1.0 - 0.57 * limbus[..., None])

    pupil_edge = 0.224 + 0.006 * np.sin(angle * 8.0 + 0.3) + 0.003 * np.sin(angle * 17.0 - 0.5)
    pupil = smoothstep((radius - pupil_edge) / 0.018)
    pupil_color = np.array((0.0035, 0.0024, 0.0018), dtype=np.float32)
    color = pupil_color[None, None, :] * (1.0 - pupil[..., None]) + color * pupil[..., None]

    alpha = 1.0 - smoothstep((radius - 0.992) / 0.012)
    rgba = np.concatenate((np.clip(color, 0.0, 1.0), alpha[..., None]), axis=-1).astype(np.float32)
    rgba[radius > 1.004, :3] = 0.0
    return rgba


OUTPUT.parent.mkdir(parents=True, exist_ok=True)
pixels = texture()
height, width, _ = pixels.shape
image = bpy.data.images.new("Aevrynd Iris Hazel V5", width=width, height=height, alpha=True)
image.colorspace_settings.name = "sRGB"
image.pixels.foreach_set(np.ascontiguousarray(pixels).ravel())
image.filepath_raw = str(OUTPUT)
image.file_format = "PNG"
image.save()
print("AEVRYND_OWNED_IRIS_V5=" + json.dumps({"path": str(OUTPUT), "size": [width, height], "seed": 236051}))
