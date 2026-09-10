import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-shadow-r95.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-root-shadow-r95"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
CAP = "AevryndFemaleCC0RootShadow_v249r95"
MAX_ROOT_DISTANCE = 0.009
OFFSET = 0.00035


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
main = bpy.data.objects[MAIN]
roots = [main.matrix_world @ main.data.points[curve.first_point_index].position for curve in main.data.curves]
root_tree = KDTree(len(roots))
for index, root in enumerate(roots):
    root_tree.insert(root, index)
root_tree.balance()

body = bpy.data.objects[BODY]
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
world_rotation = evaluated.matrix_world.to_3x3()
world_vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
world_normals = [(world_rotation @ vertex.normal).normalized() for vertex in mesh.vertices]
selected = []
for polygon in mesh.polygons:
    center = evaluated.matrix_world @ polygon.center
    nearest = root_tree.find(center)
    if nearest is None or nearest[2] > MAX_ROOT_DISTANCE or center.z < 1.575:
        continue
    normal = (world_rotation @ polygon.normal).normalized()
    if normal.z < -0.30:
        continue
    selected.append(tuple(polygon.vertices))
used = sorted({index for polygon in selected for index in polygon})
remap = {old: new for new, old in enumerate(used)}
vertices = [world_vertices[index] + world_normals[index] * OFFSET for index in used]
faces = [tuple(remap[index] for index in polygon) for polygon in selected]
evaluated.to_mesh_clear()

data = bpy.data.meshes.new(CAP + "Data")
data.from_pydata(vertices, [], faces)
data.update()
material = bpy.data.materials.get("AevryndCC0RootShadow_v249r95") or bpy.data.materials.new("AevryndCC0RootShadow_v249r95")
material.use_nodes = True
bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (0.018, 0.0045, 0.0022, 1.0)
bsdf.inputs["Roughness"].default_value = 0.88
bsdf.inputs["Specular IOR Level"].default_value = 0.16
data.materials.append(material)
cap = bpy.data.objects.new(CAP, data)
scene.collection.objects.link(cap)
rig = bpy.data.objects["AevryndFemaleRig"]
cap.parent = rig
cap.parent_type = "BONE"
cap.parent_bone = "head"
cap.matrix_world = Matrix.Identity(4)
cap["aevrynd_layer"] = "hair.scalp.root-shadow"
cap["aevrynd_revision"] = "v249-mainline-cc0-root-shadow-r95"
cap["aevrynd_runtime_dependency"] = "none"
cap["aevrynd_source"] = "Aevrynd body scalp faces selected by baked CC0 hair roots"
for name in ("AevryndFemaleScalpCoverage_v378", "AevryndFemaleScalpPart_v249r25"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-root-shadow-r95"
scene["aevrynd_release_state"] = "R95_ROOT_SHADOW_VISUAL_AND_COLLISION_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {"source": str(SOURCE), "output": str(OUTPUT), "layer": "hair.scalp.root-shadow",
          "vertices": len(vertices), "faces": len(faces), "maximumRootDistanceM": MAX_ROOT_DISTANCE,
          "surfaceOffsetM": OFFSET, "status": "VISUAL_AND_COLLISION_REVIEW_REQUIRED"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_ROOT_SHADOW_R95=" + json.dumps(report, sort_keys=True))
