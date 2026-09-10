import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r16.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r17"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
FILL_HAIR = "AevryndFemaleNapeFiberFill_v249r15"
POINTS = 20
TRIM_POINTS = 2.5


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
fill = bpy.data.objects[FILL_HAIR]
data = fill.data
curve_count = len(data.curves)
positions = [point.position.copy() for point in data.points]

# Reparameterize each fixed-size curve over its lower 17.5 original samples.
# This trims the exposed upper root row while retaining the same lower nape flow.
for curve_index in range(curve_count):
    base = curve_index * POINTS
    source = positions[base:base + POINTS]
    for point_index in range(POINTS):
        source_index = TRIM_POINTS + point_index * ((POINTS - 1 - TRIM_POINTS) / (POINTS - 1))
        low = min(POINTS - 1, int(math.floor(source_index)))
        high = min(POINTS - 1, low + 1)
        factor = source_index - low
        data.points[base + point_index].position = source[low].lerp(source[high], factor)
data.update_tag()

fill.name = "AevryndFemaleNapeFiberFill_v249r17"
fill.data.name = "AevryndFemaleNapeFiberFillData_v249r17"
fill["aevrynd_candidate"] = "v249-mainline-hair-r17"
fill["aevrynd_trimmed_root_samples"] = TRIM_POINTS
part = bpy.data.objects["AevryndFemaleScalpPart_v249r16"]
part["aevrynd_candidate"] = "v249-mainline-hair-r17"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r17"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
)
for name, location, target, lens in views:
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R17=" + json.dumps({
    "output": str(OUTPUT),
    "curves": curve_count,
    "points": len(data.points),
    "trimmed_root_samples": TRIM_POINTS,
}, sort_keys=True))
