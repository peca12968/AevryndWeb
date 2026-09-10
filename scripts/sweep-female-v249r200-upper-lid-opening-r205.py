import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r205-upper-lid-opening-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-upper-lid-opening-r205.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = (0.034528, -0.034443)
VARIANTS = (("a-control", 0.0), ("b-subtle", 1.25), ("c-balanced", 1.50), ("d-open", 1.75))
LASH_CLEARANCE = 0.00030


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def upper_weight(p, center_x):
    dx = (p.x - center_x) / 0.0315
    if abs(dx) >= 1.05 or p.y > -0.094 or not (1.595 < p.z < 1.626):
        return 0.0
    horizontal = max(0.0, 1.0 - (abs(dx) / 1.05) ** 3) ** 1.35
    return horizontal * gaussian(p.y, -0.126, 0.023) * gaussian(p.z, 1.6096, 0.0037)


def open_upper_lid(key, strength):
    moved = 0
    maximum = 0.0
    for point in key.data:
        weight = max(upper_weight(point.co, center_x) for center_x in EYES)
        delta = strength * 0.00100 * weight
        if delta <= 1e-7:
            continue
        point.co.z += delta
        moved += 1
        maximum = max(maximum, delta)
    return {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0}


def move_lashes(obj, strength):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum_z = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        horizontal = 0.0
        for center_x in EYES:
            dx = (world.x - center_x) / 0.0315
            if abs(dx) < 1.08:
                horizontal = max(horizontal, max(0.0, 1.0 - (abs(dx) / 1.08) ** 3) ** 1.35)
        delta_z = strength * 0.00100 * horizontal * gaussian(world.z, 1.6096, 0.0042)
        world.z += delta_z
        world.y -= LASH_CLEARANCE
        vertex.co = inverse @ world
        moved += 1
        maximum_z = max(maximum_z, delta_z)
    obj.data.update()
    return {"verticesMoved": moved, "maximumVerticalMoveMm": maximum_z * 1000.0, "outwardClearanceMm": LASH_CLEARANCE * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"strength": strength}
    if strength:
        body = bpy.data.objects[BODY]
        key, previous = consolidate(body, f"Aevrynd_UpperLidOpening_R205_{strength:.2f}")
        metrics.update(open_upper_lid(key, strength))
        metrics["shapeKey"] = key.name
        metrics["consolidatedShapeKeys"] = previous
        metrics["upperLashes"] = {
            f"Eye_{side}_UpperLashes": move_lashes(bpy.data.objects[f"Eye_{side}_UpperLashes"], strength)
            for side in ("L", "R")
        }
        body.data.update()
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-eyes-front", (0.0, -0.445, 1.611), (0.0, -0.076, 1.607), 132, (1280, 760)),
        ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
        ("04-eye-three-quarter", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R205_UPPER_LID_OPENING=" + json.dumps(report, sort_keys=True))
