import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r6.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r7.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r7"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
PART = "AevryndFemaleScalpPart_v249r6"


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def part_x(y):
    return -0.032 + 0.027 * smooth((y + 0.105) / 0.170)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
part = bpy.data.objects[PART]
part.name = "AevryndFemaleScalpPart_v249r7"
part.data.name = "AevryndFemaleScalpPartData_v249r7"

for vertex in part.data.vertices:
    center = part_x(vertex.co.y)
    vertex.co.x = center + (vertex.co.x - center) * 0.52
part.data.update()

material = part.data.materials[0].copy()
material.name = "Aevrynd_ScalpPartSkin_v249r7"
part.data.materials[0] = material
material.diffuse_color = (0.105, 0.027, 0.014, 1.0)
principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
principled.inputs["Base Color"].default_value = (0.105, 0.027, 0.014, 1.0)
principled.inputs["Roughness"].default_value = 0.78
principled.inputs["Specular IOR Level"].default_value = 0.12
part["aevrynd_candidate"] = "v249-mainline-hair-r7"
part["aevrynd_visible_part_width_scale"] = 0.52

scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r7"
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
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R7=" + json.dumps({
    "output": str(OUTPUT),
    "part_width_scale": 0.52,
    "part_base_color": [0.105, 0.027, 0.014, 1.0],
}, sort_keys=True))
