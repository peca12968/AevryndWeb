import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-long-hair-r229.blend",
))
DATA_DIR = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_PREVIEW_DIR",
    ROOT.parent / "Temp/female-realism/v249r229-pruned-long-hair-dynamics",
))
MAIN = os.environ.get("AEVRYND_RUNTIME_GROOM_MAIN_OBJECT", "AevryndFemaleCC0LongHairStudyMain_v249r85")
FLY = os.environ.get("AEVRYND_RUNTIME_GROOM_FLY_OBJECT", "AevryndFemaleCC0LongHairStudyFlyaway_v249r85")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def expand_runtime_to_source(values, value_start, source, curve_count, points_per_curve):
    output = []
    for curve_index in range(curve_count):
        curve = source.data.curves[curve_index]
        runtime_start = value_start + curve_index * points_per_curve * 3
        for point_index in range(curve.points_length):
            position = point_index / max(1, curve.points_length - 1) * (points_per_curve - 1)
            first = min(points_per_curve - 2, int(position))
            blend = position - first
            a = runtime_start + first * 3
            b = a + 3
            output.extend((
                values[a] + (values[b] - values[a]) * blend,
                values[a + 1] + (values[b + 1] - values[a + 1]) * blend,
                values[a + 2] + (values[b + 2] - values[a + 2]) * blend,
            ))
    return output


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
metadata = json.loads((DATA_DIR / "frames.json").read_text(encoding="utf-8"))
points_per_curve = metadata["pointsPerCurve"]
main_curve_count = metadata["mainCurveCount"]
fly_curve_count = metadata["fillCurveCount"]
main_source = bpy.data.objects[MAIN]
fly_source = bpy.data.objects[FLY]
main = main_source
fly = fly_source
for obj in (main, fly):
    obj.hide_render = False
    obj.hide_viewport = False
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
head = bpy.data.objects["AevryndFemaleRig"].pose.bones["head"]
head.rotation_mode = "XYZ"
total_value_count = metadata["curveCount"] * points_per_curve * 3

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 640
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
    main.data.points.foreach_set("position", expand_runtime_to_source(
        values, 0, main, main_curve_count, points_per_curve))
    if fly_curve_count:
        fly.data.points.foreach_set("position", expand_runtime_to_source(
            values, main_curve_count * points_per_curve * 3, fly, fly_curve_count, points_per_curve))
    else:
        fly.hide_render = True
    main.data.update_tag()
    fly.data.update_tag()
    for view, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(DATA_DIR / f"{view}-dynamic-{state['frame']:03d}.png")
        bpy.ops.render.render(write_still=True)

print("AEVRYND_V249R229_DYNAMIC_PREVIEW=" + json.dumps({
    "states": [state["frame"] for state in metadata["saved"]],
    "views": [view[0] for view in views],
    "output": str(DATA_DIR),
}, sort_keys=True))
