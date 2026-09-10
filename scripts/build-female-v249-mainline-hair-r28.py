import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r27.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r28.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r28"
OUT.mkdir(parents=True, exist_ok=True)
MAIN = "AevryndFemaleGuideBob_v249r25"
POINTS = 20
FAMILY_SIZE = 25


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def rebuild_front_clumps(hair):
    data = hair.data
    selected = []
    maximum = 0.0
    lift_pattern = (0.006, 0.014, 0.009, 0.018, 0.011, 0.016, 0.007)
    depth_pattern = (0.003, 0.007, 0.0045, 0.009, 0.0055, 0.008, 0.0035)

    for family in range(len(data.curves) // FAMILY_SIZE):
        representative = family * FAMILY_SIZE
        root = data.points[representative * POINTS].position
        tip = data.points[representative * POINTS + POINTS - 1].position
        if not (root.y < -0.075 and root.z > 1.60 and tip.x > 0.075):
            continue
        selected.append(family)
        centers = []
        for point_index in range(POINTS):
            center = Vector((0.0, 0.0, 0.0))
            for follow in range(FAMILY_SIZE):
                center += data.points[(family * FAMILY_SIZE + follow) * POINTS + point_index].position
            centers.append(center / FAMILY_SIZE)

        macro = family % len(lift_pattern)
        family_lift = lift_pattern[macro]
        family_depth = depth_pattern[macro]
        side = ((macro % 3) - 1) * 0.0035
        for follow in range(FAMILY_SIZE):
            curve_index = family * FAMILY_SIZE + follow
            for point_index in range(1, POINTS):
                index = curve_index * POINTS + point_index
                point = data.points[index]
                original = point.position.copy()
                t = point_index / (POINTS - 1)
                arc = math.sin(math.pi * t)
                gather = 0.44 * smooth((t - 0.08) / 0.42)
                point.position = point.position.lerp(centers[point_index], gather)
                point.position.y -= family_depth * arc
                point.position.z += family_lift * arc
                point.position.x += side * arc
                maximum = max(maximum, (point.position - original).length)

    data.update_tag()
    hair.name = "AevryndFemaleGuideBob_v249r28"
    hair.data.name = "AevryndFemaleGuideBobData_v249r28"
    hair["aevrynd_candidate"] = "v249-mainline-hair-r28"
    hair["aevrynd_front_clump_rebuild"] = "64 front families, 7 macro arcs, roots locked"
    return {
        "families": selected,
        "family_count": len(selected),
        "curves_changed": len(selected) * FAMILY_SIZE,
        "arc_lift_mm": [min(lift_pattern) * 1000, max(lift_pattern) * 1000],
        "outward_depth_mm": [min(depth_pattern) * 1000, max(depth_pattern) * 1000],
        "maximum_displacement_mm": maximum * 1000,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
report = rebuild_front_clumps(bpy.data.objects[MAIN])
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r28"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86, (900, 900)),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (900, 900)),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78, (900, 900)),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
)
for name, location, target, lens, resolution in views:
    scene.frame_set(1)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

payload = {"source": str(SOURCE), "output": str(OUTPUT), "front_clumps": report}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R28=" + json.dumps(payload, sort_keys=True))
