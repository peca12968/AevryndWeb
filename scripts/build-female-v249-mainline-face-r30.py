import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r27.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r30.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r30"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def sculpt_primary_face(body):
    moved = 0
    maximum = 0.0
    totals = {"cheek": 0.0, "bridge": 0.0, "alar": 0.0, "philtrum": 0.0, "chin": 0.0}
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        front = gaussian(y, -0.137, 0.026)
        face = front * gaussian(z, 1.565, 0.105)
        if face < 0.002:
            continue

        ax = abs(x)
        cheek = gaussian(ax, 0.052, 0.021) * gaussian(z, 1.580, 0.026) * front
        temple = gaussian(ax, 0.074, 0.017) * gaussian(z, 1.622, 0.032) * front
        bridge = gaussian(x, 0.0, 0.012) * gaussian(z, 1.603, 0.035) * front
        nasal_root = gaussian(x, 0.0, 0.017) * gaussian(z, 1.635, 0.014) * front
        alar = gaussian(ax, 0.020, 0.009) * gaussian(z, 1.556, 0.014) * front
        alar_groove = gaussian(ax, 0.030, 0.008) * gaussian(z, 1.548, 0.015) * front
        philtrum_center = gaussian(x, 0.0, 0.0045) * gaussian(z, 1.535, 0.012) * front
        philtrum_columns = gaussian(ax, 0.007, 0.0035) * gaussian(z, 1.535, 0.012) * front
        chin = gaussian(x, 0.0, 0.034) * gaussian(z, 1.486, 0.020) * front
        jaw = gaussian(ax, 0.066, 0.020) * gaussian(z, 1.492, 0.026) * front

        displacement = Vector((0.0, 0.0, 0.0))
        displacement.y += -0.0019 * cheek + 0.0007 * temple
        displacement.y += -0.0017 * bridge + 0.0007 * nasal_root
        displacement.y += -0.0010 * alar + 0.0010 * alar_groove
        displacement.y += 0.00065 * philtrum_center - 0.00055 * philtrum_columns
        displacement.y += -0.00155 * chin + 0.00045 * jaw
        # A restrained natural asymmetry prevents the two cheek planes from
        # reading as a mirrored procedural mask.
        displacement.y += -0.00028 * cheek * gaussian(x, 0.052, 0.026)
        if ax > 1e-6:
            displacement.x += math.copysign(0.00135 * alar + 0.00055 * jaw, x)

        length = displacement.length
        if length > 1e-7:
            vertex.co += displacement
            moved += 1
            maximum = max(maximum, length)
            totals["cheek"] += cheek
            totals["bridge"] += bridge
            totals["alar"] += alar
            totals["philtrum"] += philtrum_center + philtrum_columns
            totals["chin"] += chin
    body.data.update()
    body["aevrynd_face_revision"] = "v249-mainline-face-r30"
    body["aevrynd_face_method"] = "regional primary planes with restrained asymmetry"
    return {"vertices_moved": moved, "maximum_displacement_mm": maximum * 1000, "zone_weight_sums": totals}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
report = sculpt_primary_face(body)
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "face-r30"
scene["aevrynd_release_state"] = "FACE_PRIMARY_PLANES_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"

scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
    ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-face-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

payload = {"source": str(SOURCE), "output": str(OUTPUT), "geometry": report}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_FACE_R30=" + json.dumps(payload, sort_keys=True))
