import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v13.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v14.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v14.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v14-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "groom-v14"
RNG = random.Random(614208)


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def surface_hit(tree, origin, direction, distance=0.65):
    location, normal, _, _ = tree.ray_cast(origin, direction.normalized(), distance)
    if location is None:
        return None
    if normal.dot(location - Vector((0.0, 0.0, 1.60))) < 0.0:
        normal.negate()
    return location, normal.normalized()


def keep_outside(tree, point, clearance):
    location, normal, _, _ = tree.find_nearest(point)
    if location is None:
        return point
    if normal.dot(point - Vector((0.0, 0.0, 1.60))) < 0.0:
        normal.negate()
    signed = (point - location).dot(normal)
    return point + normal * max(0.0, clearance - signed)


def parent_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def ribbon_mesh(name, strands, materials, rig, role, body_tree):
    vertices = []
    faces = []
    face_materials = []
    for points, width, material_index in strands:
        base = len(vertices)
        for row, point in enumerate(points):
            previous = points[max(0, row - 1)]
            following = points[min(len(points) - 1, row + 1)]
            tangent = (following - previous).normalized()
            _, normal, _, _ = body_tree.find_nearest(point)
            if normal is None:
                normal = Vector((0.0, 0.0, 1.0))
            axis = tangent.cross(normal).normalized()
            progress = row / max(1, len(points) - 1)
            half_width = width * (0.72 + 0.28 * math.sin(math.pi * progress)) * (1.0 - 0.72 * progress)
            vertices.extend((point - axis * half_width, point + axis * half_width))
        for row in range(len(points) - 1):
            a = base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
            face_materials.append(material_index)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for material in materials:
        obj.data.materials.append(material)
    for polygon, material_index in zip(obj.data.polygons, face_materials):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj["aevrynd_role"] = role
    obj["aevrynd_groom_revision"] = 14
    obj["aevrynd_clump_count"] = len(strands)
    obj["aevrynd_source"] = "Aevrynd directed transition clumps"
    parent_head(obj, rig)
    return obj


def follow_surface(tree, root, desired, length, rows, variation):
    points = [root]
    point = root.copy()
    for row in range(1, rows):
        progress = row / (rows - 1)
        _, normal, _, _ = tree.find_nearest(point)
        if normal is None:
            normal = Vector((0.0, 0.0, 1.0))
        if normal.dot(point - Vector((0.0, 0.0, 1.60))) < 0.0:
            normal.negate()
        direction = desired + Vector((variation * 0.035, math.sin(variation * 3.0) * 0.025, 0.0))
        tangent = direction - normal * direction.dot(normal)
        tangent.normalize()
        point = point + tangent * length / (rows - 1)
        point += normal * 0.00012 * math.sin(math.pi * progress)
        point = keep_outside(tree, point, 0.00125)
        points.append(point.copy())
    return points


def transition_clumps(tree):
    temples = []
    for side in (-1.0, 1.0):
        for index in range(30):
            fraction = index / 29
            y = -0.040 + 0.092 * fraction + RNG.uniform(-0.0013, 0.0013)
            z = 1.646 - 0.025 * fraction + RNG.uniform(-0.0015, 0.0015)
            hit = surface_hit(tree, Vector((side * 0.34, y, z)), Vector((-side, 0.0, 0.0)))
            if not hit:
                continue
            root, normal = hit
            root += normal * 0.00135
            length = RNG.uniform(0.020, 0.043)
            desired = Vector((-side * 0.015, 0.18 + 0.10 * fraction, -0.97))
            points = follow_surface(tree, root, desired, length, 11, RNG.uniform(-1.0, 1.0))
            temples.append((points, RNG.uniform(0.000095, 0.000165), index % 7 == 0))

    nape = []
    for index in range(46):
        t = index / 45 * 2.0 - 1.0
        x = t * 0.066 + RNG.uniform(-0.0012, 0.0012)
        z = 1.576 + 0.020 * abs(t) ** 1.45 + RNG.uniform(-0.0015, 0.0015)
        hit = surface_hit(tree, Vector((x, 0.34, z)), Vector((0.0, -1.0, 0.0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.00135
        desired = Vector((0.12 * t, 0.08, -0.99))
        points = follow_surface(tree, root, desired, RNG.uniform(0.026, 0.048), 11, RNG.uniform(-1.0, 1.0))
        nape.append((points, RNG.uniform(0.000090, 0.000155), index % 8 == 0))
    return temples, nape


def downsample_strands(obj, stride, keep_every):
    old = obj.data
    keep = set()
    count = 0
    for strand, start in enumerate(range(0, len(old.vertices), stride)):
        if start + stride > len(old.vertices):
            break
        if strand % keep_every == 0:
            keep.update(range(start, start + stride))
            count += 1
    ordered = sorted(keep)
    remap = {old_index: new_index for new_index, old_index in enumerate(ordered)}
    vertices = [old.vertices[index].co.copy() for index in ordered]
    selected = [polygon for polygon in old.polygons if all(index in remap for index in polygon.vertices)]
    faces = [tuple(remap[index] for index in polygon.vertices) for polygon in selected]
    material_indices = [polygon.material_index for polygon in selected]
    mesh = bpy.data.meshes.new(old.name + "LODAdjusted")
    mesh.from_pydata(vertices, [], faces)
    for material in old.materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj.data = mesh
    bpy.data.meshes.remove(old)
    obj["aevrynd_strand_count"] = count
    obj["aevrynd_groom_revision"] = 14
    return count


def remove_body_intersections(obj, body):
    body_tree = world_tree(body)
    object_tree = world_tree(obj)
    doomed = {pair[1] for pair in body_tree.overlap(object_tree)}
    if not doomed:
        return 0
    old = obj.data
    vertices = [vertex.co.copy() for vertex in old.vertices]
    kept = [polygon for polygon in old.polygons if polygon.index not in doomed]
    faces = [tuple(polygon.vertices) for polygon in kept]
    material_indices = [polygon.material_index for polygon in kept]
    mesh = bpy.data.meshes.new(old.name + "CollisionClean")
    mesh.from_pydata(vertices, [], faces)
    for material in old.materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj.data = mesh
    bpy.data.meshes.remove(old)
    obj["aevrynd_removed_body_intersection_faces"] = len(doomed)
    return len(doomed)


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
for name in ("HairTempleClumps", "HairNapeClumps"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

body_tree = world_tree(body)
materials = tuple(bpy.data.objects["HairMain"].data.materials)
hairline_count = downsample_strands(bpy.data.objects["HairlineFine"], 21, 2)
temple_data, nape_data = transition_clumps(body_tree)
temples = ribbon_mesh("HairTempleClumps", temple_data, materials, rig, "hair_temple_clumps", body_tree)
nape = ribbon_mesh("HairNapeClumps", nape_data, materials, rig, "hair_nape_clumps", body_tree)
for obj in bpy.data.objects:
    if obj.name.startswith("Hair"):
        obj["aevrynd_groom_revision"] = 14
removed = {obj.name: remove_body_intersections(obj, body) for obj in (temples, nape)}

bpy.context.scene["aevrynd_runtime_lod_revision"] = 14
bpy.context.scene["aevrynd_lod1_excluded_layers"] = "HairMain,HairlineFine,HairFlyaways"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-groom-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-groom-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-groom-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-groom-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairlineFine", "HairFlyaways"})
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_GROOM_V14_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "hairline_strands": hairline_count,
    "temple_clumps": len(temple_data),
    "nape_clumps": len(nape_data),
    "removed_body_intersection_faces": removed,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
