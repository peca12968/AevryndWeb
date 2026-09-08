import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v3.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v4.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v4.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "hair-v4"
RNG = random.Random(284771)


def make_material(name, color, roughness, anisotropy=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("IOR"):
        shader.inputs["IOR"].default_value = 1.55
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = anisotropy
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.025
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.28
    return material


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), body.matrix_world, body.matrix_world.inverted()


def world_hit_from_inside(surface_data, origin, direction):
    tree, matrix, inverse = surface_data
    local_origin = inverse @ origin
    local_direction = (inverse.to_3x3() @ direction).normalized()
    location, normal, _, _ = tree.ray_cast(local_origin, local_direction, 0.5)
    if location is None:
        return None
    world_location = matrix @ location
    world_normal = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    return world_location, world_normal


def keep_outside(surface_data, point, clearance):
    tree, matrix, inverse = surface_data
    local_point = inverse @ point
    location, normal, _, _ = tree.find_nearest(local_point)
    if location is None:
        return point, float("inf")
    world_location = matrix @ location
    world_normal = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    signed = (point - world_location).dot(world_normal)
    if signed < clearance:
        point = point + world_normal * (clearance - signed)
        signed = clearance
    return point, signed


def bezier(a, b, c, d, t):
    u = 1.0 - t
    return a * (u ** 3) + b * (3.0 * u * u * t) + c * (3.0 * u * t * t) + d * (t ** 3)


def ribbon_mesh(name, strands, material):
    vertices = []
    faces = []
    for points, root_width in strands:
        base = len(vertices)
        for index, point in enumerate(points):
            previous = points[max(0, index - 1)]
            following = points[min(len(points) - 1, index + 1)]
            tangent = (following - previous).normalized()
            radial = Vector((point.x, point.y + 0.002, 0.0))
            if radial.length < 0.001:
                radial = Vector((0, -1, 0))
            radial.normalize()
            width_axis = tangent.cross(radial)
            if width_axis.length < 0.001:
                width_axis = tangent.cross(Vector((0, 1, 0)))
            width_axis.normalize()
            t = index / max(1, len(points) - 1)
            envelope = max(0.055, math.sin(math.pi * t) ** 0.42)
            width = root_width * envelope
            vertices.append(point - width_axis * width)
            vertices.append(point + width_axis * width)
        for row in range(len(points) - 1):
            a = base + row * 2
            b = a + 1
            c = base + (row + 1) * 2 + 1
            d = base + (row + 1) * 2
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def scalp_cap(body, material):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    source_mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    normal_matrix = matrix.inverted().transposed().to_3x3()
    selected = []
    for polygon in source_mesh.polygons:
        center = matrix @ polygon.center
        hairline = 1.655 + 0.020 * min(1.0, abs(center.x) / 0.078) ** 1.7
        if center.y < -0.015:
            selected_here = center.z > hairline
        elif center.y < 0.055:
            selected_here = center.z > 1.605
        else:
            selected_here = center.z > 1.565
        if selected_here:
            selected.append(polygon)
    used = sorted({index for polygon in selected for index in polygon.vertices})
    remap = {source_index: target_index for target_index, source_index in enumerate(used)}
    vertices = []
    for source_index in used:
        vertex = source_mesh.vertices[source_index]
        point = matrix @ vertex.co
        normal = (normal_matrix @ vertex.normal).normalized()
        vertices.append(point + normal * 0.0014)
    faces = [tuple(remap[index] for index in polygon.vertices) for polygon in selected]
    mesh = bpy.data.meshes.new("HairScalpMesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("HairScalp", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    evaluated.to_mesh_clear()
    obj["aevrynd_role"] = "hair_scalp"
    return obj


def perpendicular_basis(direction):
    reference = Vector((0, 0, 1)) if abs(direction.z) < 0.9 else Vector((1, 0, 0))
    axis_a = direction.cross(reference).normalized()
    axis_b = direction.cross(axis_a).normalized()
    return axis_a, axis_b


def build_groom(body):
    surface_data = surface(body)
    center = Vector((0.0, -0.003, 1.625))
    part_x = 0.012
    roots = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for index in range(190):
        fraction = (index + 0.5) / 190
        cos_theta = 1.0 - fraction * 1.10
        theta = math.acos(max(-1.0, min(1.0, cos_theta)))
        phi = index * golden
        direction = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
        hit = world_hit_from_inside(surface_data, center, direction)
        if not hit:
            continue
        root, normal = hit
        if root.y < -0.055 and root.z < 1.66:
            continue
        if abs(root.x - part_x) < 0.0035 and root.z > 1.68 and root.y < 0.065:
            continue
        roots.append((direction, root, normal))

    main_strands = []
    guide_strands = []
    minimum_clearance = float("inf")
    missed_roots = 0
    for clump_index, (direction, guide_root, guide_normal) in enumerate(roots):
        axis_a, axis_b = perpendicular_basis(direction)
        for child in range(4):
            spread_a = ((child * 0.754877666 + clump_index * 0.173) % 1.0 - 0.5) * 0.048
            spread_b = ((child * 0.569840296 + clump_index * 0.113) % 1.0 - 0.5) * 0.048
            child_direction = (direction + axis_a * spread_a + axis_b * spread_b).normalized()
            hit = world_hit_from_inside(surface_data, center, child_direction)
            if not hit:
                missed_roots += 1
                continue
            root, normal = hit
            root += normal * 0.00165
            side_sign = 1.0 if root.x >= part_x else -1.0
            if abs(root.x - part_x) < 0.006:
                side_sign = 1.0 if (child + clump_index) % 2 else -1.0
            desired = Vector((side_sign * 0.62, child_direction.y * 0.48, -0.48))
            tangent = desired - normal * desired.dot(normal)
            if tangent.length < 0.001:
                tangent = Vector((side_sign, 0, -0.2))
            tangent.normalize()
            crown = max(0.0, min(1.0, (root.z - 1.625) / 0.15))
            length = 0.026 + crown * 0.044 + RNG.uniform(-0.004, 0.006)
            points = []
            for step in range(7):
                t = step / 6
                point = root + tangent * length * t
                point += normal * (math.sin(math.pi * t) * (0.0035 + 0.002 * crown))
                point.x += math.sin(t * math.pi + clump_index * 0.47) * 0.0012 * t
                point.y += math.sin(t * math.pi + child * 0.83) * 0.0007 * t
                point, clearance = keep_outside(surface_data, point, 0.00135)
                minimum_clearance = min(minimum_clearance, clearance)
                points.append(point)
            strand = (points, 0.00135 + RNG.uniform(-0.00018, 0.00018))
            main_strands.append(strand)
            if child == 0:
                guide_strands.append((points, 0.0020))

    # Fine hairs soften the forehead transition instead of forming a solid cap edge.
    hairline_strands = []
    for index in range(380):
        if len(hairline_strands) >= 320:
            break
        t = index / 379 * 2.0 - 1.0
        x = t * 0.068 + RNG.uniform(-0.0008, 0.0008)
        z = 1.661 + 0.019 * abs(t) ** 1.7 + RNG.uniform(-0.0012, 0.0012)
        origin = Vector((x, -0.34, z))
        hit = world_hit_from_inside(surface_data, origin, Vector((0, 1, 0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.00065
        side_sign = 1.0 if x >= part_x else -1.0
        length = RNG.uniform(0.010, 0.027) * (0.72 + 0.28 * abs(t))
        direction = (normal * 0.10 + Vector((side_sign * 0.22, -0.06, -0.78))).normalized()
        mid, c1 = keep_outside(surface_data, root + direction * length * 0.55, 0.0008)
        tip, c2 = keep_outside(surface_data, root + direction * length, 0.0008)
        minimum_clearance = min(minimum_clearance, c1, c2)
        hairline_strands.append(([root, mid, tip], 0.00032))
    if len(hairline_strands) != 320:
        missed_roots += 320 - len(hairline_strands)

    # Separate nape hairs break the hard lower edge of the scalp layer.
    nape_count = 0
    for index in range(220):
        if nape_count >= 160:
            break
        t = index / 219 * 2.0 - 1.0
        x = t * 0.066 + RNG.uniform(-0.0007, 0.0007)
        z = 1.566 + 0.024 * abs(t) ** 1.45 + RNG.uniform(-0.0010, 0.0010)
        hit = world_hit_from_inside(surface_data, Vector((x, 0.34, z)), Vector((0, -1, 0)))
        if not hit:
            continue
        root, normal = hit
        root += normal * 0.0009
        side_sign = 1.0 if x >= 0 else -1.0
        length = RNG.uniform(0.009, 0.021)
        direction = (normal * 0.08 + Vector((side_sign * 0.18, 0.04, -0.86))).normalized()
        mid, c1 = keep_outside(surface_data, root + direction * length * 0.55, 0.0008)
        tip, c2 = keep_outside(surface_data, root + direction * length, 0.0008)
        minimum_clearance = min(minimum_clearance, c1, c2)
        hairline_strands.append(([root, mid, tip], 0.00028))
        nape_count += 1
    if nape_count != 160:
        missed_roots += 160 - nape_count

    # A small separate layer of flyaways breaks the outer silhouette.
    flyaways = []
    for index in range(56):
        source_points, _ = main_strands[(index * 37) % len(main_strands)]
        points = []
        for step, source_point in enumerate(source_points):
            t = step / (len(source_points) - 1)
            offset = Vector(
                (
                    math.sin(index * 1.7 + t * 4.3),
                    math.cos(index * 1.1 + t * 3.1),
                    math.sin(index * 0.7 + t * 5.0),
                )
            ) * (0.007 * t)
            point, clearance = keep_outside(surface_data, source_point + offset, 0.0008)
            minimum_clearance = min(minimum_clearance, clearance)
            points.append(point)
        flyaways.append((points, 0.00020))

    hair_material = make_material("Aevrynd_Hair_DarkBrown", (0.026, 0.008, 0.003, 1), 0.46, 0.68)
    scalp_material = make_material("Aevrynd_Hair_Scalp", (0.014, 0.0035, 0.0015, 1), 0.72, 0.12)
    guide_material = make_material("Aevrynd_Hair_Primary", (0.027, 0.0082, 0.0031, 1), 0.48, 0.62)
    scalp_shader = scalp_material.node_tree.nodes.get("Principled BSDF")
    if scalp_shader.inputs.get("Specular IOR Level"):
        scalp_shader.inputs["Specular IOR Level"].default_value = 0.12
    noise = scalp_material.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 185.0
    noise.inputs["Detail"].default_value = 2.2
    noise.inputs["Roughness"].default_value = 0.42
    bump = scalp_material.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.11
    bump.inputs["Distance"].default_value = 0.00065
    scalp_material.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    scalp_material.node_tree.links.new(bump.outputs["Normal"], scalp_shader.inputs["Normal"])
    objects = [
        scalp_cap(body, scalp_material),
        ribbon_mesh("HairGuides", guide_strands, guide_material),
        ribbon_mesh("HairMain", main_strands, hair_material),
        ribbon_mesh("HairlineFine", hairline_strands, hair_material),
        ribbon_mesh("HairFlyaways", flyaways, hair_material),
    ]
    roles = ("hair_scalp", "hair_guides", "hair_main", "hairline_fine", "hair_flyaways")
    for obj, role in zip(objects, roles):
        obj["aevrynd_role"] = role
        obj["aevrynd_source"] = "Aevrynd authored groom on CC0 female base"
        obj["aevrynd_collision_clearance_m"] = minimum_clearance
    return objects, len(roots), len(main_strands), len(hairline_strands), len(flyaways), missed_roots, minimum_clearance


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=72):
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


def export_runtime(body):
    multires = next(m for m in body.modifiers if m.type == "MULTIRES")
    old = (multires.levels, multires.sculpt_levels, multires.render_levels)
    multires.levels = multires.sculpt_levels = multires.render_levels = 0
    bpy.ops.object.select_all(action="DESELECT")
    runtime = [
        obj for obj in bpy.data.objects
        if obj.type == "MESH" and (
            obj == body
            or obj.name.startswith("Eye_")
            or obj.name.startswith("Brow_")
            or obj.name.startswith("Hair")
        )
    ]
    for obj in runtime:
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.gltf(
        filepath=str(BUILD), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
    )
    multires.levels, multires.sculpt_levels, multires.render_levels = old
    return runtime


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
groom, guide_count, strand_count, hairline_count, flyaway_count, missed_roots, clearance = build_groom(body)
for obj in bpy.data.objects:
    if obj.get("aevrynd_role") == "cornea":
        obj.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
runtime = export_runtime(body)

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-hair-front", (0, -0.98, 1.56), (0, 0, 1.535), 72)
render(camera, "female-hair-three-quarter", (0.38, -0.82, 1.57), (0, 0, 1.525), 72)
render(camera, "female-hair-side", (0.82, 0, 1.56), (0, 0, 1.52), 72)
render(camera, "female-hair-back", (0, 1.02, 1.55), (0, 0.02, 1.50), 72)

print(
    "AEVRYND_HAIR_REPORT="
    + json.dumps(
        {
            "state": "AUTHORING",
            "guide_count": guide_count,
            "main_strands": strand_count,
            "hairline_strands": hairline_count,
            "flyaways": flyaway_count,
            "missed_roots": missed_roots,
            "minimum_body_clearance_m": clearance,
            "groom_layers": [obj.name for obj in groom],
            "runtime_objects": len(runtime),
            "runtime_glb": str(BUILD),
        }
    )
)
