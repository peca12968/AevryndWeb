import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r12.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r13.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r13"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
UNDERLAYER = "AevryndFemaleNapeUnderlayer_v249r13"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects["AevryndFemaleRig"]

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
faces = []
uvs = []
strips = 11
segments = 13
for strip in range(strips):
    center_x = -0.024 + strip * (0.048 / (strips - 1))
    start = len(vertices)
    for point_index in range(segments):
        t = point_index / (segments - 1)
        z = 1.655 - 0.245 * t
        wave_x = math.sin(strip * 1.91 + t * math.pi * 1.3) * 0.0016 * t
        x = center_x + wave_x
        hit = tree.ray_cast(Vector((x, 0.30, z)), Vector((0.0, -1.0, 0.0)), 0.45)
        if hit[0] is None or hit[1] is None:
            raise RuntimeError(f"No posterior body hit at {(x, z)}")
        center = hit[0] + hit[1].normalized() * (0.0030 + 0.0025 * t)
        width_taper = math.sin(math.pi * t) ** 0.35
        half_width = 0.00165 * width_taper
        vertices.extend((center + Vector((-half_width, 0.0, 0.0)), center + Vector((half_width, 0.0, 0.0))))
        u0 = 0.05 + (strip % 4) * 0.25
        uvs.extend(((u0, t), (u0 + 0.19, t)))
    for point_index in range(segments - 1):
        a = start + point_index * 2
        faces.append((a, a + 1, a + 3, a + 2))

under_mesh = bpy.data.meshes.new("AevryndFemaleNapeUnderlayerData_v249r13")
under_mesh.from_pydata(vertices, [], faces)
under_mesh.update()
uv_layer = under_mesh.uv_layers.new(name="UVMap")
for polygon in under_mesh.polygons:
    for loop_index in polygon.loop_indices:
        uv_layer.data[loop_index].uv = uvs[under_mesh.loops[loop_index].vertex_index]

material = bpy.data.materials["Aevrynd_HairRootShadow_v249r6"].copy()
material.name = "Aevrynd_NapeRootShadow_v249r13"
principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
principled.inputs["Base Color"].default_value = (0.010, 0.0032, 0.0018, 1.0)
principled.inputs["Roughness"].default_value = 0.88
principled.inputs["Specular IOR Level"].default_value = 0.10
under_mesh.materials.append(material)

under = bpy.data.objects.new(UNDERLAYER, under_mesh)
scene.collection.objects.link(under)
under.parent = rig
under.parent_type = "BONE"
under.parent_bone = "head"
under.matrix_world = bpy.data.objects["AevryndFemaleGuideBob_v249r12"].matrix_world.copy()
under["aevrynd_layer"] = "hair.nape.underlayer"
under["aevrynd_mainline_base"] = "v249"
under["aevrynd_candidate"] = "v249-mainline-hair-r13"
under["aevrynd_mainline_hair_collision"] = True
under["aevrynd_card_count"] = strips

scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r13"
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
print("AEVRYND_V249_MAINLINE_HAIR_R13=" + json.dumps({
    "output": str(OUTPUT),
    "cards": strips,
    "vertices": len(vertices),
    "faces": len(faces),
}, sort_keys=True))
