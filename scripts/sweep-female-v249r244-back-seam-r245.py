import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-physical-hair-r244.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r245-back-seam-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-back-seam-r245.sweep-report.json"
TARGET_LAYERS = ("hair.main", "hair.overlay")
VARIANTS = (
    ("a-control", 0.0),
    ("b-close-5mm", 0.005),
    ("c-close-10mm", 0.010),
    ("d-close-15mm", 0.015),
)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def target_objects():
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == "CURVES" and any(str(obj.get("aevrynd_layer", "")).startswith(prefix) for prefix in TARGET_LAYERS)
    ]


def close_back_seam(objects, shift):
    moved = 0
    maximum = 0.0
    for obj in objects:
        inverse_vector = obj.matrix_world.inverted().to_3x3()
        for curve in obj.data.curves:
            for local_index in range(1, curve.points_length):
                index = curve.first_point_index + local_index
                point = obj.data.points[index]
                world = obj.matrix_world @ point.position
                if world.y <= 0.0 or abs(world.x) >= 0.075:
                    continue
                t = local_index / max(1, curve.points_length - 1)
                backness = smoothstep(0.0, 0.080, world.y)
                root_release = smoothstep(0.12, 0.58, t)
                center = 1.0 - smoothstep(0.025, 0.075, abs(world.x))
                weight = backness * root_release * (0.35 + 0.65 * center)
                direction = -1.0 if world.x > 0.0 else 1.0
                delta = Vector((direction * shift * weight, 0.0, 0.0))
                point.position += inverse_vector @ delta
                if delta.length > 1e-8:
                    moved += 1
                    maximum = max(maximum, delta.length)
        obj.data.update_tag()
    return {"pointsMoved": moved, "maximumMoveMm": maximum * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}}
for label, shift in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = close_back_seam(target_objects(), shift) if shift else {"pointsMoved": 0, "maximumMoveMm": 0.0}
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for view_name, location, target, lens in (
        ("01-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.595), 88),
        ("02-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("03-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ):
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {"shiftM": shift, **metrics}
report["status"] = "STRICT_VISUAL_SELECTION_PENDING"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R245_BACK_SEAM=" + json.dumps(report, sort_keys=True))
