import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r15.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r16.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r16"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
PART = "AevryndFemaleScalpPart_v249r7"


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
part.name = "AevryndFemaleScalpPart_v249r16"
part.data.name = "AevryndFemaleScalpPartData_v249r16"

# Keep a narrow, irregular skin-visible line at the frontal part and taper it
# into root shadow before the crown.  The previous constant-width strip read as
# a luminous cut through the whole groom from a top camera.
for vertex in part.data.vertices:
    y = vertex.co.y
    center = part_x(y)
    posterior = smooth((y + 0.040) / 0.048)
    width_scale = 0.70 * (1.0 - posterior) + 0.16 * posterior
    irregular = math.sin(y * 173.0 + vertex.index * 0.91) * 0.00018 * (1.0 - posterior)
    vertex.co.x = center + (vertex.co.x - center) * width_scale + irregular
part.data.update()

skin_material = part.data.materials[0].copy()
skin_material.name = "Aevrynd_ScalpPartSkin_v249r16"
skin_material.diffuse_color = (0.050, 0.012, 0.006, 1.0)
skin_bsdf = next(node for node in skin_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
skin_bsdf.inputs["Base Color"].default_value = (0.050, 0.012, 0.006, 1.0)
skin_bsdf.inputs["Roughness"].default_value = 0.90
skin_bsdf.inputs["Specular IOR Level"].default_value = 0.06
part.data.materials[0] = skin_material

root_material = bpy.data.materials["Aevrynd_HairRootShadow_v249r6"]
if len(part.data.materials) == 1:
    part.data.materials.append(root_material)
else:
    part.data.materials[1] = root_material
posterior_faces = 0
for polygon in part.data.polygons:
    center_y = sum(part.data.vertices[index].co.y for index in polygon.vertices) / len(polygon.vertices)
    polygon.material_index = 1 if center_y > -0.015 else 0
    posterior_faces += int(polygon.material_index == 1)

part["aevrynd_candidate"] = "v249-mainline-hair-r16"
part["aevrynd_visible_part_relative_width_scale"] = 0.70
part["aevrynd_visible_part_crown_taper"] = 0.16
part["aevrynd_visible_part_shadow_start_y"] = -0.015
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r16"
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
print("AEVRYND_V249_MAINLINE_HAIR_R16=" + json.dumps({
    "output": str(OUTPUT),
    "posterior_shadow_faces": posterior_faces,
    "part_vertices": len(part.data.vertices),
    "part_faces": len(part.data.polygons),
}, sort_keys=True))
