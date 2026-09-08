import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v42.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v43.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v43.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v43-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "hairline-v43"
RNG = random.Random(43017)


def hairline_height(x):
    t = max(-1.0, min(1.0, x / 0.075))
    return 1.653 + 0.021 * abs(t) ** 1.55 + 0.0011 * math.sin(31.0 * x + 0.4)


def forehead_violation(point, margin=0.010):
    return point.y < -0.035 and abs(point.x) < 0.10 and point.z < hairline_height(point.x) + margin


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def rebuild_mesh(obj, removed_vertices, suffix):
    old = obj.data
    kept = [index for index in range(len(old.vertices)) if index not in removed_vertices]
    mapping = {old_index: new_index for new_index, old_index in enumerate(kept)}
    vertices = [old.vertices[index].co.copy() for index in kept]
    faces, material_indices, smooth = [], [], []
    for polygon in old.polygons:
        if any(index in removed_vertices for index in polygon.vertices):
            continue
        faces.append(tuple(mapping[index] for index in polygon.vertices))
        material_indices.append(polygon.material_index)
        smooth.append(polygon.use_smooth)
    mesh = bpy.data.meshes.new(obj.name + suffix)
    mesh.from_pydata(vertices, [], faces)
    for material in old.materials:
        mesh.materials.append(material)
    for polygon, material_index, use_smooth in zip(mesh.polygons, material_indices, smooth):
        polygon.material_index = material_index
        polygon.use_smooth = use_smooth
    if old.uv_layers and faces:
        # Hair fiber meshes do not require UVs; card meshes are rebuilt separately below.
        pass
    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)


def prune_fibers(obj, stride, sides):
    removed = set()
    count = 0
    for start in range(0, len(obj.data.vertices) - stride + 1, stride):
        points = [
            sum((obj.matrix_world @ obj.data.vertices[start + row * sides + side].co for side in range(sides)), Vector()) / sides
            for row in range(stride // sides)
        ]
        if any(forehead_violation(point) for point in points):
            removed.update(range(start, start + stride))
            count += 1
    rebuild_mesh(obj, removed, "MeshV43")
    obj["aevrynd_removed_forehead_fibers"] = count
    obj["aevrynd_groom_revision"] = 43
    return count


def prune_card_components(obj):
    mesh = obj.data
    parent = list(range(len(mesh.vertices)))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        first, second = find(first), find(second)
        if first != second:
            parent[second] = first

    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for vertex in vertices[1:]:
            union(vertices[0], vertex)
    bad_roots = {
        find(vertex.index)
        for vertex in mesh.vertices
        if forehead_violation(obj.matrix_world @ vertex.co)
    }
    removed = {vertex.index for vertex in mesh.vertices if find(vertex.index) in bad_roots}
    removed_components = len(bad_roots)

    old = obj.data
    kept = [index for index in range(len(old.vertices)) if index not in removed]
    mapping = {old_index: new_index for new_index, old_index in enumerate(kept)}
    vertices = [old.vertices[index].co.copy() for index in kept]
    faces, face_sources = [], []
    for polygon in old.polygons:
        if any(index in removed for index in polygon.vertices):
            continue
        faces.append(tuple(mapping[index] for index in polygon.vertices))
        face_sources.append(polygon)
    new = bpy.data.meshes.new(obj.name + "MeshV43")
    new.from_pydata(vertices, [], faces)
    for material in old.materials:
        new.materials.append(material)
    uv = new.uv_layers.new(name="UVMap")
    old_uv = old.uv_layers.active
    for new_polygon, old_polygon in zip(new.polygons, face_sources):
        new_polygon.use_smooth = old_polygon.use_smooth
        new_polygon.material_index = old_polygon.material_index
        for new_loop, old_loop_index in zip(new_polygon.loop_indices, old_polygon.loop_indices):
            uv.data[new_loop].uv = old_uv.data[old_loop_index].uv
    obj.data = new
    if old.users == 0:
        bpy.data.meshes.remove(old)
    obj["aevrynd_removed_forehead_cards"] = removed_components
    obj["aevrynd_clump_count"] = int(obj.get("aevrynd_clump_count", 0)) - removed_components
    obj["aevrynd_groom_revision"] = 43
    return removed_components


def keep_outside(tree, point, clearance):
    location, normal, _, _ = tree.find_nearest(point)
    if location is None:
        return point
    if normal.dot(point - Vector((0.0, 0.0, 1.60))) < 0.0:
        normal.negate()
    signed = (point - location).dot(normal)
    return point + normal * max(0.0, clearance - signed)


def build_baby_hairs(body, rig):
    old = bpy.data.objects.get("HairlineBaby")
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    tree = evaluated_tree(body)
    strands = []
    count = 90
    samples = sorted(RNG.uniform(-1.0, 1.0) for _ in range(count))
    for index, t in enumerate(samples):
        x = 0.0735 * math.copysign(abs(t) ** 1.08, t) + RNG.uniform(-0.00075, 0.00075)
        z = hairline_height(x) + RNG.uniform(0.0012, 0.0064)
        location, normal, _, _ = tree.ray_cast(Vector((x, -0.34, z)), Vector((0.0, 1.0, 0.0)), 0.65)
        if location is None:
            continue
        if normal.dot(location - Vector((0.0, 0.0, 1.60))) < 0.0:
            normal.negate()
        root = location + normal * 0.00086
        temple = min(1.0, abs(t) ** 1.45)
        length = RNG.uniform(0.0013, 0.0037) + temple * RNG.uniform(0.0002, 0.0010)
        side = 1.0 if x >= 0.0 else -1.0
        lateral = side * RNG.uniform(0.08, 0.58) * (0.35 + 0.65 * temple)
        vertical = -RNG.uniform(0.72, 1.0) if RNG.random() < 0.78 else -RNG.uniform(0.30, 0.62)
        direction = Vector((lateral, RNG.uniform(0.010, 0.080), vertical)).normalized()
        rows = 5
        points = []
        phase = RNG.uniform(-0.5, 0.5)
        for row in range(rows):
            progress = row / (rows - 1)
            bend = Vector((-side * (0.00010 + 0.00028 * temple) * math.sin(math.pi * progress + phase), 0.0, 0.0))
            points.append(keep_outside(tree, root + direction * length * progress + bend, 0.00078))
        strands.append((points, RNG.uniform(0.000032, 0.000064), 1 if RNG.random() < 0.12 else 0))

    vertices, faces, material_indices = [], [], []
    for points, width, material_index in strands:
        base = len(vertices)
        for row, point in enumerate(points):
            previous = points[max(0, row - 1)]
            following = points[min(len(points) - 1, row + 1)]
            tangent = (following - previous).normalized()
            _, normal, _, _ = tree.find_nearest(point)
            normal = normal or Vector((0.0, -1.0, 0.0))
            axis = tangent.cross(normal)
            if axis.length < 1e-8:
                axis = Vector((1.0, 0.0, 0.0))
            axis.normalize()
            progress = row / (len(points) - 1)
            half_width = width * (1.0 - 0.88 * progress)
            vertices.extend((point - axis * half_width, point + axis * half_width))
        for row in range(len(points) - 1):
            a = base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
            material_indices.append(material_index)
    mesh = bpy.data.meshes.new("HairlineBabyMeshV43")
    mesh.from_pydata(vertices, [], faces)
    for material in bpy.data.objects["HairMain"].data.materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj = bpy.data.objects.new("HairlineBaby", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "hairline_baby_hairs"
    obj["aevrynd_groom_revision"] = 43
    obj["aevrynd_strand_count"] = len(strands)
    obj["aevrynd_source"] = "Aevrynd irregular collision-safe short hairline transition"
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return len(strands)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=82):
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
removed_fibers = {
    name: prune_fibers(bpy.data.objects[name], stride, sides)
    for name, stride, sides in (("HairMain", 27, 3), ("HairGuides", 24, 3), ("HairFlyaways", 27, 3))
}
removed_cards = {name: prune_card_components(bpy.data.objects[name]) for name in ("HairClumpsLarge", "HairClumpsMediumCards")}
baby_count = build_baby_hairs(body, rig)
bpy.context.scene["aevrynd_hair_revision"] = 43
bpy.context.scene["aevrynd_hairline_strategy"] = "irregular_short_transition_with_forehead_exclusion"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
for name, location, target, lens in (
    ("female-hairline-close", (0.0, -0.49, 1.665), (0.0, -0.055, 1.665), 112),
    ("female-hairline-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 82),
    ("female-hairline-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 82),
    ("female-hairline-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545), 82),
    ("female-hairline-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545), 82),
    ("female-hairline-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545), 82),
):
    render(camera, name, location, target, lens)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export(BUILD, rig)
export(LOD1, rig, {"HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards"})
multires.levels, multires.sculpt_levels, multires.render_levels = levels
print("AEVRYND_HAIRLINE_V43_REPORT=" + json.dumps({"state": "AUTHORING", "removed_forehead_fibers": removed_fibers, "removed_forehead_cards": removed_cards, "baby_hairs": baby_count, "runtime_glb": str(BUILD), "lod1_glb": str(LOD1)}))
