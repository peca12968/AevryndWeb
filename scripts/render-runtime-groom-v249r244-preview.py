import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-physical-hair-r244.blend",
))
DATA_DIR = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_PREVIEW_DIR",
    ROOT.parent / "Temp/female-realism/v249r244-physical-hair-dynamics",
))


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
metadata = json.loads((DATA_DIR / "frames.json").read_text(encoding="utf-8"))
points_per_curve = metadata["pointsPerCurve"]
curve_count = metadata["curveCount"]
total_value_count = curve_count * points_per_curve * 3

# Keep the collision-safe baked root veil rigidly attached to the head.  The
# long main and overlay strands are replaced by the simulated runtime curves.
for obj in scene.objects:
    layer = str(obj.get("aevrynd_layer", ""))
    if obj.type == "CURVES" and (layer.startswith("hair.main") or layer.startswith("hair.overlay")):
        obj.hide_render = True
        obj.hide_viewport = True

data = bpy.data.hair_curves.new("AevryndRuntimeHairPreview_v249r244_Data")
data.add_curves([points_per_curve] * curve_count)
radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
for curve in data.curves:
    for local_index in range(curve.points_length):
        t = local_index / max(1, curve.points_length - 1)
        radius.data[curve.first_point_index + local_index].value = 0.000035 * (1.0 - 0.82 * t ** 2)
runtime = bpy.data.objects.new("AevryndRuntimeHairPreview_v249r244", data)
scene.collection.objects.link(runtime)
material = bpy.data.materials.get("AevryndFemaleHairBase_v249r244")
if material:
    data.materials.append(material)

head = bpy.data.objects["AevryndFemaleRig"].pose.bones["head"]
head.rotation_mode = "XYZ"
camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("front", (0.0, -2.15, 1.56), (0.0, 0.0, 1.56), 82),
    ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("threequarter", (1.40, -1.70, 1.58), (0.0, 0.0, 1.55), 82),
)

for state in metadata["saved"]:
    head.rotation_euler = (0.0, state.get("yawDeg", 0.0) * math.pi / 180.0, 0.0)
    bpy.context.view_layer.update()
    payload = (DATA_DIR / state["filename"]).read_bytes()
    values = struct.unpack(f"<{total_value_count}f", payload)
    data.points.foreach_set("position", values)
    data.update_tag()
    for view, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(DATA_DIR / f"{view}-dynamic-{state['frame']:03d}.png")
        bpy.ops.render.render(write_still=True)

print("AEVRYND_V249R244_DYNAMIC_PREVIEW=" + json.dumps({
    "states": [state["frame"] for state in metadata["saved"]],
    "views": [view[0] for view in views],
    "curveCount": curve_count,
    "pointsPerCurve": points_per_curve,
    "output": str(DATA_DIR),
}, sort_keys=True))
