import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r197-mouth-placement-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-mouth-placement-r197.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
MOUTH_OBJECTS = ("Lip_Lower", "Lip_Upper", "Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth", "Mouth_WetLine")
VARIANTS = (("a-control", 0.0), ("b-down-5mm", 0.005), ("c-down-10mm", 0.010), ("d-down-15mm", 0.015))


def smoothstep(edge0, edge1, value):
    if edge0 == edge1:
        return 0.0
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def body_weight(p):
    if abs(p.x) > 0.082 or p.y > -0.072 or not (1.455 < p.z < 1.565):
        return 0.0
    lateral = gaussian(abs(p.x), 0.0, 0.050)
    front = smoothstep(-0.072, -0.116, p.y)
    upper = smoothstep(1.565, 1.548, p.z)
    lower = smoothstep(1.455, 1.492, p.z)
    return lateral * front * upper * lower


def deform_body(key, shift):
    moved = 0
    maximum = 0.0
    for point in key.data:
        weight = body_weight(point.co)
        if weight <= 1e-6:
            continue
        delta = shift * weight
        point.co.z -= delta
        moved += 1
        maximum = max(maximum, delta)
    return {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0}


def move_object_world_z(obj, shift):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.z -= shift
        vertex.co = inverse @ world
    obj.data.update()
    return len(obj.data.vertices)


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
report = {"source": str(SOURCE), "variants": {}}
for label, shift in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"shiftMm": shift * 1000.0, "verticesMoved": 0, "maximumMoveMm": 0.0}
    if shift:
        body = bpy.data.objects[BODY]
        key, previous = consolidate(body, f"Aevrynd_MouthPlacement_R197_{shift * 1000.0:.0f}mm")
        metrics.update(deform_body(key, shift))
        metrics["shapeKey"] = key.name
        metrics["consolidatedShapeKeys"] = previous
        metrics["mouthObjects"] = {name: move_object_world_z(bpy.data.objects[name], shift) for name in MOUTH_OBJECTS}
        body.data.update()
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
        ("03-face-profile", (0.70, -0.03, 1.60), (0.0, -0.010, 1.575), 92, (1000, 1000)),
        ("04-mouth-front", (0.0, -0.47, 1.525), (0.0, -0.075, 1.520), 122, (1200, 900)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R197_MOUTH_PLACEMENT=" + json.dumps(report, sort_keys=True))
