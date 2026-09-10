import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r202-eye-aperture-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-aperture-r202.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = (0.034528, -0.034443)
VARIANTS = (
    ("a-control", 0.0),
    ("b-natural", 1.0),
    ("c-open", 1.5),
    ("d-strong", 2.0),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def eye_weight(p, center_x):
    dx = (p.x - center_x) / 0.0315
    if abs(dx) >= 1.05 or p.y > -0.094 or not (1.588 < p.z < 1.626):
        return 0.0, 0.0
    horizontal = max(0.0, 1.0 - (abs(dx) / 1.05) ** 3) ** 1.35
    front = gaussian(p.y, -0.126, 0.023)
    upper = horizontal * front * gaussian(p.z, 1.6096, 0.0037)
    lower = horizontal * front * gaussian(p.z, 1.5995, 0.0035)
    return upper, lower


def open_body(key, strength):
    moved = 0
    maximum = 0.0
    upper_max = 0.0
    lower_max = 0.0
    for point in key.data:
        upper = lower = 0.0
        for center_x in EYES:
            local_upper, local_lower = eye_weight(point.co, center_x)
            upper = max(upper, local_upper)
            lower = max(lower, local_lower)
        delta = strength * (0.00100 * upper - 0.00038 * lower)
        if abs(delta) <= 1e-7:
            continue
        point.co.z += delta
        moved += 1
        maximum = max(maximum, abs(delta))
        upper_max = max(upper_max, max(delta, 0.0))
        lower_max = max(lower_max, max(-delta, 0.0))
    return {
        "verticesMoved": moved,
        "maximumMoveMm": maximum * 1000.0,
        "upperMaximumMm": upper_max * 1000.0,
        "lowerMaximumMm": lower_max * 1000.0,
        "nominalApertureIncreaseMm": strength * 1.38,
    }


def move_accessory(obj, strength, direction, center_z, sigma):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        horizontal = 0.0
        for center_x in EYES:
            dx = (world.x - center_x) / 0.0315
            if abs(dx) < 1.08:
                horizontal = max(horizontal, max(0.0, 1.0 - (abs(dx) / 1.08) ** 3) ** 1.35)
        if horizontal <= 0.0:
            continue
        amount = strength * direction * horizontal * gaussian(world.z, center_z, sigma)
        if abs(amount) <= 1e-7:
            continue
        world.z += amount
        vertex.co = inverse @ world
        moved += 1
        maximum = max(maximum, abs(amount))
    obj.data.update()
    return {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0}


def synchronize_layers(strength):
    result = {}
    for side in ("L", "R"):
        lash = bpy.data.objects[f"Eye_{side}_UpperLashes"]
        result[lash.name] = move_accessory(lash, strength, 0.00100, 1.6096, 0.0042)
        tear = bpy.data.objects[f"Eye_{side}_TearMeniscus"]
        result[tear.name] = move_accessory(tear, strength, -0.00038, 1.5995, 0.0040)
        caruncle = bpy.data.objects[f"Eye_{side}_Caruncle"]
        result[caruncle.name] = move_accessory(caruncle, strength, -0.00008, 1.6050, 0.0060)
    return result


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
        key, previous = consolidate(body, f"Aevrynd_EyeAperture_R202_{strength:.2f}")
        metrics.update(open_body(key, strength))
        metrics["shapeKey"] = key.name
        metrics["consolidatedShapeKeys"] = previous
        metrics["synchronizedLayers"] = synchronize_layers(strength)
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
print("AEVRYND_V249R202_EYE_APERTURE=" + json.dumps(report, sort_keys=True))
