import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-philtrum-r81-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-restrained", 0.45), ("c-balanced", 0.70), ("d-full", 0.90))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def features(x, z):
    dz = z - 1.544
    return [1.0, x, dz, x * x, dz * dz, x * dz]


def reconstruct(body, blend):
    training = []
    targets = []
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        ax = abs(x)
        if 0.014 < ax < 0.030 and 1.534 < z < 1.555 and -0.160 < y < -0.105:
            training.append(features(x, z))
            targets.append(y)
    matrix = np.asarray(training, dtype=np.float64)
    values = np.asarray(targets, dtype=np.float64)
    coefficients, residuals, _rank, _singular = np.linalg.lstsq(matrix, values, rcond=None)
    moved = 0
    maximum = 0.0
    mean = 0.0
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        ax = abs(x)
        if ax >= 0.023 or not (1.533 < z < 1.556) or not (-0.160 < y < -0.105):
            continue
        wx = smoothstep(0.023, 0.014, ax)
        wz = smoothstep(1.533, 1.539, z) * smoothstep(1.556, 1.549, z)
        weight = wx * wz * blend
        if weight <= 0.0:
            continue
        baseline = float(np.dot(coefficients, np.asarray(features(x, z))))
        vertical = gaussian(z, 1.544, 0.0075)
        central_groove = 0.00032 * gaussian(x, 0.0, 0.0032) * vertical
        columns = -0.00018 * gaussian(ax, 0.0062, 0.0024) * vertical
        target_y = baseline + central_groove + columns
        delta = (target_y - y) * weight
        if abs(delta) <= 0.000001:
            continue
        vertex.co.y += delta
        moved += 1
        maximum = max(maximum, abs(delta))
        mean += abs(delta)
    body.data.update()
    return {
        "training_vertices": len(training),
        "moved_vertices": moved,
        "blend": blend,
        "maximum_delta_mm": maximum * 1000.0,
        "mean_delta_mm": (mean / moved if moved else 0.0) * 1000.0,
        "fit_residual_sum": float(residuals[0]) if len(residuals) else 0.0,
        "coefficients": coefficients.tolist(),
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, blend in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1100
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        geometry = reconstruct(bpy.data.objects[BODY], blend)
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{name}-01-front", (0.0, -0.50, 1.555), (0.0, -0.070, 1.545), 118)
        render(camera, f"{name}-02-three-quarter", (0.32, -0.50, 1.58), (0.0, -0.035, 1.550), 110)
        render(camera, f"{name}-03-profile", (0.62, -0.03, 1.57), (0.0, -0.010, 1.545), 100)
        report[name] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_PHILTRUM_R81_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
