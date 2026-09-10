import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = Path(os.environ.get(
    "AEVRYND_FACE_DIAGNOSTIC_MODEL",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r31.blend",
))
OUT = Path(os.environ.get(
    "AEVRYND_FACE_DIAGNOSTIC_OUT",
    ROOT.parent / "Temp/female-realism/v249-face-diagnostic",
))
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
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
print(f"AEVRYND_FACE_DIAGNOSTIC={OUT}")
