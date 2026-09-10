import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-baked-r76.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eyelid-r78-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = ((0.034528, -0.10087, 1.607765), (-0.034443, -0.10077, 1.607765))
VARIANTS = (("a-control", 0.0), ("b-restrained", 0.8), ("c-balanced", 1.2), ("d-strong", 1.6))


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


def sculpt(body, strength):
    moved = 0
    maximum = 0.0
    positive = negative = 0
    for vertex in body.data.vertices:
        point = vertex.co
        if not (-0.134 < point.y < -0.094):
            continue
        best = 0.0
        for cx, _cy, cz in EYES:
            dx = (point.x - cx) / 0.0185
            dz = point.z - cz
            if abs(dx) >= 1.08 or not (-0.014 < dz < 0.017):
                continue
            horizontal = smoothstep(1.08, 0.60, abs(dx))
            horizontal *= 0.92 + 0.08 * gaussian(dx, -0.25, 0.40)
            front = gaussian(point.y, -0.114, 0.0105)
            margin_guard = (
                smoothstep(0.0040, 0.0053, dz)
                if dz >= 0.0
                else smoothstep(0.0035, 0.0050, -dz)
            )
            # Narrow crease plus adjacent tarsal fullness. Positive Y recedes
            # into the face; negative Y builds a readable lid roll.
            crease = gaussian(dz, 0.0080, 0.00078)
            upper_roll = gaussian(dz, 0.0047, 0.00105)
            lower_roll = gaussian(dz, -0.0049, 0.00115)
            infra_transition = gaussian(dz, -0.0090, 0.00165)
            delta = strength * horizontal * front * margin_guard * (
                0.00044 * crease
                - 0.00031 * upper_roll
                - 0.00022 * lower_roll
                + 0.00020 * infra_transition
            )
            if abs(delta) > abs(best):
                best = delta
        if abs(best) < 0.000001:
            continue
        point.y += best
        moved += 1
        maximum = max(maximum, abs(best))
        if best > 0:
            positive += 1
        else:
            negative += 1
    body.data.update()
    return {
        "vertices_moved": moved,
        "maximum_displacement_mm": maximum * 1000.0,
        "recessed_vertices": positive,
        "projected_vertices": negative,
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
    for name, strength in VARIANTS:
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
        geometry = sculpt(bpy.data.objects[BODY], strength) if strength else {
            "vertices_moved": 0, "maximum_displacement_mm": 0.0,
            "recessed_vertices": 0, "projected_vertices": 0,
        }
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{name}-01-front", (0.0, -0.56, 1.605), (0.0, -0.060, 1.605), 118)
        render(camera, f"{name}-02-three-quarter", (0.40, -0.56, 1.625), (0.0, -0.020, 1.605), 104)
        report[name] = {"strength": strength, "geometry": geometry}
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_EYELID_R78_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
