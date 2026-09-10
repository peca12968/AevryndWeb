import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-philtrum-r80.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eye-aperture-r83-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
VARIANTS = (
    ("a-control", 0.0, 0.0),
    ("b-restrained", 0.00045, 0.00035),
    ("c-balanced", 0.00075, 0.00055),
    ("d-strong", 0.00105, 0.00075),
)


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


def sculpt_aperture(body, upper_amount, lower_amount):
    key = body.shape_key_add(name=f"Aevrynd_EyeAperture_R83_{upper_amount * 1000:.2f}", from_mix=False)
    moved = 0
    maximum = 0.0
    upper_vertices = lower_vertices = 0
    for index, basis_point in enumerate(body.data.vertices):
        point = basis_point.co
        best_delta = 0.0
        for side, (cx, _cy, cz) in EYES.items():
            lateral = 1.0 if side == "L" else -1.0
            u = (point.x - cx) / 0.01045
            if abs(u) >= 0.98 or not (-0.136 < point.y < -0.100):
                continue
            arc = math.sqrt(max(0.0, 1.0 - u * u))
            tilt = lateral * 0.023 * (point.x - cx)
            front = gaussian(point.y, -0.118, 0.0105)
            end_guard = smoothstep(0.98, 0.78, abs(u))
            upper_edge = cz + 0.00382 * arc + tilt
            lower_edge = cz - 0.00282 * arc + tilt
            upper_weight = gaussian(point.z, upper_edge, 0.00145) * front * end_guard
            lower_weight = gaussian(point.z, lower_edge, 0.00135) * front * end_guard
            delta = upper_amount * arc * upper_weight - lower_amount * arc * lower_weight
            if abs(delta) > abs(best_delta):
                best_delta = delta
        if abs(best_delta) <= 0.000001:
            continue
        key.data[index].co.z += best_delta
        moved += 1
        maximum = max(maximum, abs(best_delta))
        if best_delta > 0:
            upper_vertices += 1
        else:
            lower_vertices += 1
    key.value = 1.0
    key.slider_min = 0.0
    key.slider_max = 1.0
    return {
        "shape_key": key.name,
        "upper_amount_mm": upper_amount * 1000.0,
        "lower_amount_mm": lower_amount * 1000.0,
        "moved_vertices": moved,
        "upper_vertices": upper_vertices,
        "lower_vertices": lower_vertices,
        "maximum_delta_mm": maximum * 1000.0,
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
    for name, upper, lower in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1200
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj) or "Lashes" in obj.name:
                obj.hide_render = True
        geometry = sculpt_aperture(bpy.data.objects[BODY], upper, lower) if upper else {
            "upper_amount_mm": 0.0, "lower_amount_mm": 0.0,
            "moved_vertices": 0, "maximum_delta_mm": 0.0,
        }
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{name}-01-front", (0.0, -0.48, 1.610), (0.0, -0.065, 1.608), 122)
        render(camera, f"{name}-02-three-quarter", (0.38, -0.52, 1.625), (0.0, -0.025, 1.608), 108)
        report[name] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_EYE_APERTURE_R83_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
