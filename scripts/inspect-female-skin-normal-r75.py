import json
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TEXTURE_DIR = ROOT / "assets-source/aevrynd-character/textures"
OUTPUT = TEXTURE_DIR / "aevrynd-female-skin-normal-v75.validation.json"
FILES = {
    "baseline_v219": TEXTURE_DIR / "aevrynd-female-skin-normal-v219.png",
    "baked_v75": TEXTURE_DIR / "aevrynd-female-skin-normal-v75.png",
}


def load_pixels(path: Path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    rgb = pixels.reshape((-1, 4))[:, :3].copy()
    bpy.data.images.remove(image)
    return width, height, rgb


def inspect(path: Path, width: int, height: int, rgb: np.ndarray) -> dict:
    flat = np.array([0.5, 0.5, 1.0], dtype=np.float32)
    distance = np.linalg.norm(rgb - flat, axis=1)
    active = distance > (1.5 / 255.0)
    strong = distance > (4.0 / 255.0)
    result = {
        "path": str(path),
        "width": int(width),
        "height": int(height),
        "rgb_min": rgb.min(axis=0).round(7).tolist(),
        "rgb_max": rgb.max(axis=0).round(7).tolist(),
        "rgb_mean": rgb.mean(axis=0).round(7).tolist(),
        "rgb_std": rgb.std(axis=0).round(7).tolist(),
        "nonflat_pixels_1_5_over_255": int(active.sum()),
        "nonflat_ratio_1_5_over_255": float(active.mean()),
        "strong_pixels_4_over_255": int(strong.sum()),
        "strong_ratio_4_over_255": float(strong.mean()),
        "mean_flat_distance": float(distance.mean()),
        "p95_flat_distance": float(np.percentile(distance, 95)),
        "p99_flat_distance": float(np.percentile(distance, 99)),
    }
    if active.any():
        active_rgb = rgb[active]
        result["active_rgb_mean"] = active_rgb.mean(axis=0).round(7).tolist()
        result["active_rgb_std"] = active_rgb.std(axis=0).round(7).tolist()
    return result


loaded = {name: load_pixels(path) for name, path in FILES.items()}
report = {
    name: inspect(path, loaded[name][0], loaded[name][1], loaded[name][2])
    for name, path in FILES.items()
}
base = report["baseline_v219"]
baked = report["baked_v75"]
base_rgb = loaded["baseline_v219"][2]
baked_rgb = loaded["baked_v75"][2]
delta = np.abs(baked_rgb - base_rgb)
delta_length = np.linalg.norm(baked_rgb - base_rgb, axis=1)
report["baked_minus_baseline"] = {
    "rgb_abs_mean": delta.mean(axis=0).round(7).tolist(),
    "rgb_abs_max": delta.max(axis=0).round(7).tolist(),
    "mean_vector_distance": float(delta_length.mean()),
    "p95_vector_distance": float(np.percentile(delta_length, 95)),
    "p99_vector_distance": float(np.percentile(delta_length, 99)),
    "changed_pixels_1_over_255": int((delta_length > (1.0 / 255.0)).sum()),
    "changed_ratio_1_over_255": float((delta_length > (1.0 / 255.0)).mean()),
    "changed_pixels_2_over_255": int((delta_length > (2.0 / 255.0)).sum()),
    "changed_ratio_2_over_255": float((delta_length > (2.0 / 255.0)).mean()),
}
report["assessment"] = {
    "bake_has_signal": baked["strong_pixels_4_over_255"] > 1000,
    "bake_signal_exceeds_baseline": (
        baked["mean_flat_distance"] > base["mean_flat_distance"] * 1.02
    ),
    "valid": (
        baked["strong_pixels_4_over_255"] > 1000
        and baked["mean_flat_distance"] > base["mean_flat_distance"] * 1.02
    ),
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SKIN_NORMAL_R75_VALIDATION=" + json.dumps(report, sort_keys=True))
