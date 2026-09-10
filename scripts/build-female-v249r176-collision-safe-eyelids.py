import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-eyelids-r176.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r176-collision-safe-eyelids"
OUT.mkdir(parents=True, exist_ok=True)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def refine_lids(body):
    body.data = body.data.copy()
    body.data.name = body.data.name + "_CollisionSafeLids_v249r176"
    body.data.update()
    normals = [vertex.normal.copy() for vertex in body.data.vertices]
    moved = 0
    maximum = 0.0
    for vertex, normal in zip(body.data.vertices, normals):
        p = vertex.co.copy()
        if p.y > -0.096 or not (1.588 < p.z < 1.627):
            continue
        delta = Vector((0.0, 0.0, 0.0))
        for cx in (-0.035, 0.035):
            dx = (p.x - cx) / 0.031
            if abs(dx) >= 1.10:
                continue
            horizontal = max(0.0, 1.0 - (dx / 1.10) ** 2) ** 1.8
            front = gaussian(p.y, -0.126, 0.024)
            upper = horizontal * front * gaussian(p.z, 1.6098, 0.0034)
            lower = horizontal * front * gaussian(p.z, 1.5989, 0.0036)
            crease = horizontal * front * gaussian(p.z, 1.6180, 0.0028)
            # Close the aperture by less than 0.2 mm, while most of the visible
            # change is outward lid-roll volume rather than motion into the eye.
            delta.z += -0.000072 * upper + 0.000030 * lower
            delta += normal * (0.000080 * upper + 0.000052 * lower - 0.000044 * crease)
            outer = max(0.0, abs(dx) - 0.72) / 0.38
            delta.z += 0.000032 * outer * horizontal * front * (1.0 if dx * cx > 0.0 else 0.0)
        if delta.length > 1e-7:
            vertex.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    body.data.update()
    body["aevrynd_face_revision"] = "v249r176"
    body["aevrynd_eyelid_structure"] = "collision-safe micro lid rolls with recessed eye assembly"
    return {"vertices_moved": moved, "max_move_mm": maximum * 1000.0}


def recess_eyes():
    moved = {}
    prefixes = ("Eye_L_", "Eye_R_")
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.startswith(prefixes):
            continue
        shift = 0.00010 if any(label in obj.name for label in ("Lashes", "UpperFold")) else 0.00040
        obj.data = obj.data.copy()
        obj.data.name = obj.data.name + "_Recessed_v249r176"
        for vertex in obj.data.vertices:
            vertex.co.y += shift
        obj.data.update()
        obj["aevrynd_face_revision"] = "v249r176"
        moved[obj.name] = {"vertices": len(obj.data.vertices), "shift_mm": shift * 1000.0}
    return moved


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
report = {"eyelids": refine_lids(body), "recessed_eye_meshes": recess_eyes(), "eye_recess_mm": 0.40, "lash_fold_recess_mm": 0.10}

scene = bpy.context.scene
scene["aevrynd_face_revision"] = "v249r176"
scene["aevrynd_release_state"] = "COLLISION_SAFE_EYELIDS_PENDING_REVIEW"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("04-face-profile", (0.70, -0.02, 1.61), (0.0, -0.015, 1.595), 92),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

(ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-eyelids-r176.build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R176_COLLISION_SAFE_EYELIDS=" + json.dumps(report, sort_keys=True))

