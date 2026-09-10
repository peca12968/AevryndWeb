import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cloth-r35.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r37.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r37"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def sculpt_identity_silhouette(body):
    moved = 0
    maximum = 0.0
    zone_counts = {"jaw": 0, "chin": 0, "alar": 0, "tip": 0}
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        ax = abs(x)
        front = gaussian(y, -0.137, 0.025) * gaussian(z, 1.545, 0.115)
        if front < 0.002:
            continue

        # Preserve every established eye/lash/fold and lip/wet-line contact.
        eye_contact_guard = 0.012 < ax < 0.088 and 1.582 < z < 1.648
        lip_contact_guard = ax < 0.066 and 1.500 < z < 1.548
        if eye_contact_guard or lip_contact_guard:
            continue

        jaw = gaussian(ax, 0.073, 0.026) * gaussian(z, 1.485, 0.034) * front
        jaw_angle = gaussian(ax, 0.091, 0.017) * gaussian(z, 1.515, 0.028) * front
        chin = gaussian(ax, 0.022, 0.030) * gaussian(z, 1.466, 0.022) * front
        chin_side = gaussian(ax, 0.043, 0.015) * gaussian(z, 1.476, 0.023) * front
        alar = gaussian(ax, 0.023, 0.010) * gaussian(z, 1.557, 0.013) * front
        nose_tip = gaussian(ax, 0.008, 0.012) * gaussian(z, 1.563, 0.014) * front
        bridge = gaussian(ax, 0.0, 0.010) * gaussian(z, 1.596, 0.021) * front

        displacement = Vector((0.0, 0.0, 0.0))
        if ax > 1e-6:
            # Narrow the lower third while retaining the cheek width established in r31.
            displacement.x -= math.copysign(0.0032 * jaw + 0.0015 * jaw_angle, x)
            displacement.x -= math.copysign(0.00105 * alar + 0.00045 * chin_side, x)
        # Give the chin and nose a readable profile instead of a flat front plane.
        displacement.y -= 0.00165 * chin + 0.00075 * nose_tip + 0.00045 * bridge
        displacement.z -= 0.00085 * chin
        # Restrained left/right variation avoids a perfectly mirrored procedural mask.
        displacement.y -= 0.00020 * jaw * gaussian(x, 0.070, 0.030)

        length = displacement.length
        if length <= 1e-7:
            continue
        vertex.co += displacement
        moved += 1
        maximum = max(maximum, length)
        if jaw + jaw_angle > 0.05:
            zone_counts["jaw"] += 1
        if chin + chin_side > 0.05:
            zone_counts["chin"] += 1
        if alar > 0.05:
            zone_counts["alar"] += 1
        if nose_tip + bridge > 0.05:
            zone_counts["tip"] += 1

    body.data.update()
    body["aevrynd_face_revision"] = "v249-mainline-face-r37"
    body["aevrynd_face_method"] = "eye-lip-safe lower-third silhouette and nasal refinement"
    return {
        "vertices_moved": moved,
        "maximum_displacement_mm": maximum * 1000.0,
        "zone_vertex_counts": zone_counts,
    }


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
geometry = sculpt_identity_silhouette(body)
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "face-r37"
scene["aevrynd_release_state"] = "FACE_R37_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"

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
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for diagnostic in (False, True):
    for obj in hair_objects:
        obj.hide_render = diagnostic
    suffix = "face-only" if diagnostic else "with-hair"
    for name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
for obj in hair_objects:
    obj.hide_render = False

payload = {"source": str(SOURCE), "output": str(OUTPUT), "geometry": geometry}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_FACE_R37=" + json.dumps(payload, sort_keys=True))
