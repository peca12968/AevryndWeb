import json
import math
from array import array
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v9.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v10.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v10.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "head-v10"


def material(name, color, roughness, anisotropy=0.0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.24
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = anisotropy
    return result


def hair_alpha_image():
    width, height = 256, 512
    image = bpy.data.images.new("aevrynd-hair-strands-v1", width=width, height=height, alpha=True)
    pixels = array("f")
    strand_count = 13
    for y in range(height):
        v = y / (height - 1)
        tip_fade = min(1.0, (1.0 - v) / 0.10)
        root_fade = min(1.0, v / 0.025)
        for x in range(width):
            u = x / (width - 1)
            best = 1.0
            tone = 0.0
            for strand in range(strand_count):
                phase = strand * 1.913
                center = (strand + 0.5) / strand_count
                center += math.sin(v * math.tau * (0.78 + strand * 0.017) + phase) * 0.010
                distance = abs(u - center)
                if distance < best:
                    best = distance
                    tone = 0.78 + 0.22 * math.sin(strand * 2.31 + v * 8.0)
            alpha = math.exp(-((best / 0.0105) ** 2)) * tip_fade * root_fade
            pixels.extend((0.028 * tone, 0.0085 * tone, 0.0032 * tone, alpha))
    image.pixels.foreach_set(pixels)
    image.pack()
    image["aevrynd_source"] = "Procedurally generated strand opacity and color"
    return image


def hair_alpha_material(image):
    result = material("Aevrynd_Hair_AlphaStrands", (0.018, 0.0045, 0.0018, 1.0), 0.58, 0.42)
    shader = result.node_tree.nodes.get("Principled BSDF")
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.07
    texture = result.node_tree.nodes.new("ShaderNodeTexImage")
    texture.name = "Aevrynd Hair Strand Atlas"
    texture.image = image
    result.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    result.node_tree.links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    try:
        result.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    result["aevrynd_alpha_revision"] = 10
    return result


def ribbon_uv(obj, points_per_strand):
    vertices_per_strand = points_per_strand * 2
    if len(obj.data.vertices) % vertices_per_strand:
        raise RuntimeError(f"{obj.name} topology does not match {points_per_strand}-point ribbons")
    uv = obj.data.uv_layers.get("AevryndHairUV") or obj.data.uv_layers.new(name="AevryndHairUV")
    for polygon in obj.data.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = obj.data.loops[loop_index].vertex_index
            within = vertex_index % vertices_per_strand
            row = within // 2
            side = within % 2
            uv.data[loop_index].uv = (float(side), row / (points_per_strand - 1))


def assign_hair_alpha(obj, alpha_material, points_per_strand):
    ribbon_uv(obj, points_per_strand)
    obj.data.materials.clear()
    obj.data.materials.append(alpha_material)
    obj["aevrynd_alpha_card_revision"] = 10


def rebuild_scalp_volume(rig):
    old = bpy.data.objects.get("HairScalp")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    columns, rows = 64, 18
    center = Vector((0.0, -0.022, 1.608))
    radius_x, radius_y, radius_z = 0.098, 0.106, 0.117
    vertices = [center + Vector((0.0, 0.0, radius_z))]
    for row in range(1, rows + 1):
        fraction = row / rows
        for column in range(columns):
            phi = column / columns * math.tau
            frontness = max(0.0, -math.sin(phi))
            backness = max(0.0, math.sin(phi))
            theta_limit = 1.56 - 0.38 * frontness + 0.16 * backness
            theta = theta_limit * fraction
            vertices.append(center + Vector((
                radius_x * math.sin(theta) * math.cos(phi),
                radius_y * math.sin(theta) * math.sin(phi),
                radius_z * math.cos(theta),
            )))
    faces = []
    for column in range(columns):
        following = (column + 1) % columns
        faces.append((0, 1 + following, 1 + column))
    for row in range(rows - 1):
        first = 1 + row * columns
        second = first + columns
        for column in range(columns):
            following = (column + 1) % columns
            faces.append((first + column, first + following, second + following, second + column))
    mesh = bpy.data.meshes.new("HairScalpMesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("HairScalp", mesh)
    bpy.context.scene.collection.objects.link(obj)
    scalp = material("Aevrynd_Hair_ScalpVolume", (0.0055, 0.0011, 0.00045, 1.0), 0.94)
    shader = scalp.node_tree.nodes.get("Principled BSDF")
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.0
    obj.data.materials.append(scalp)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "hair_scalp"
    obj["aevrynd_head_revision"] = 10
    obj["aevrynd_source"] = "Aevrynd parametric collision shell"
    parent_to_head(obj, rig)
    return obj


def body_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def front_surface(surface, x, z):
    tree, matrix, inverse = surface
    origin = Vector((x, -0.35, z))
    direction = Vector((0.0, 1.0, 0.0))
    local_origin = inverse @ origin
    local_direction = (inverse.to_3x3() @ direction).normalized()
    location, normal, _, _ = tree.ray_cast(local_origin, local_direction, 0.6)
    if location is None:
        raise RuntimeError(f"face ray missed at x={x:.5f}, z={z:.5f}")
    point = matrix @ location
    normal_world = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    if normal_world.y > 0.0:
        normal_world.negate()
    return point + normal_world * 0.00022


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def evaluated_world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def push_outside_body(obj, body, clearance):
    tree = evaluated_world_tree(body)
    inverse = obj.matrix_world.inverted()
    head_center = Vector((0.0, 0.0, 1.58))
    moved = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        location, normal, _, _ = tree.find_nearest(point)
        if location is None:
            continue
        offset = point - location
        distance = offset.length
        if distance >= clearance:
            continue
        if distance > 1e-8:
            direction = offset.normalized()
        else:
            outward = point - head_center
            if normal.dot(outward) < 0.0:
                normal.negate()
            direction = normal.normalized()
        target = location + direction * clearance
        maximum = max(maximum, (target - point).length)
        vertex.co = inverse @ target
        moved += 1
    obj.data.update()
    obj["aevrynd_collision_revision"] = 10
    obj["aevrynd_collision_clearance_m"] = clearance
    obj["aevrynd_collision_moved_vertices"] = moved
    return moved, maximum


def skin_from_body(obj, body, rig):
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = world
    tree = KDTree(len(body.data.vertices))
    for vertex in body.data.vertices:
        tree.insert(body.matrix_world @ vertex.co, vertex.index)
    tree.balance()
    groups = {group.index: obj.vertex_groups.new(name=group.name) for group in body.vertex_groups}
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        _, source_index, _ = tree.find(point)
        assignments = sorted(
            ((entry.group, entry.weight) for entry in body.data.vertices[source_index].groups if entry.weight > 1e-8),
            key=lambda item: item[1], reverse=True,
        )[:4]
        total = sum(weight for _, weight in assignments)
        for group_index, weight in assignments:
            groups[group_index].add([vertex.index], weight / total, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Face Layer Deform", "ARMATURE")
    modifier.object = rig
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_world = world
    obj["aevrynd_skin_binding_revision"] = 10
    obj["aevrynd_weight_limit"] = 4


def lip_mesh(name, surface, upper, lip_material, rig, columns=40):
    vertices = []
    for index in range(columns):
        t = index / (columns - 1) * 2.0 - 1.0
        x = t * 0.0290
        envelope = max(0.0, 1.0 - abs(t) ** 1.75)
        crease = 1.5350 + 0.00045 * math.cos(t * math.pi)
        if upper:
            cupid = 0.00125 * math.exp(-((abs(t) - 0.34) / 0.20) ** 2)
            center_notch = 0.00075 * math.exp(-(t / 0.15) ** 2)
            outer = crease + 0.0047 * envelope + cupid - center_notch
        else:
            outer = crease - 0.0058 * envelope - 0.00065 * math.exp(-(t / 0.36) ** 2)
        vertices.append(front_surface(surface, x, crease))
        vertices.append(front_surface(surface, x, outer))
    faces = []
    for index in range(columns - 1):
        a = index * 2
        face = (a, a + 1, a + 3, a + 2)
        faces.append(tuple(reversed(face)) if upper else face)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(lip_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "upper_lip" if upper else "lower_lip"
    obj["aevrynd_head_revision"] = 10
    obj["aevrynd_surface_offset_m"] = 0.00022
    obj["aevrynd_source"] = "Aevrynd surface-authored on CC0-derived female head"
    parent_to_head(obj, rig)
    return obj


def narrow_ribbons(obj, factor):
    if len(obj.data.vertices) % 2:
        raise RuntimeError(f"{obj.name} does not have paired ribbon vertices")
    maximum_shift = 0.0
    for index in range(0, len(obj.data.vertices), 2):
        left = obj.data.vertices[index]
        right = obj.data.vertices[index + 1]
        middle = (left.co + right.co) * 0.5
        old_left = left.co.copy()
        old_right = right.co.copy()
        left.co = middle + (left.co - middle) * factor
        right.co = middle + (right.co - middle) * factor
        maximum_shift = max(maximum_shift, (left.co - old_left).length, (right.co - old_right).length)
    obj.data.update()
    obj["aevrynd_ribbon_width_revision"] = 10
    obj["aevrynd_ribbon_width_factor"] = factor
    return maximum_shift


def remove_root_card_faces(obj, faces_per_strand=6):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    doomed = [face for face in bm.faces if face.index % faces_per_strand == 0]
    count = len(doomed)
    bmesh.ops.delete(bm, geom=doomed, context="FACES_ONLY")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj["aevrynd_removed_root_faces"] = count
    return count


def remove_body_intersecting_faces(obj, body):
    body_tree = evaluated_world_tree(body)
    object_tree = evaluated_world_tree(obj)
    overlaps = body_tree.overlap(object_tree)
    doomed = {pair[1] for pair in overlaps}
    if not doomed:
        return 0
    old_mesh = obj.data
    materials = list(old_mesh.materials)
    vertices = [vertex.co.copy() for vertex in old_mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in old_mesh.polygons if polygon.index not in doomed]
    new_mesh = bpy.data.meshes.new(old_mesh.name + "CollisionClean")
    new_mesh.from_pydata(vertices, [], faces)
    for value in materials:
        new_mesh.materials.append(value)
    for polygon in new_mesh.polygons:
        polygon.use_smooth = True
    obj.data = new_mesh
    bpy.data.meshes.remove(old_mesh)
    obj["aevrynd_removed_body_intersection_faces"] = len(doomed)
    return len(doomed)


def remove_body_intersecting_faces_frames(obj, body, frames=(1, 20)):
    scene = bpy.context.scene
    original = scene.frame_current
    doomed = set()
    for frame in frames:
        scene.frame_set(frame)
        for _, object_polygon in evaluated_world_tree(body).overlap(evaluated_world_tree(obj)):
            doomed.add(object_polygon)
    scene.frame_set(original)
    if not doomed:
        return 0
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    selected = [bm.faces[index] for index in doomed if index < len(bm.faces)]
    bmesh.ops.delete(bm, geom=selected, context="FACES_ONLY")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj["aevrynd_removed_dynamic_intersection_faces"] = len(doomed)
    return len(doomed)


def main_centerlines(obj, points_per_strand=7):
    vertices_per_strand = points_per_strand * 2
    if len(obj.data.vertices) % vertices_per_strand:
        raise RuntimeError("HairMain topology no longer matches the authored ribbon layout")
    strands = []
    for base in range(0, len(obj.data.vertices), vertices_per_strand):
        points = []
        for row in range(points_per_strand):
            left = obj.data.vertices[base + row * 2].co
            right = obj.data.vertices[base + row * 2 + 1].co
            points.append(obj.matrix_world @ ((left + right) * 0.5))
        strands.append(points)
    return strands


def hair_fibers(main, rig):
    vertices = []
    faces = []
    strands = main_centerlines(main)
    root_distances = []
    for strand_index, centerline in enumerate(strands):
        for child in (-1.0, 1.0):
            base = len(vertices)
            root_distances.append(0.0)
            for row, point in enumerate(centerline):
                previous = centerline[max(0, row - 1)]
                following = centerline[min(len(centerline) - 1, row + 1)]
                tangent = (following - previous).normalized()
                radial = Vector((point.x, point.y, 0.0))
                if radial.length < 1e-6:
                    radial = Vector((0.0, -1.0, 0.0))
                radial.normalize()
                width_axis = tangent.cross(radial)
                if width_axis.length < 1e-6:
                    width_axis = tangent.cross(Vector((0.0, 0.0, 1.0)))
                width_axis.normalize()
                progress = row / max(1, len(centerline) - 1)
                separation = child * 0.00048 * math.sin(math.pi * progress)
                irregularity = math.sin(strand_index * 1.713 + progress * 5.2) * 0.00013 * progress
                center = point + width_axis * separation + radial * irregularity
                half_width = 0.00016 * (1.0 - 0.72 * progress) + 0.000025
                vertices.extend((center - width_axis * half_width, center + width_axis * half_width))
            for row in range(1, len(centerline) - 1):
                a = base + row * 2
                faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("HairFiberDetailMesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("HairFiberDetail", mesh)
    bpy.context.scene.collection.objects.link(obj)
    fiber_material = material("Aevrynd_Hair_Fiber_Warm", (0.018, 0.0048, 0.0020, 1.0), 0.60, 0.38)
    fiber_shader = fiber_material.node_tree.nodes.get("Principled BSDF")
    if fiber_shader.inputs.get("Specular IOR Level"):
        fiber_shader.inputs["Specular IOR Level"].default_value = 0.06
    obj.data.materials.append(fiber_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "hair_fiber_detail"
    obj["aevrynd_head_revision"] = 10
    obj["aevrynd_fiber_strands"] = len(strands) * 2
    obj["aevrynd_parent_root_distance_m"] = max(root_distances)
    obj["aevrynd_source"] = "Aevrynd child fibers derived from owned HairMain guides"
    parent_to_head(obj, rig)
    return obj, len(strands) * 2


def refine_eye_aperture(body):
    center_z = 1.6078
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    for center_x in (0.034527, -0.034443):
        for vertex in body.data.vertices:
            source = body.matrix_world @ vertex.co
            dx = source.x - center_x
            dz = source.z - center_z
            if abs(dx) >= 0.0205 or not (0.0022 <= abs(dz) <= 0.0115) or source.y > -0.108:
                continue
            horizontal = max(0.0, 1.0 - (abs(dx) / 0.0205) ** 2)
            band = max(0.0, 1.0 - abs(abs(dz) - 0.0062) / 0.0053)
            target = source.copy()
            target.z = center_z + dz * (1.0 - 0.075 * horizontal * band)
            delta = (target - source).length
            if delta > 1e-8:
                vertex.co = inverse @ target
                changed += 1
                maximum = max(maximum, delta)
    body.data.update()
    body["aevrynd_eyelid_revision"] = 10
    body["aevrynd_eyelid_v10_changed_vertices"] = changed
    body["aevrynd_eyelid_v10_max_delta_m"] = maximum
    return changed, maximum


def reduce_pupils(factor=0.72):
    adjusted = {}
    for name in ("Eye_L_Pupil", "Eye_R_Pupil"):
        obj = bpy.data.objects[name]
        center = sum((vertex.co for vertex in obj.data.vertices), Vector()) / len(obj.data.vertices)
        maximum = 0.0
        for vertex in obj.data.vertices:
            old = vertex.co.copy()
            vertex.co.x = center.x + (vertex.co.x - center.x) * factor
            vertex.co.z = center.z + (vertex.co.z - center.z) * factor
            maximum = max(maximum, (vertex.co - old).length)
        obj.data.update()
        obj["aevrynd_pupil_revision"] = 10
        obj["aevrynd_pupil_scale_factor"] = factor
        adjusted[name] = maximum
    return adjusted


def follow_eyelids():
    shifts = {
        "Eye_L_UpperLashes": -0.00024,
        "Eye_R_UpperLashes": -0.00024,
        "Eye_L_LowerLashes": 0.00020,
        "Eye_R_LowerLashes": 0.00020,
        "Eye_L_TearMeniscus": 0.00020,
        "Eye_R_TearMeniscus": 0.00020,
    }
    for name, shift in shifts.items():
        obj = bpy.data.objects[name]
        world = obj.matrix_world.copy()
        world.translation.z += shift
        obj.matrix_world = world
        obj["aevrynd_eyelid_follow_revision"] = 10
    return shifts


def tune_skin(body):
    skin = body.data.materials[0]
    shader = skin.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.49
    if shader.inputs.get("Subsurface Weight"):
        shader.inputs["Subsurface Weight"].default_value = 0.075
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.23
    bump = skin.node_tree.nodes.get("Aevrynd Skin Micro Bump")
    if bump:
        bump.inputs["Strength"].default_value = 0.11
        bump.inputs["Distance"].default_value = 0.00016
    skin["aevrynd_head_material_revision"] = 10


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=82):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = lens
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

changed, maximum_eye_delta = refine_eye_aperture(body)
followed = follow_eyelids()
pupil_adjustments = reduce_pupils()
tune_skin(body)
surface = body_surface(body)
lip_material = material("Aevrynd_Lip_Natural", (0.185, 0.047, 0.034, 1.0), 0.72)
lip_shader = lip_material.node_tree.nodes.get("Principled BSDF")
if lip_shader.inputs.get("Specular IOR Level"):
    lip_shader.inputs["Specular IOR Level"].default_value = 0.04
upper_lip = lip_mesh("Lip_Upper", surface, True, lip_material, rig)
lower_lip = lip_mesh("Lip_Lower", surface, False, lip_material, rig)
for lip in (upper_lip, lower_lip):
    skin_from_body(lip, body, rig)
    clearance = lip.modifiers.new("Aevrynd Face Layer Clearance", "DISPLACE")
    clearance.direction = "NORMAL"
    clearance.mid_level = 0.0
    clearance.strength = 0.00085
    lip["aevrynd_dynamic_clearance_m"] = 0.00085
lip_removed_faces = {upper_lip.name: 0, lower_lip.name: 0}
main_shift = narrow_ribbons(bpy.data.objects["HairMain"], 0.82)
guide_shift = narrow_ribbons(bpy.data.objects["HairGuides"], 0.78)
removed_root_faces = remove_root_card_faces(bpy.data.objects["HairMain"])
hair_collision = {}
for name, clearance in (("HairMain", 0.0030), ("HairGuides", 0.0030), ("HairlineFine", 0.0010), ("HairFlyaways", 0.0015)):
    hair_collision[name] = push_outside_body(bpy.data.objects[name], body, clearance)
removed_body_faces = {"HairMain": remove_body_intersecting_faces(bpy.data.objects["HairMain"], body)}
fiber_detail, fiber_count = hair_fibers(bpy.data.objects["HairMain"], rig)
hair_collision["HairFiberDetail"] = push_outside_body(fiber_detail, body, 0.0025)
removed_body_faces["HairFiberDetail"] = remove_body_intersecting_faces(fiber_detail, body)
alpha_image = hair_alpha_image()
alpha_material = hair_alpha_material(alpha_image)
for name, points in (("HairMain", 7), ("HairGuides", 7), ("HairFlyaways", 7)):
    assign_hair_alpha(bpy.data.objects[name], alpha_material, points)
scalp = bpy.data.objects["HairScalp"]
scalp_material = scalp.data.materials[0]
scalp_shader = scalp_material.node_tree.nodes.get("Principled BSDF")
scalp_shader.inputs["Base Color"].default_value = (0.006, 0.0012, 0.0005, 1.0)
scalp_shader.inputs["Roughness"].default_value = 0.94
if scalp_shader.inputs.get("Specular IOR Level"):
    scalp_shader.inputs["Specular IOR Level"].default_value = 0.0
scalp_material["aevrynd_head_revision"] = 10

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-head-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-head-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-head-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-head-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

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

print("AEVRYND_HEAD_V10_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "eyelid_changed_vertices": changed,
    "eyelid_max_delta_m": maximum_eye_delta,
    "followed_layers": followed,
    "pupil_adjustments": pupil_adjustments,
    "lip_layers": [upper_lip.name, lower_lip.name],
    "lip_removed_intersection_faces": lip_removed_faces,
    "main_ribbon_maximum_shift_m": main_shift,
    "removed_main_root_faces": removed_root_faces,
    "guide_ribbon_maximum_shift_m": guide_shift,
    "fiber_strands": fiber_count,
    "fiber_vertices": len(fiber_detail.data.vertices),
    "scalp_vertices": len(scalp.data.vertices),
    "hair_collision_adjustments": hair_collision,
    "removed_body_intersection_faces": removed_body_faces,
    "runtime_glb": str(BUILD),
}))
