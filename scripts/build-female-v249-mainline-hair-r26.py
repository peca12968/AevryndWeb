import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r25.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r26.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r26"
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


def break_up_front_sweep(hair):
    data = hair.data
    radius = data.attributes.get("radius")
    family_count = len(data.curves) // FAMILY_SIZE
    selected = []
    maximum = 0.0

    for family in range(family_count):
        representative = family * FAMILY_SIZE
        root = data.points[representative * POINTS].position
        tip = data.points[representative * POINTS + POINTS - 1].position
        # The dense front families all cross toward the model's right side.  They
        # need depth separation; rear and side families retain the r25 silhouette.
        if not (root.y < -0.075 and root.z > 1.60 and tip.x > 0.075):
            continue
        selected.append(family)
        family_phase = math.sin((family + 1) * 1.137)
        family_depth = 0.0010 + 0.0022 * (0.5 + 0.5 * family_phase)
        family_lift = 0.0012 * math.sin((family + 2) * 0.79)

        for follow in range(FAMILY_SIZE):
            curve_index = family * FAMILY_SIZE + follow
            follow_phase = math.sin((follow + 1) * 2.173 + family * 0.31)
            clump = (follow % 5 - 2) / 2.0
            for point_index in range(1, POINTS):
                index = curve_index * POINTS + point_index
                point = data.points[index]
                original = point.position.copy()
                t = point_index / (POINTS - 1)
                release = smooth((t - 0.08) / 0.72)
                arc = math.sin(math.pi * t)

                # Negative Y is away from the face in this authoring coordinate
                # system.  Alternating clumps produce visible depth instead of a
                # single parallel sheet while the root remains exactly fixed.
                point.position.y -= family_depth * release * (0.55 + 0.45 * (0.5 + 0.5 * follow_phase))
                point.position.x += (0.0014 * follow_phase + 0.0010 * clump) * arc
                point.position.z += (family_lift + 0.0010 * follow_phase) * arc
                maximum = max(maximum, (point.position - original).length)
                if radius:
                    radius.data[index].value *= 0.86 + 0.18 * (0.5 + 0.5 * follow_phase)

    data.update_tag()
    hair.name = "AevryndFemaleGuideBob_v249r26"
    hair.data.name = "AevryndFemaleGuideBobData_v249r26"
    hair["aevrynd_candidate"] = "v249-mainline-hair-r26"
    hair["aevrynd_front_sweep_breakup"] = "root-locked depth and width variation"
    return {
        "families": selected,
        "family_count": len(selected),
        "curves_changed": len(selected) * FAMILY_SIZE,
        "max_displacement_mm": maximum * 1000.0,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair_report = break_up_front_sweep(bpy.data.objects[MAIN])
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r26"
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

report = {"source": str(SOURCE), "output": str(OUTPUT), "front_sweep_breakup": hair_report}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R26=" + json.dumps(report, sort_keys=True))
