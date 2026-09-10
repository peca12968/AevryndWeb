import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-crown-flow-r152.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r152-crown-lift-r153-sweep"
CROWN = "AevryndFemaleOwnedHairCrownFlow_v249r152"
VARIANTS_MM = (0.0, 1.5, 3.0, 4.5)
HEAD_CENTER = Vector((0.0, -0.020, 1.615))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
crown = bpy.data.objects[CROWN]
base_positions = [point.position.copy() for point in crown.data.points]
for obj in bpy.data.objects:
    if obj.type == "CURVES":
        obj.visible_shadow = False

report = {"source": str(SOURCE), "crown": CROWN, "variants": [], "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
for lift_mm in VARIANTS_MM:
    lift = lift_mm * 0.001
    modified = 0
    maximum = 0.0
    for curve in crown.data.curves:
        root = base_positions[curve.first_point_index]
        normal = root - HEAD_CENTER
        normal.y *= 0.78
        normal.normalize()
        for local_index in range(curve.points_length):
            point_index = curve.first_point_index + local_index
            t = local_index / max(1, curve.points_length - 1)
            weight = math.sin(math.pi * t / 0.68) if t < 0.68 else 0.0
            displacement = normal * lift * weight
            crown.data.points[point_index].position = base_positions[point_index] + displacement
            if displacement.length > 1e-9:
                modified += 1
                maximum = max(maximum, displacement.length)
    prefix = f"lift-{lift_mm:.1f}mm".replace(".", "p")
    render(camera, f"{prefix}-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78)
    render(camera, f"{prefix}-face", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    report["variants"].append({"liftMm": lift_mm, "modifiedPoints": modified, "maximumDisplacementM": maximum})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R152_CROWN_LIFT_R153=" + json.dumps(report, sort_keys=True))
