import json
import os
import struct
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend",
))
DATA_DIR = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_PREVIEW_DIR",
    ROOT.parent / "Temp/female-realism/v249-mainline-hair-r17-dynamics",
))
MAIN = os.environ.get("AEVRYND_RUNTIME_GROOM_MAIN_OBJECT", "AevryndFemaleGuideBob_v249r12")
FILL = "AevryndFemaleNapeFiberFill_v249r17"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
metadata = json.loads((DATA_DIR / "frames.json").read_text(encoding="utf-8"))
main = bpy.data.objects[MAIN]
fill = bpy.data.objects[FILL]
main.parent = None
fill.parent = None
main.matrix_world = Matrix.Identity(4)
fill.matrix_world = Matrix.Identity(4)
head = bpy.data.objects["AevryndFemaleRig"].pose.bones["head"]
head.rotation_mode = "XYZ"
main_values = len(main.data.points) * 3
total_values = (len(main.data.points) + len(fill.data.points)) * 3

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
)

for state in metadata["saved"]:
    head.rotation_euler = (0.0, state.get("yawDeg", 0.0) * 3.141592653589793 / 180.0, 0.0)
    bpy.context.view_layer.update()
    payload = (DATA_DIR / state["filename"]).read_bytes()
    values = struct.unpack(f"<{total_values}f", payload)
    main.data.points.foreach_set("position", values[:main_values])
    fill.data.points.foreach_set("position", values[main_values:])
    main.data.update_tag()
    fill.data.update_tag()
    for view, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(DATA_DIR / f"{view}-dynamic-{state['frame']:03d}.png")
        bpy.ops.render.render(write_still=True)

print("AEVRYND_V249R17_DYNAMIC_PREVIEW=" + json.dumps({
    "states": [state["frame"] for state in metadata["saved"]],
    "views": [view[0] for view in views],
    "output": str(DATA_DIR),
}, sort_keys=True))
