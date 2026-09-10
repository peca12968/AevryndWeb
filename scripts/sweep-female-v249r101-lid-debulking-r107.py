import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-lid-debulking-r107-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
VARIANTS = (("a-control", 0.0), ("b-restrained", 0.68), ("c-balanced", 1.0), ("d-strong", 1.34))


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


def mixed_coordinate(keys, index):
    basis = keys[0].data[index].co.copy()
    result = basis.copy()
    for key in keys[1:]:
        if key.value:
            result += (key.data[index].co - key.relative_key.data[index].co) * key.value
    return result


def sculpt(body, strength):
    keys = body.data.shape_keys.key_blocks
    current = [mixed_coordinate(keys, index) for index in range(len(body.data.vertices))]
    key = body.shape_key_add(name=f"Aevrynd_LidDebulking_R107_{strength:.2f}", from_mix=False)
    moved = 0
    maximum = 0.0
    projected = recessed = 0
    for index, point in enumerate(current):
        best = 0.0
        for side, (cx, _cy, cz) in EYES.items():
            lateral = 1.0 if side == "L" else -1.0
            u = (point.x - cx) / 0.01045
            if abs(u) >= 1.24 or not (-0.136 < point.y < -0.098):
                continue
            cu = max(-1.0, min(1.0, u))
            arc = math.sqrt(max(0.0, 1.0 - cu * cu))
            tilt = lateral * 0.023 * (point.x - cx)
            upper = cz + 0.00382 * arc + tilt
            lower = cz - 0.00282 * arc + tilt
            front = gaussian(point.y, -0.118, 0.0100)
            end_guard = smoothstep(1.18, 0.82, abs(u))

            # Recess the swollen plate, then recover only the thin free margin.
            upper_plate = gaussian(point.z, upper + 0.00225 * (0.62 + 0.38 * arc), 0.00150)
            upper_crease = gaussian(point.z, upper + 0.00445 * (0.58 + 0.42 * arc), 0.00078)
            upper_margin = gaussian(point.z, upper + 0.00040, 0.00055)
            lower_bulk = gaussian(point.z, lower - 0.00255 * (0.70 + 0.30 * arc), 0.00175)
            lower_margin = gaussian(point.z, lower - 0.00045, 0.00062)
            subtle_trough = gaussian(point.z, lower - 0.0064, 0.00150)
            medial = gaussian(u, -0.28, 0.62)

            delta = strength * front * end_guard * (
                0.00048 * upper_plate
                + 0.00072 * upper_crease
                - 0.00018 * upper_margin
                + 0.00038 * lower_bulk
                - 0.00016 * lower_margin
                + 0.00022 * subtle_trough * (0.72 + 0.28 * medial)
            )
            if abs(delta) > abs(best):
                best = delta
        if abs(best) <= 0.000001:
            continue
        key.data[index].co.y += best
        moved += 1
        maximum = max(maximum, abs(best))
        if best < 0.0:
            projected += 1
        else:
            recessed += 1

    key.value = 1.0
    key.slider_min = 0.0
    key.slider_max = 1.0
    body.data.update()
    return {
        "shape_key": key.name,
        "strength": strength,
        "vertices_moved": moved,
        "maximum_displacement_mm": maximum * 1000.0,
        "projected_vertices": projected,
        "recessed_vertices": recessed,
    }


def render(camera, name, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for label, strength in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        geometry = sculpt(bpy.data.objects[BODY], strength) if strength else {
            "strength": 0.0, "vertices_moved": 0, "maximum_displacement_mm": 0.0,
        }
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-eyes-front", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
        render(camera, f"{label}-02-left-eye-three-quarter", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
        render(camera, f"{label}-03-face-front", (0.0, -0.555, 1.605), (0.0, -0.058, 1.604), 116, (1050, 1050))
        report[label] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R101_LID_DEBULKING_R107=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
