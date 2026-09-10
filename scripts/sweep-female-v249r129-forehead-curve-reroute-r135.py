import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-forehead-curve-reroute-r135-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
VARIANTS = (
    ("a-baseline", 0.0, 0.0),
    ("b-back-2-up-3", 0.002, 0.003),
    ("c-back-4-up-6", 0.004, 0.006),
    ("d-back-6-up-9", 0.006, 0.009),
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def deepest_front_curves(obj):
    matrix = obj.matrix_world
    result = {}
    for curve_index, curve in enumerate(obj.data.curves):
        hits = []
        for local_index, point_index in enumerate(
            range(curve.first_point_index, curve.first_point_index + curve.points_length)
        ):
            point = matrix @ obj.data.points[point_index].position
            if abs(point.x) <= 0.120 and -0.150 <= point.y <= -0.130 and 1.625 <= point.z <= 1.715:
                hits.append(local_index)
        if hits:
            result[curve_index] = sum(hits) / len(hits)
    return result


def restore(obj, original):
    for index, position in enumerate(original):
        obj.data.points[index].position = position


def reroute(obj, targets, back, up):
    local_direction = obj.matrix_world.inverted().to_3x3() @ Vector((0.0, back, up))
    modified = 0
    maximum = 0.0
    for curve_index, center in targets.items():
        curve = obj.data.curves[curve_index]
        sigma = max(2.2, curve.points_length * 0.16)
        for local_index in range(curve.points_length):
            distance = (local_index - center) / sigma
            weight = math.exp(-0.5 * distance * distance)
            if weight < 0.02:
                continue
            point_index = curve.first_point_index + local_index
            delta = local_direction * weight
            obj.data.points[point_index].position += delta
            modified += 1
            maximum = max(maximum, delta.length)
    return modified, maximum


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
original = [point.position.copy() for point in main.data.points]
targets = deepest_front_curves(main)
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "targetCurves": sorted(targets), "variants": []}

for name, back, up in VARIANTS:
    restore(main, original)
    modified, maximum = reroute(main, targets, back, up)
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "backM": back,
        "upM": up,
        "modifiedControlPoints": modified,
        "maximumDisplacementM": maximum,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R135_FOREHEAD_CURVE_REROUTE=" + json.dumps(report, sort_keys=True))
