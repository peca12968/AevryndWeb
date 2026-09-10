import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r19.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eyelid-r19"
BODY = "AevryndFemaleBodyBaseV118"
EYES = ((0.034528, -0.10087, 1.607765), (-0.034443, -0.10077, 1.607765))
STRENGTH_M = 0.0025


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def delta_at(point):
    best = None
    for cx, cy, cz in EYES:
        dx = (point.x - cx) / 0.0190
        dz = point.z - cz
        if abs(dx) >= 1.10 or not (-0.017 < dz < 0.020) or point.y > -0.094:
            continue
        front = gaussian(point.y, -0.113, 0.012)
        horizontal = max(0.0, 1.0 - (dx / 1.10) ** 2) ** 1.65
        upper = horizontal * front * gaussian(dz, 0.0052, 0.0033)
        lower = horizontal * front * gaussian(dz, -0.0055, 0.0030)
        outer = smoothstep(0.62, 1.02, abs(dx))
        delta = Vector((0.0, -STRENGTH_M * (0.30 * upper + 0.22 * lower), 0.0))
        delta.z += STRENGTH_M * (-0.58 * upper + 0.30 * lower)
        delta.z += STRENGTH_M * 0.13 * outer * horizontal * front
        inner = smoothstep(0.78, 1.02, abs(dx)) if dx * cx < 0.0 else 1.0
        delta *= 0.72 + 0.28 * inner
        weight = upper + lower
        if weight > 0.02 and (best is None or weight > best[0]):
            best = (weight, delta)
    return best[1] if best else None


def apply_body(body):
    moved = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        delta = delta_at(vertex.co)
        if delta is None:
            continue
        vertex.co += delta
        moved += 1
        maximum = max(maximum, delta.length)
    body.data.update()
    return {"moved_vertices": moved, "max_displacement_mm": maximum * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
report = apply_body(body)
body["aevrynd_mainline_baseline"] = "v249"
body["aevrynd_face_revision"] = "v249-mainline-eyelid-r19"
body["aevrynd_eyelid_method"] = "globe-aware tangential lid wrap with outward margin roll"
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "eyelid-r19"
scene["aevrynd_release_state"] = "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "01-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112)
render(camera, "02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
render(camera, "03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_MAINLINE_EYELID_R19=" + json.dumps(report, sort_keys=True))
