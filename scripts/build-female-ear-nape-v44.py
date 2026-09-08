import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v43.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v44.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v44.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v44-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "ear-nape-v44"
RNG = random.Random(44018)


def tail_violation(point):
    rear = point.y > 0.020 and abs(point.x) < 0.105 and point.z < 1.590
    ear = abs(point.x) > 0.075 and point.z < 1.610 and -0.055 < point.y < 0.075
    return rear or ear


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def prune_fibers(obj, stride, sides):
    removed = set()
    count = 0
    for start in range(0, len(obj.data.vertices) - stride + 1, stride):
        points = [sum((obj.matrix_world @ obj.data.vertices[start + row * sides + side].co for side in range(sides)), Vector()) / sides for row in range(stride // sides)]
        if any(tail_violation(point) for point in points):
            removed.update(range(start, start + stride))
            count += 1
    old = obj.data
    kept = [index for index in range(len(old.vertices)) if index not in removed]
    mapping = {old_index: new_index for new_index, old_index in enumerate(kept)}
    vertices = [old.vertices[index].co.copy() for index in kept]
    polygons = [polygon for polygon in old.polygons if all(index not in removed for index in polygon.vertices)]
    faces = [tuple(mapping[index] for index in polygon.vertices) for polygon in polygons]
    mesh = bpy.data.meshes.new(obj.name + "MeshV44")
    mesh.from_pydata(vertices, [], faces)
    for material in old.materials:
        mesh.materials.append(material)
    for target, source in zip(mesh.polygons, polygons):
        target.material_index = source.material_index
        target.use_smooth = source.use_smooth
    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)
    obj["aevrynd_removed_ear_nape_fibers"] = count
    obj["aevrynd_groom_revision"] = 44
    return count


def prune_card_components(obj):
    old = obj.data
    parent = list(range(len(old.vertices)))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        first, second = find(first), find(second)
        if first != second:
            parent[second] = first

    for polygon in old.polygons:
        indices = list(polygon.vertices)
        for index in indices[1:]:
            union(indices[0], index)
    bad = {find(vertex.index) for vertex in old.vertices if tail_violation(obj.matrix_world @ vertex.co)}
    removed = {vertex.index for vertex in old.vertices if find(vertex.index) in bad}
    kept = [index for index in range(len(old.vertices)) if index not in removed]
    mapping = {old_index: new_index for new_index, old_index in enumerate(kept)}
    vertices = [old.vertices[index].co.copy() for index in kept]
    sources = [polygon for polygon in old.polygons if all(index not in removed for index in polygon.vertices)]
    faces = [tuple(mapping[index] for index in polygon.vertices) for polygon in sources]
    mesh = bpy.data.meshes.new(obj.name + "MeshV44")
    mesh.from_pydata(vertices, [], faces)
    for material in old.materials:
        mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="UVMap")
    old_uv = old.uv_layers.active
    for target, source in zip(mesh.polygons, sources):
        target.material_index = source.material_index
        target.use_smooth = source.use_smooth
        for target_loop, source_loop in zip(target.loop_indices, source.loop_indices):
            uv.data[target_loop].uv = old_uv.data[source_loop].uv
    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)
    obj["aevrynd_removed_ear_nape_cards"] = len(bad)
    obj["aevrynd_clump_count"] = int(obj.get("aevrynd_clump_count", 0)) - len(bad)
    obj["aevrynd_groom_revision"] = 44
    return len(bad)


def outward_normal(normal, point):
    normal = normal.normalized()
    if normal.dot(point - Vector((0.0, 0.0, 1.60))) < 0.0:
        normal.negate()
    return normal


def keep_outside(tree, point, clearance):
    location, normal, _, _ = tree.find_nearest(point)
    if location is None:
        return point
    normal = outward_normal(normal, point)
    signed = (point - location).dot(normal)
    return point + normal * max(0.0, clearance - signed)


def surface_hit(tree, origin, direction):
    location, normal, _, _ = tree.ray_cast(origin, direction.normalized(), 0.65)
    if location is None:
        return None
    return location, outward_normal(normal, location)


def follow_surface(tree, root, desired, length, rows, clearance, curl):
    points = [keep_outside(tree, root, clearance)]
    point = points[0]
    for row in range(1, rows):
        t = row / (rows - 1)
        location, normal, _, _ = tree.find_nearest(point)
        normal = outward_normal(normal, point)
        direction = desired + Vector((curl * math.sin(math.pi * t), curl * 0.35 * math.sin(math.tau * t), 0.0))
        tangent = direction - normal * direction.dot(normal)
        if tangent.length < 1e-8:
            tangent = Vector((0.0, 0.0, -1.0))
        tangent.normalize()
        point = point + tangent * length / (rows - 1)
        point = keep_outside(tree, point, clearance + 0.00018 * math.sin(math.pi * t))
        points.append(point.copy())
    return points


def build_transition_data(tree):
    temples = []
    for side in (-1.0, 1.0):
        samples = sorted(RNG.random() for _ in range(23))
        for index, u in enumerate(samples):
            y = -0.047 + 0.105 * u + RNG.uniform(-0.0015, 0.0015)
            z = 1.657 - 0.030 * u + RNG.uniform(-0.0022, 0.0022)
            hit = surface_hit(tree, Vector((side * 0.34, y, z)), Vector((-side, 0.0, 0.0)))
            if not hit:
                continue
            root, normal = hit
            root += normal * 0.00145
            length = RNG.uniform(0.0050, 0.0145) + 0.0030 * u
            desired = Vector((-side * RNG.uniform(0.02, 0.14), RNG.uniform(0.08, 0.30), -1.0))
            points = follow_surface(tree, root, desired, length, 7, 0.00135, side * RNG.uniform(-0.08, 0.08))
            temples.append((points, RNG.uniform(0.000045, 0.000090), 1 if RNG.random() < 0.13 else 0))

    nape = []
    samples = sorted(RNG.uniform(-1.0, 1.0) for _ in range(38))
    for t in samples:
        x = 0.068 * math.copysign(abs(t) ** 1.10, t) + RNG.uniform(-0.0011, 0.0011)
        z = 1.592 + 0.017 * abs(t) ** 1.55 + RNG.uniform(-0.0020, 0.0020)
        hit = surface_hit(tree, Vector((x, 0.34, z)), Vector((0.0, -1.0, 0.0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.00155
        length = RNG.uniform(0.0050, 0.0135) + 0.0030 * (1.0 - abs(t))
        desired = Vector((RNG.uniform(0.04, 0.22) * t, RNG.uniform(0.03, 0.14), -1.0))
        points = follow_surface(tree, root, desired, length, 7, 0.00148, RNG.uniform(-0.07, 0.07))
        nape.append((points, RNG.uniform(0.000040, 0.000082), 1 if RNG.random() < 0.12 else 0))

    boundary = []
    samples = sorted(RNG.uniform(-1.0, 1.0) for _ in range(30))
    for t in samples:
        x = 0.071 * t + RNG.uniform(-0.0010, 0.0010)
        z = 1.606 + 0.016 * abs(t) ** 1.35 + RNG.uniform(-0.0018, 0.0018)
        hit = surface_hit(tree, Vector((x, 0.34, z)), Vector((0.0, -1.0, 0.0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.00118
        length = RNG.uniform(0.0040, 0.0095)
        desired = Vector((RNG.uniform(0.03, 0.18) * t, RNG.uniform(0.05, 0.17), -1.0))
        points = follow_surface(tree, root, desired, length, 6, 0.00110, RNG.uniform(-0.06, 0.06))
        boundary.append((points, RNG.uniform(0.000080, 0.000155), 1 if RNG.random() < 0.10 else 0))
    return temples, nape, boundary


def ribbon_mesh(name, strands, materials, rig, role, tree):
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    vertices, faces, material_indices = [], [], []
    for points, width, material_index in strands:
        base = len(vertices)
        for row, point in enumerate(points):
            previous = points[max(0, row - 1)]
            following = points[min(len(points) - 1, row + 1)]
            tangent = (following - previous).normalized()
            _, normal, _, _ = tree.find_nearest(point)
            normal = outward_normal(normal, point)
            axis = tangent.cross(normal)
            if axis.length < 1e-8:
                axis = Vector((1.0, 0.0, 0.0))
            axis.normalize()
            t = row / (len(points) - 1)
            half_width = width * (0.82 + 0.18 * math.sin(math.pi * t)) * (1.0 - 0.90 * t)
            vertices.extend((point - axis * half_width, point + axis * half_width))
        for row in range(len(points) - 1):
            a = base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
            material_indices.append(material_index)
    mesh = bpy.data.meshes.new(name + "MeshV44")
    mesh.from_pydata(vertices, [], faces)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = role
    obj["aevrynd_groom_revision"] = 44
    obj["aevrynd_clump_count"] = len(strands)
    obj["aevrynd_source"] = "Aevrynd collision-safe staggered short-hair transition"
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=88):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


def export(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True, export_yup=True, export_extras=True, export_animations=True, export_frame_range=True, export_attributes=True, export_vertex_color="ACTIVE")


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
tree = evaluated_tree(body)
removed_fibers = {name: prune_fibers(bpy.data.objects[name], stride, sides) for name, stride, sides in (("HairMain", 27, 3), ("HairGuides", 24, 3), ("HairFlyaways", 27, 3))}
removed_cards = {name: prune_card_components(bpy.data.objects[name]) for name in ("HairClumpsLarge", "HairClumpsMediumCards")}
materials = tuple(bpy.data.objects["HairMain"].data.materials)
temple_data, nape_data, boundary_data = build_transition_data(tree)
temples = ribbon_mesh("HairTempleClumps", temple_data, materials, rig, "hair_temple_clumps", tree)
nape = ribbon_mesh("HairNapeClumps", nape_data, materials, rig, "hair_nape_clumps", tree)
boundary = ribbon_mesh("HairBoundaryClumps", boundary_data, materials, rig, "hair_boundary_clumps", tree)
bpy.context.scene["aevrynd_hair_revision"] = 44
bpy.context.scene["aevrynd_boundary_strategy"] = "staggered_short_tapered_transition"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
for name, location, target in (
    ("female-ear-nape-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555)),
    ("female-ear-nape-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55)),
    ("female-ear-nape-left", (-0.66, -0.05, 1.60), (0.0, 0.0, 1.57)),
    ("female-ear-nape-right", (0.66, -0.05, 1.60), (0.0, 0.0, 1.57)),
    ("female-ear-nape-back", (0.0, 0.76, 1.60), (0.0, 0.01, 1.57)),
):
    render(camera, name, location, target)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export(BUILD, rig)
export(LOD1, rig, {"HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards", "HairlineBaby", "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps", "HairUndercutScalp"})
multires.levels, multires.sculpt_levels, multires.render_levels = levels
print("AEVRYND_EAR_NAPE_V44_REPORT=" + json.dumps({"state": "AUTHORING", "removed_ear_nape_fibers": removed_fibers, "removed_ear_nape_cards": removed_cards, "temple_clumps": len(temple_data), "nape_clumps": len(nape_data), "boundary_clumps": len(boundary_data), "runtime_glb": str(BUILD), "lod1_glb": str(LOD1)}))
