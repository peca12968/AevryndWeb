import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v15.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v16.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v16.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v16-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "hairline-v16"
RNG = random.Random(160916)


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def keep_outside(tree, point, clearance):
    location, normal, _, _ = tree.find_nearest(point)
    if location is None:
        return point
    if normal.dot(point - Vector((0.0, 0.0, 1.60))) < 0.0:
        normal.negate()
    signed = (point - location).dot(normal)
    return point + normal * max(0.0, clearance - signed)


def hairline_height(x):
    t = max(-1.0, min(1.0, x / 0.075))
    return 1.653 + 0.021 * abs(t) ** 1.55 + 0.0011 * math.sin(31.0 * x + 0.4)


def baby_hairs(body_tree):
    strands = []
    for index in range(84):
        t = index / 83 * 2.0 - 1.0
        x = t * 0.071 + RNG.uniform(-0.00045, 0.00045)
        z = hairline_height(x) + RNG.uniform(0.0005, 0.0045)
        location, normal, _, _ = body_tree.ray_cast(Vector((x, -0.34, z)), Vector((0.0, 1.0, 0.0)), 0.65)
        if location is None:
            continue
        if normal.dot(location - Vector((0.0, 0.0, 1.60))) < 0.0:
            normal.negate()
        root = location + normal * 0.00072
        length = RNG.uniform(0.0038, 0.0085) * (0.82 + 0.18 * abs(t))
        side = 1.0 if x >= 0.0 else -1.0
        direction = Vector((side * RNG.uniform(0.05, 0.20), 0.05, -1.0)).normalized()
        points = []
        for row in range(5):
            progress = row / 4
            curl = Vector((-side * 0.00045 * math.sin(math.pi * progress), 0.0, 0.0))
            points.append(keep_outside(body_tree, root + direction * length * progress + curl, 0.00068))
        strands.append((points, RNG.uniform(0.000070, 0.000105), 1 if index % 9 == 0 else 0))
    return strands


def parent_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def ribbon_mesh(name, strands, materials, rig, body_tree):
    vertices, faces, material_indices = [], [], []
    for points, width, material_index in strands:
        base = len(vertices)
        for row, point in enumerate(points):
            previous = points[max(0, row - 1)]
            following = points[min(len(points) - 1, row + 1)]
            tangent = (following - previous).normalized()
            _, normal, _, _ = body_tree.find_nearest(point)
            normal = normal or Vector((0.0, -1.0, 0.0))
            axis = tangent.cross(normal).normalized()
            progress = row / max(1, len(points) - 1)
            half_width = width * (1.0 - 0.82 * progress)
            vertices.extend((point - axis * half_width, point + axis * half_width))
        for row in range(len(points) - 1):
            a = base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
            material_indices.append(material_index)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj["aevrynd_role"] = "hairline_baby_hairs"
    obj["aevrynd_groom_revision"] = 16
    obj["aevrynd_strand_count"] = len(strands)
    obj["aevrynd_source"] = "Aevrynd procedural short hairline transition"
    parent_head(obj, rig)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = 82
    camera.location = location
    look_at(camera, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
for name in ("HairlineFine", "HairlineBaby"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

body_tree = world_tree(body)
materials = tuple(bpy.data.objects["HairMain"].data.materials)
strands = baby_hairs(body_tree)
hairline = ribbon_mesh("HairlineBaby", strands, materials, rig, body_tree)

for name, color, roughness in (
    ("Aevrynd_Hair_v11_Dark", (0.020, 0.0045, 0.0018, 1.0), 0.48),
    ("Aevrynd_Hair_v11_Warm", (0.050, 0.0120, 0.0048, 1.0), 0.44),
    ("Aevrynd_Hair_Scalp", (0.012, 0.0026, 0.0010, 1.0), 0.72),
):
    material = bpy.data.materials.get(name)
    if material and material.use_nodes:
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = roughness

for obj in bpy.data.objects:
    if obj.name.startswith("Hair"):
        obj["aevrynd_groom_revision"] = 16
bpy.context.scene["aevrynd_groom_revision"] = 16
bpy.context.scene["aevrynd_hairline_strategy"] = "short_transition_ribbons"
bpy.context.scene["aevrynd_rejected_oral_prototype"] = "requires mouth-slit retopology"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-hairline-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-hairline-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-hairline-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-hairline-close", (0.0, -0.49, 1.64), (0.0, -0.055, 1.64))

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_HAIRLINE_V16_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "removed_long_hairline_layer": "HairlineFine",
    "short_hairline_strands": len(strands),
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
