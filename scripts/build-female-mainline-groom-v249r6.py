import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r2.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r6.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r6"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
SCALP = "AevryndFemaleScalpCoverage_v378"
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
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects["AevryndFemaleRig"]
scalp = bpy.data.objects[SCALP]

# The coverage shell is a root shadow, so suppress the broad grey specular band
# that made an empty rear part visible through otherwise dense hair.
old_material = scalp.data.materials[0]
scalp_material = old_material.copy()
scalp_material.name = "Aevrynd_HairRootShadow_v249r6"
scalp.data.materials[0] = scalp_material
scalp_material.diffuse_color = (0.006, 0.0022, 0.0014, 1.0)
if scalp_material.use_nodes:
    principled = next(node for node in scalp_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (0.006, 0.0022, 0.0014, 1.0)
    principled.inputs["Roughness"].default_value = 0.94
    principled.inputs["Specular IOR Level"].default_value = 0.06
scalp["aevrynd_layer"] = "hair.scalp.root_shadow"
scalp["aevrynd_mainline_hair_collision"] = True
bpy.data.objects["AevryndFemaleGuideBob_v378"]["aevrynd_mainline_hair_collision"] = True

# Add a warm skin-toned part only from the frontal hairline to the crown.  It is
# projected from the actual v249 head, so the line follows its anatomy and ends
# before the rear fall instead of exposing a grey stripe down the back.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
tree = BVHTree.FromPolygons(
    [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices],
    [tuple(poly.vertices) for poly in mesh.polygons],
    all_triangles=False,
)
evaluated.to_mesh_clear()

vertices = []
segments = 34
for index in range(segments):
    t = index / (segments - 1)
    y = -0.116 + 0.132 * t
    center_x = part_x(y)
    half_width = 0.00115 + 0.00055 * math.sin(math.pi * t) ** 2
    half_width *= 0.88 + 0.12 * math.sin(index * 2.17)
    for x in (center_x - half_width, center_x + half_width):
        hit = tree.ray_cast(Vector((x, y, 1.90)), Vector((0.0, 0.0, -1.0)), 0.50)
        if hit[0] is None or hit[1] is None:
            raise RuntimeError(f"No v249 scalp hit for part at {(x, y)}")
        vertices.append(hit[0] + hit[1].normalized() * 0.00135)
faces = [(index * 2, index * 2 + 1, index * 2 + 3, index * 2 + 2) for index in range(segments - 1)]
part_mesh = bpy.data.meshes.new("AevryndFemaleScalpPartData_v249r6")
part_mesh.from_pydata(vertices, [], faces)
part_mesh.update()

part_material = bpy.data.materials.new("Aevrynd_ScalpPartSkin_v249r6")
part_material.use_nodes = True
part_material.diffuse_color = (0.31, 0.105, 0.060, 1.0)
part_bsdf = next(node for node in part_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
part_bsdf.inputs["Base Color"].default_value = (0.31, 0.105, 0.060, 1.0)
part_bsdf.inputs["Roughness"].default_value = 0.72
part_bsdf.inputs["Specular IOR Level"].default_value = 0.22
part_mesh.materials.append(part_material)

part = bpy.data.objects.new(PART, part_mesh)
scene.collection.objects.link(part)
part.parent = rig
part.parent_type = "BONE"
part.parent_bone = "head"
part.matrix_world = scalp.matrix_world.copy()
part["aevrynd_layer"] = "hair.scalp.visible_part"
part["aevrynd_mainline_base"] = "v249"
part["aevrynd_candidate"] = "v249-mainline-hair-r6"
part["aevrynd_mainline_hair_collision"] = True

scene["aevrynd_mainline_base"] = "v249"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r6"
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
print("AEVRYND_V249_MAINLINE_HAIR_R6=" + json.dumps({
    "output": str(OUTPUT),
    "part_vertices": len(vertices),
    "part_faces": len(faces),
    "part_y_range": [-0.116, 0.016],
    "root_shadow_material": scalp_material.name,
}, sort_keys=True))
