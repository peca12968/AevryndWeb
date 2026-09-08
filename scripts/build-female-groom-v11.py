import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v10.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v11.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v11.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "groom-v11"
RNG = random.Random(611208)


def world_surface(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def surface_hit(tree, origin, direction, distance=0.55):
    location, normal, _, _ = tree.ray_cast(origin, direction.normalized(), distance)
    if location is None:
        return None
    center = Vector((0.0, 0.0, 1.60))
    if normal.dot(location - center) < 0.0:
        normal.negate()
    return location, normal.normalized()


def keep_outside(tree, point, clearance):
    location, normal, _, _ = tree.find_nearest(point)
    if location is None:
        return point
    center = Vector((0.0, 0.0, 1.60))
    if normal.dot(location - center) < 0.0:
        normal.negate()
    signed = (point - location).dot(normal)
    if signed < clearance:
        return point + normal * (clearance - signed)
    return point


def groom_material(name, color, roughness):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.10
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.30
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.0
    return result


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def tube_mesh(name, strands, materials, rig, role, sides=3):
    vertices = []
    faces = []
    face_materials = []
    for strand_index, (points, root_radius, material_index) in enumerate(strands):
        base = len(vertices)
        for row, point in enumerate(points):
            previous = points[max(0, row - 1)]
            following = points[min(len(points) - 1, row + 1)]
            tangent = (following - previous).normalized()
            reference = Vector((0.0, 0.0, 1.0)) if abs(tangent.z) < 0.88 else Vector((1.0, 0.0, 0.0))
            axis_a = tangent.cross(reference).normalized()
            axis_b = tangent.cross(axis_a).normalized()
            progress = row / max(1, len(points) - 1)
            radius = root_radius * ((1.0 - progress) ** 0.72) + 0.000018
            for side in range(sides):
                angle = side / sides * math.tau
                vertices.append(point + axis_a * math.cos(angle) * radius + axis_b * math.sin(angle) * radius)
        for row in range(len(points) - 1):
            for side in range(sides):
                a = base + row * sides + side
                b = base + row * sides + (side + 1) % sides
                c = base + (row + 1) * sides + (side + 1) % sides
                d = base + (row + 1) * sides + side
                faces.append((a, b, c, d))
                face_materials.append(material_index)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for value in materials:
        obj.data.materials.append(value)
    for polygon, material_index in zip(obj.data.polygons, face_materials):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj["aevrynd_role"] = role
    obj["aevrynd_groom_revision"] = 11
    obj["aevrynd_strand_count"] = len(strands)
    obj["aevrynd_source"] = "Aevrynd procedural scalp-flow groom"
    parent_to_head(obj, rig)
    return obj


def flow_strand(tree, root, normal, length, region, variation):
    part_x = -0.015
    side = 1.0 if root.x >= part_x else -1.0
    if region == "front":
        desired = Vector((side * 0.84, 0.10, -0.22))
    elif region == "back":
        desired = Vector((side * 0.16, 0.48, -0.78))
    else:
        desired = Vector((side * 0.52, root.y * 1.7, -0.54))
    desired += Vector((variation * 0.18, math.sin(variation * 2.3) * 0.10, variation * 0.05))
    tangent = desired - normal * desired.dot(normal)
    if tangent.length < 1e-6:
        tangent = Vector((side, 0.0, -0.2))
    tangent.normalize()
    points = []
    for row in range(9):
        progress = row / 8
        point = root + tangent * length * progress
        point += normal * (0.0022 * math.sin(math.pi * progress))
        point.z -= 0.0045 * progress * progress
        point.x += math.sin(progress * math.pi * 1.3 + variation * 5.0) * 0.0009 * progress
        point = keep_outside(tree, point, 0.0017 if row < 3 else 0.00115)
        points.append(point)
    return points


def build_primary(tree):
    center = Vector((0.0, -0.012, 1.625))
    strands = []
    roots = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    attempts = 2400
    for index in range(attempts):
        fraction = (index + 0.5) / attempts
        cos_theta = 1.0 - fraction * 1.24
        theta = math.acos(max(-1.0, min(1.0, cos_theta)))
        phi = index * golden
        direction = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
        hit = surface_hit(tree, center, direction)
        if not hit:
            continue
        root, normal = hit
        front_limit = 1.654 + 0.018 * min(1.0, abs(root.x) / 0.075) ** 1.6
        if root.y < -0.020 and root.z < front_limit:
            continue
        if root.y >= -0.020 and root.y < 0.040 and root.z < 1.615:
            continue
        if root.y >= 0.040 and root.z < 1.575:
            continue
        root += normal * 0.00175
        roots.append(root)
        region = "front" if root.y < -0.035 else "back" if root.y > 0.035 else "crown"
        length = {
            "front": RNG.uniform(0.028, 0.050),
            "back": RNG.uniform(0.036, 0.060),
            "crown": RNG.uniform(0.032, 0.055),
        }[region]
        variation = RNG.uniform(-1.0, 1.0)
        points = flow_strand(tree, root, normal, length, region, variation)
        radius = RNG.uniform(0.000105, 0.000155)
        material_index = 0 if (index * 17) % 7 else 1
        strands.append((points, radius, material_index))
    return strands, roots


def front_and_nape(tree):
    strands = []
    for index in range(420):
        t = index / 419 * 2.0 - 1.0
        x = t * 0.074 + RNG.uniform(-0.00065, 0.00065)
        z = 1.655 + 0.018 * abs(t) ** 1.6 + RNG.uniform(-0.0010, 0.0010)
        hit = surface_hit(tree, Vector((x, -0.35, z)), Vector((0.0, 1.0, 0.0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.00085
        side = 1.0 if x > -0.015 else -1.0
        length = RNG.uniform(0.007, 0.016)
        direction = (Vector((side * 0.22, 0.06, -0.94)) + normal * 0.08).normalized()
        points = [keep_outside(tree, root + direction * length * row / 4, 0.00075) for row in range(5)]
        strands.append((points, RNG.uniform(0.000055, 0.000085), index % 9 == 0))
    for index in range(190):
        t = index / 189 * 2.0 - 1.0
        x = t * 0.067 + RNG.uniform(-0.0006, 0.0006)
        z = 1.574 + 0.023 * abs(t) ** 1.5 + RNG.uniform(-0.0010, 0.0010)
        hit = surface_hit(tree, Vector((x, 0.34, z)), Vector((0.0, -1.0, 0.0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.0009
        side = 1.0 if x >= 0.0 else -1.0
        length = RNG.uniform(0.010, 0.024)
        direction = (Vector((side * 0.16, 0.08, -0.94)) + normal * 0.06).normalized()
        points = [keep_outside(tree, root + direction * length * row / 4, 0.0008) for row in range(5)]
        strands.append((points, RNG.uniform(0.00005, 0.000078), index % 11 == 0))
    # Fine sideburns bridge the dense scalp cap into the ear and temple instead
    # of leaving a hard polygon boundary above the ear.
    for side in (-1.0, 1.0):
        for index in range(110):
            fraction = index / 109
            y = -0.052 + fraction * 0.080 + RNG.uniform(-0.0012, 0.0012)
            z = 1.655 - fraction * 0.061 + RNG.uniform(-0.0011, 0.0011)
            hit = surface_hit(tree, Vector((side * 0.34, y, z)), Vector((-side, 0.0, 0.0)))
            if not hit:
                continue
            root, normal = hit
            root += normal * 0.00085
            length = RNG.uniform(0.008, 0.021)
            direction = (Vector((side * 0.05, 0.05, -0.96)) + normal * 0.06).normalized()
            points = [keep_outside(tree, root + direction * length * row / 4, 0.0008) for row in range(5)]
            strands.append((points, RNG.uniform(0.000048, 0.000074), index % 13 == 0))
    return strands


def flyaways(primary):
    strands = []
    for index in range(52):
        source, _, material_index = primary[(index * 31) % len(primary)]
        points = []
        for row, point in enumerate(source):
            progress = row / (len(source) - 1)
            offset = Vector((
                math.sin(index * 1.77 + progress * 4.0),
                math.cos(index * 1.13 + progress * 3.1),
                0.35 + math.sin(index * 0.71 + progress * 5.0),
            )) * (0.0045 * progress)
            points.append(point + offset)
        strands.append((points, 0.000045, material_index))
    return strands


def remove_body_intersections(obj, body):
    body_tree = world_surface(body)
    object_tree = world_surface(obj)
    doomed = {pair[1] for pair in body_tree.overlap(object_tree)}
    if not doomed:
        return 0
    old = obj.data
    materials = list(old.materials)
    vertices = [vertex.co.copy() for vertex in old.vertices]
    faces = [tuple(poly.vertices) for poly in old.polygons if poly.index not in doomed]
    material_indices = [poly.material_index for poly in old.polygons if poly.index not in doomed]
    mesh = bpy.data.meshes.new(old.name + "CollisionClean")
    mesh.from_pydata(vertices, [], faces)
    for value in materials:
        mesh.materials.append(value)
    for poly, material_index in zip(mesh.polygons, material_indices):
        poly.use_smooth = True
        poly.material_index = material_index
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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]

for name in ("HairMain", "HairGuides", "HairlineFine", "HairFlyaways", "HairFiberDetail"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

scalp = bpy.data.objects["HairScalp"]
scalp_material = scalp.data.materials[0]
scalp_shader = scalp_material.node_tree.nodes.get("Principled BSDF")
scalp_shader.inputs["Base Color"].default_value = (0.0048, 0.0009, 0.00035, 1.0)
scalp_shader.inputs["Roughness"].default_value = 0.96
for input_name in ("Specular IOR Level", "Coat Weight"):
    if scalp_shader.inputs.get(input_name):
        scalp_shader.inputs[input_name].default_value = 0.0
scalp["aevrynd_groom_revision"] = 11

tree = world_surface(body)
dark = groom_material("Aevrynd_Hair_v11_Dark", (0.012, 0.0028, 0.0011, 1.0), 0.62)
warm = groom_material("Aevrynd_Hair_v11_Warm", (0.027, 0.0065, 0.0025, 1.0), 0.58)
materials = (dark, warm)
primary, roots = build_primary(tree)
hairline = front_and_nape(tree)
flyaway_strands = flyaways(primary)
main = tube_mesh("HairMain", primary, materials, rig, "hair_main", 3)
guides = tube_mesh("HairGuides", primary[::13], materials, rig, "hair_guides", 3)
fine = tube_mesh("HairlineFine", hairline, materials, rig, "hairline_fine", 3)
loose = tube_mesh("HairFlyaways", flyaway_strands, materials, rig, "hair_flyaways", 3)
removed = {
    obj.name: remove_body_intersections(obj, body)
    for obj in (main, guides, fine, loose)
}

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-groom-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-groom-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-groom-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-groom-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
bpy.ops.object.select_all(action="DESELECT")
runtime = [obj for obj in bpy.data.objects if obj.type in {"MESH", "ARMATURE"}]
for obj in runtime:
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(BUILD), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_extras=True,
    export_animations=True, export_frame_range=True,
)
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_GROOM_V11_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "primary_strands": len(primary),
    "guide_strands": len(primary[::13]),
    "hairline_and_nape_strands": len(hairline),
    "flyaways": len(flyaway_strands),
    "root_count": len(roots),
    "removed_body_intersection_faces": removed,
    "runtime_glb": str(BUILD),
}))
