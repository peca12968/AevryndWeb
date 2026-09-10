import json
import os
from pathlib import Path

import bpy
from mathutils import Vector


source = Path(os.environ["AEVRYND_FACE_CONTROL_SOURCE"])
out = Path(os.environ["AEVRYND_FACE_CONTROL_OUT"])
out.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(source))
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
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(out / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("AEVRYND_V249_FACE_CONTROL=" + json.dumps({"source": str(source), "output": str(out)}))
