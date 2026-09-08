import json
import math
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TEXTURE_DIR = ROOT / "assets-source" / "aevrynd-character" / "textures"
IRIS_PATH = TEXTURE_DIR / "aevrynd-iris-hazel-v61.png"
SCLERA_PATH = TEXTURE_DIR / "aevrynd-sclera-basecolor-v61.png"
RNG = np.random.default_rng(61091)


def save_rgba(name, pixels, path):
    height, width, channels = pixels.shape
    assert channels == 4
    image = bpy.data.images.get(name) or bpy.data.images.new(name, width=width, height=height, alpha=True)
    if image.size[0] != width or image.size[1] != height:
        image.scale(width, height)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(np.ascontiguousarray(pixels, dtype=np.float32).ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def iris_texture(size=512):
    axis = (np.arange(size, dtype=np.float32) + 0.5) / size * 2.0 - 1.0
    x, y = np.meshgrid(axis, axis)
    radius = np.sqrt(x * x + y * y)
    angle = np.arctan2(y, x)
    radial = np.clip(radius, 0.0, 1.0)

    # Layer several nonuniform angular frequencies so the fibers fork and
    # interrupt rather than forming a single procedural starburst.
    warp = 0.14 * np.sin(angle * 3.0 + radial * 8.0) + 0.07 * np.sin(angle * 7.0 - radial * 13.0)
    fiber = np.zeros_like(radius)
    for frequency, amplitude, phase, drift in (
        (83.0, 0.42, 0.3, 19.0),
        (137.0, 0.27, 1.7, -31.0),
        (211.0, 0.18, -0.8, 47.0),
        (317.0, 0.10, 2.1, -71.0),
    ):
        fiber += amplitude * np.sin(angle * frequency + radial * drift + phase + warp)
    fiber = 0.5 + 0.5 * np.tanh(fiber * 1.45)

    granular = RNG.normal(0.0, 1.0, (size, size)).astype(np.float32)
    granular = (granular + np.roll(granular, 1, 0) + np.roll(granular, 1, 1)) / 3.0
    collarette_edge = 0.43 + 0.032 * np.sin(angle * 11.0 + 0.6) + 0.018 * np.sin(angle * 23.0 - 1.2)
    collarette = np.exp(-0.5 * ((radial - collarette_edge) / 0.050) ** 2)
    inner = np.exp(-0.5 * ((radial - 0.27) / 0.16) ** 2)
    outer_green = np.clip((radial - 0.50) / 0.45, 0.0, 1.0)
    limbus = np.clip((radial - 0.84) / 0.14, 0.0, 1.0) ** 1.7

    color = np.empty((size, size, 3), dtype=np.float32)
    warm = np.stack((0.105 + 0.135 * fiber, 0.033 + 0.078 * fiber, 0.009 + 0.024 * fiber), axis=-1)
    green = np.stack((0.060 + 0.035 * fiber, 0.075 + 0.060 * fiber, 0.025 + 0.018 * fiber), axis=-1)
    color[:] = warm * (1.0 - outer_green[..., None]) + green * outer_green[..., None]
    color += collarette[..., None] * np.array((0.20, 0.095, 0.018), dtype=np.float32)
    color += inner[..., None] * np.array((0.030, 0.010, 0.002), dtype=np.float32)
    color += (granular * 0.014)[..., None]

    # Irregular crypts around the collarette give medium-scale iris anatomy.
    for index in range(34):
        theta = RNG.uniform(-math.pi, math.pi)
        center_r = RNG.uniform(0.38, 0.62)
        center_x, center_y = math.cos(theta) * center_r, math.sin(theta) * center_r
        tangent = -math.sin(theta) * (x - center_x) + math.cos(theta) * (y - center_y)
        normal = math.cos(theta) * (x - center_x) + math.sin(theta) * (y - center_y)
        crypt = np.exp(-0.5 * ((tangent / RNG.uniform(0.012, 0.028)) ** 2 + (normal / RNG.uniform(0.025, 0.055)) ** 2))
        color -= crypt[..., None] * np.array((0.035, 0.020, 0.007), dtype=np.float32)

    color *= (1.0 - 0.72 * limbus[..., None])
    pupil_falloff = smooth = np.clip((radial - 0.235) / 0.030, 0.0, 1.0)
    smooth = smooth * smooth * (3.0 - 2.0 * smooth)
    color *= (0.10 + 0.90 * smooth[..., None])
    alpha = (radius <= 0.995).astype(np.float32)
    rgba = np.concatenate((np.clip(color, 0.0, 1.0), alpha[..., None]), axis=-1)
    rgba[radius > 0.995, :3] = 0.0
    return rgba


def add_vessel(canvas, xs, ys, color, opacity, width):
    height, width_px, _ = canvas.shape
    for index in range(len(xs) - 1):
        x0, x1 = xs[index] * (width_px - 1), xs[index + 1] * (width_px - 1)
        y0, y1 = ys[index] * (height - 1), ys[index + 1] * (height - 1)
        radius = max(1.0, width * width_px * 3.0)
        xmin = max(0, int(min(x0, x1) - radius))
        xmax = min(width_px, int(max(x0, x1) + radius + 1))
        ymin = max(0, int(min(y0, y1) - radius))
        ymax = min(height, int(max(y0, y1) + radius + 1))
        yy, xx = np.mgrid[ymin:ymax, xmin:xmax]
        dx, dy = x1 - x0, y1 - y0
        denom = max(dx * dx + dy * dy, 1e-8)
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / denom, 0.0, 1.0)
        distance = np.sqrt((xx - (x0 + t * dx)) ** 2 + (yy - (y0 + t * dy)) ** 2)
        mask = np.exp(-0.5 * (distance / max(0.45, width * width_px)) ** 2) * opacity
        region = canvas[ymin:ymax, xmin:xmax]
        region[:] = region * (1.0 - mask[..., None]) + color * mask[..., None]


def sclera_texture(width=512, height=256):
    u = (np.arange(width, dtype=np.float32) + 0.5) / width
    v = (np.arange(height, dtype=np.float32) + 0.5) / height
    uu, vv = np.meshgrid(u, v)
    fine = RNG.normal(0.0, 1.0, (height, width)).astype(np.float32)
    fine = (fine + np.roll(fine, 1, 0) + np.roll(fine, 1, 1) + np.roll(fine, -1, 0)) / 4.0
    corner = np.exp(-0.5 * (np.minimum(uu, 1.0 - uu) / 0.17) ** 2)
    vertical = 0.70 + 0.30 * np.cos((vv - 0.5) * math.pi)

    base = np.empty((height, width, 3), dtype=np.float32)
    base[:] = np.array((0.79, 0.755, 0.69), dtype=np.float32)
    base += fine[..., None] * np.array((0.010, 0.008, 0.006), dtype=np.float32)
    base += (corner * vertical)[..., None] * np.array((0.010, -0.014, -0.020), dtype=np.float32)

    vessel_color = np.array((0.57, 0.20, 0.17), dtype=np.float32)
    for edge in (0.0, 1.0):
        direction = 1.0 if edge == 0.0 else -1.0
        for _ in range(15):
            start_y = RNG.uniform(0.08, 0.92)
            length = RNG.uniform(0.10, 0.32)
            count = RNG.integers(5, 9)
            progress = np.linspace(0.0, 1.0, count)
            xs = edge + direction * length * progress
            ys = start_y + np.cumsum(RNG.normal(0.0, 0.012, count)) + 0.018 * np.sin(progress * math.pi * RNG.uniform(1.0, 2.5))
            opacity = RNG.uniform(0.07, 0.16) * (1.0 - 0.45 * progress)
            for index in range(count - 1):
                add_vessel(base, xs[index:index + 2], ys[index:index + 2], vessel_color, float(opacity[index]), RNG.uniform(0.00045, 0.00085))

            if RNG.random() < 0.72:
                branch_at = int(RNG.integers(2, count - 1))
                branch_progress = np.linspace(0.0, 1.0, 4)
                branch_x = xs[branch_at] + direction * RNG.uniform(0.035, 0.085) * branch_progress
                branch_y = ys[branch_at] + RNG.choice((-1.0, 1.0)) * RNG.uniform(0.025, 0.070) * branch_progress
                add_vessel(base, branch_x, branch_y, vessel_color, RNG.uniform(0.045, 0.10), RNG.uniform(0.00035, 0.00060))

    alpha = np.ones((height, width, 1), dtype=np.float32)
    return np.concatenate((np.clip(base, 0.0, 1.0), alpha), axis=-1)


TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
save_rgba("Aevrynd Iris Hazel V61", iris_texture(), IRIS_PATH)
save_rgba("Aevrynd Sclera BaseColor V61", sclera_texture(), SCLERA_PATH)
print("AEVRYND_EYE_TEXTURES_V61=" + json.dumps({
    "iris": str(IRIS_PATH),
    "sclera": str(SCLERA_PATH),
    "generator": "Blender 5.2 NumPy deterministic seed 61091",
}))
