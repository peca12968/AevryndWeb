import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-boolean-eyelid-r67.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-orbital-r68-strong-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = ((0.034528, -0.10087, 1.607765), (-0.034443, -0.10077, 1.607765))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def displacement(point, strength_m):
    if not (-0.133 < point.y < -0.094):
        return 0.0
    best = 0.0
    for cx, cy, cz in EYES:
        dx = (point.x - cx) / 0.0185
        dz = point.z - cz
        if abs(dx) >= 1.08 or not (-0.013 < dz < 0.018):
            continue
        horizontal = smoothstep(1.08, 0.58, abs(dx))
        horizontal = 0.18 * max(0.0, 1.0 - abs(dx) / 1.08) + 0.82 * horizontal
        front = gaussian(point.y, -0.114, 0.0105)

        # Preserve the boolean lid margin.  A shallow inward crease above it
        # separates the mobile upper lid from the supraorbital plane; a much
        # weaker lower recession removes the spherical under-eye bulge.
        upper_crease = gaussian(dz, 0.0075, 0.00175)
        lid_roll = gaussian(dz, 0.00445, 0.00105)
        brow_transition = gaussian(dz, 0.0123, 0.0027)
        lower_plane = gaussian(dz, -0.0072, 0.00235)
        margin_guard = smoothstep(0.0040, 0.0052, dz) if dz >= 0.0 else smoothstep(0.0035, 0.0050, -dz)

        delta = strength_m * horizontal * front * (
            0.92 * upper_crease * margin_guard
            - 0.16 * lid_roll * margin_guard
            - 0.10 * brow_transition
            + 0.28 * lower_plane * margin_guard
        )
        if abs(delta) > abs(best):
            best = delta
    return best


def apply_sculpt(body, strength_m):
    moved = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        delta_y = displacement(vertex.co, strength_m)
        if abs(delta_y) < 0.000002:
            continue
        vertex.co.y += delta_y
        moved += 1
        maximum = max(maximum, abs(delta_y))
    body.data.update()
    return {"moved_vertices": moved, "max_displacement_mm": maximum * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
body = bpy.data.objects[BODY]
original_mesh = body.data
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
views = (
    ("front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
)
report = {}
for strength_mm in (0.0, 1.40, 1.90, 2.40):
    body.data = original_mesh.copy()
    report[strength_mm] = apply_sculpt(body, strength_mm / 1000.0)
    for obj in hair_objects:
        obj.hide_render = True
    label = f"{strength_mm:.2f}mm".replace(".", "p")
    for view_name, location, target, lens in views:
        render(camera, f"{label}-{view_name}-face-only", location, target, lens)
    for obj in hair_objects:
        obj.hide_render = False
    render(camera, f"{label}-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)

body.data = original_mesh
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_ORBITAL_R68_SWEEP=" + json.dumps(report, sort_keys=True))
