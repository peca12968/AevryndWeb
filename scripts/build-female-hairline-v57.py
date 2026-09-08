import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v52.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v57.blend"
TEXTURE = ROOT / "assets-source" / "aevrynd-character" / "textures" / "aevrynd-hair-strand-alpha-v57.png"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "hairline-v57"
PART_X = -0.015


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def hairline_threshold(x):
    temple = smoothstep(abs(x + 0.002) / 0.082)
    widow_peak = 0.0028 * math.exp(-((x + 0.010) / 0.018) ** 2)
    asymmetry = 0.0012 * math.sin((x + 0.016) * 67.0)
    return 1.681 + 0.010 * temple - widow_peak + asymmetry


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def outward_normal(location, normal):
    result = normal.normalized()
    if result.dot(location - Vector((0.0, 0.0, 1.60))) < 0.0:
        result.negate()
    return result


def project_shell(tree, candidate, clearance):
    location, normal, _, _ = tree.find_nearest(candidate)
    if location is None:
        raise RuntimeError("hair_shell_projection_failed")
    normal = outward_normal(location, normal)
    return location + normal * clearance, normal


def make_texture():
    width, height = 192, 768
    image = bpy.data.images.get("AevryndHairStrandAlphaV57")
    if image:
        bpy.data.images.remove(image)
    image = bpy.data.images.new("AevryndHairStrandAlphaV57", width=width, height=height, alpha=True)
    rng = random.Random(55101)
    fibers = [
        ((index + 0.5) / 11.0, rng.uniform(0.018, 0.030), rng.uniform(-math.pi, math.pi), rng.uniform(0.82, 1.0))
        for index in range(11)
    ]
    pixels = [0.0] * (width * height * 4)
    for y in range(height):
        v = y / (height - 1)
        tip = 1.0 - smoothstep((v - 0.84) / 0.16)
        # Keep the scalp coverage layer visible through the first part of each
        # ribbon. A synchronized opaque root produced a hard horizontal band
        # in profile, even though the geometry itself cleared the scalp.
        root = 0.16 + 0.84 * smoothstep(v / 0.16)
        for x in range(width):
            u = x / (width - 1)
            edge = 1.0 - smoothstep((abs(u - 0.5) - 0.43) / 0.07)
            fiber_value = 0.0
            tone = 0.0
            for center, fiber_width, phase, fiber_tone in fibers:
                displaced = center + 0.012 * math.sin(v * math.tau * 1.55 + phase)
                strength = math.exp(-((u - displaced) / fiber_width) ** 2)
                fiber_value = max(fiber_value, strength)
                tone = max(tone, strength * fiber_tone)
            alpha = edge * root * tip * min(1.0, 0.28 + 0.94 * fiber_value)
            shade = 0.68 + 0.32 * tone
            offset = (y * width + x) * 4
            pixels[offset:offset + 4] = (0.028 * shade, 0.0058 * shade, 0.0018 * shade, alpha)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_material(image):
    material = bpy.data.materials.get("Aevrynd_Hair_Strands_v57") or bpy.data.materials.new("Aevrynd_Hair_Strands_v57")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Roughness"].default_value = 0.54
    shader.inputs["Specular IOR Level"].default_value = 0.055
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.58
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_runtime_owned"] = True
    material["aevrynd_alpha_strategy"] = "eleven_fiber_clump"
    return material


def tune_scalp(scalp):
    material = scalp.data.materials[0]
    density = scalp.data.color_attributes["AevryndScalpDensity"]
    for vertex in scalp.data.vertices:
        value = density.data[vertex.index]
        original_alpha = value.color_srgb[3]
        x, y, z = vertex.co
        front_weight = smoothstep((-y - 0.050) / 0.060)
        shaped_alpha = smoothstep((z - hairline_threshold(x)) / 0.011)
        alpha = original_alpha * (1.0 - front_weight) + min(original_alpha, shaped_alpha) * front_weight
        value.color_srgb = (0.020, 0.0042, 0.0014, alpha)
    for node in material.node_tree.nodes:
        if node.type != "BSDF_PRINCIPLED":
            continue
        node.inputs["Roughness"].default_value = 0.82
        node.inputs["Specular IOR Level"].default_value = 0.025
        if node.inputs.get("Anisotropic IOR Level"):
            node.inputs["Anisotropic IOR Level"].default_value = 0.28
    material["aevrynd_groom_revision"] = 57


def remove_old_groom():
    removed = []
    for name in ("HairMain", "HairGuides", "HairFlyaways", "HairClumpsLarge", "HairClumpsMediumCards", "HairlineBaby"):
        obj = bpy.data.objects.get(name)
        if not obj:
            continue
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        removed.append(name)
    return removed


def safe_free_point(body_tree, point, minimum_clearance):
    location, normal, _, distance = body_tree.find_nearest(point)
    if location is None or distance >= minimum_clearance:
        return point, distance if location is not None else 999.0
    normal = outward_normal(location, normal)
    return location + normal * minimum_clearance, minimum_clearance


def strand_path(root, root_normal, scalp_tree, body_tree, rng, rows, layer_clearance, force_rear=False):
    side = -1.0 if root.x < PART_X else 1.0
    rear_weight = 1.0 if force_rear else smoothstep((root.y - 0.004) / 0.072)
    side_transition = Vector((side * (0.100 + rng.uniform(-0.004, 0.004)), root.y + rng.uniform(0.010, 0.022), root.z - 0.025))
    rear_transition = Vector((root.x * 1.05 + rng.uniform(-0.003, 0.003), 0.112 + rng.uniform(-0.004, 0.006), root.z - 0.035))
    transition_guess = side_transition.lerp(rear_transition, rear_weight)
    transition, transition_normal = project_shell(scalp_tree, transition_guess, layer_clearance + rng.uniform(0.0001, 0.0008))
    y_factor = max(-1.0, min(1.0, root.y / 0.105))
    side_target = Vector((
        side * (0.116 + rng.uniform(-0.006, 0.009)),
        min(0.125, root.y + 0.018 + rng.uniform(-0.006, 0.012)),
        1.485 + 0.022 * (1.0 - abs(y_factor)) + rng.uniform(-0.010, 0.012),
    ))
    rear_target = Vector((
        root.x * 1.10 + rng.uniform(-0.005, 0.005),
        0.126 + rng.uniform(-0.004, 0.006),
        1.465 + rng.uniform(-0.010, 0.012),
    ))
    target = side_target.lerp(rear_target, rear_weight)
    points, normals, minimum_body = [], [], 999.0
    # Stagger where neighboring fibers leave the scalp and preserve the scalp
    # tangent into the falling section. A fixed split made every ribbon bend on
    # the same profile line and read as a hard helmet rim.
    leave = rng.uniform(0.29, 0.51)
    fall_distance = (target - transition).length
    scalp_tangent = transition - root
    if scalp_tangent.length < 1e-8:
        scalp_tangent = Vector((side, 0.0, -0.15))
    scalp_tangent.normalize()
    control_1 = transition + scalp_tangent * (0.30 * fall_distance)
    control_2 = target + Vector((0.0, 0.0, 0.30 * fall_distance))
    for row in range(rows):
        t = row / (rows - 1)
        if t <= leave:
            local = t / leave
            guess = root.lerp(transition, smoothstep(local))
            point, normal = project_shell(
                scalp_tree,
                guess,
                layer_clearance + 0.0070 * math.sin(math.pi * local) ** 1.4,
            )
        else:
            local = (t - leave) / (1.0 - leave)
            inverse = 1.0 - local
            point = (
                transition * (inverse ** 3)
                + control_1 * (3.0 * inverse * inverse * local)
                + control_2 * (3.0 * inverse * local * local)
                + target * (local ** 3)
            )
            point.x += side * 0.006 * math.sin(math.pi * local)
            point.y += 0.004 * math.sin(math.pi * local)
            point, _ = safe_free_point(scalp_tree, point, 0.0030)
            point, body_distance = safe_free_point(body_tree, point, 0.0040)
            minimum_body = min(minimum_body, body_distance)
            tangent_hint = target - transition
            side_normal = Vector((-side * 0.65, -0.15, 0.74))
            rear_normal = Vector((0.0, 0.82, 0.57))
            normal = side_normal.lerp(rear_normal, rear_weight).normalized()
            if normal.dot(tangent_hint) > 0.85:
                normal = Vector((0.0, -1.0, 0.0))
        points.append(point)
        normals.append(normal)
    return points, normals, minimum_body


def append_ribbon(vertices, faces, uvs, points, normals, width, rng):
    base = len(vertices)
    rows = len(points)
    phase = rng.uniform(-math.pi, math.pi)
    for row, (point, normal) in enumerate(zip(points, normals)):
        t = row / (rows - 1)
        before = points[max(0, row - 1)]
        after = points[min(rows - 1, row + 1)]
        tangent = after - before
        if tangent.length < 1e-8:
            tangent = Vector((0.0, 0.0, -1.0))
        tangent.normalize()
        across = tangent.cross(normal)
        if across.length < 1e-8:
            across = Vector((1.0, 0.0, 0.0))
        across.normalize()
        taper = (1.0 - 0.76 * (t ** 1.6))
        flutter = across * (0.00035 * math.sin(t * math.tau * 1.35 + phase) * math.sin(math.pi * t))
        half = 0.5 * width * taper
        vertices.extend((tuple(point + flutter - across * half), tuple(point + flutter + across * half)))
        uvs.extend(((0.0, t), (1.0, t)))
    for row in range(rows - 1):
        index = base + row * 2
        faces.append((index, index + 2, index + 3, index + 1))


def build_fiber_layer(name, role, scalp_tree, body_tree, rig, material, y_rows, x_rows, width, clearance, seed):
    rng = random.Random(seed)
    vertices, faces, uvs = [], [], []
    root_clearances = []
    minimum_body = 999.0
    roots = 0
    for y_index in range(y_rows):
        y = -0.104 + (0.202 * y_index / (y_rows - 1))
        half_extent = 0.096 * math.sqrt(max(0.08, 1.0 - (y / 0.116) ** 2))
        for x_index in range(x_rows):
            x = -half_extent + (2.0 * half_extent * (x_index + 0.5) / x_rows)
            x += rng.uniform(-0.32, 0.32) * (2.0 * half_extent / x_rows)
            y_jittered = y + rng.uniform(-0.0022, 0.0022)
            if abs(x - PART_X) < 0.00125:
                continue
            vertical_drop = 0.060 * smoothstep((y_jittered - 0.052) / 0.052)
            root, normal = project_shell(scalp_tree, Vector((x, y_jittered, 1.72 - vertical_drop)), clearance)
            if root.z < 1.605:
                continue
            if root.y < -0.058 and root.z < hairline_threshold(root.x) + rng.uniform(-0.0018, 0.0018):
                continue
            points, normals, body_distance = strand_path(root, normal, scalp_tree, body_tree, rng, 10, clearance)
            append_ribbon(vertices, faces, uvs, points, normals, width * rng.uniform(0.78, 1.20), rng)
            root_clearances.append(clearance)
            minimum_body = min(minimum_body, body_distance)
            roots += 1
    if role == "hair_fiber_base":
        for y_index in range(y_rows):
            y = -0.102 + (0.198 * y_index / (y_rows - 1))
            vertical_drop = 0.060 * smoothstep((y - 0.052) / 0.052)
            for side in (-1.0, 1.0):
                root, normal = project_shell(scalp_tree, Vector((PART_X + side * 0.00115, y, 1.72 - vertical_drop)), clearance + 0.00035)
                if root.y < -0.058 and root.z < hairline_threshold(root.x) + rng.uniform(-0.0012, 0.0012):
                    continue
                points, normals, body_distance = strand_path(root, normal, scalp_tree, body_tree, rng, 10, clearance + 0.00035)
                append_ribbon(vertices, faces, uvs, points, normals, width * 1.34, rng)
                root_clearances.append(clearance + 0.00035)
                minimum_body = min(minimum_body, body_distance)
                roots += 1
        for y_index in range(18):
            y = 0.030 + 0.068 * y_index / 17.0
            vertical_drop = 0.060 * smoothstep((y - 0.052) / 0.052)
            for x_offset in (-0.0030, -0.0020, -0.0010, 0.0, 0.0010, 0.0020, 0.0030):
                root, normal = project_shell(scalp_tree, Vector((PART_X + x_offset, y, 1.72 - vertical_drop)), clearance + 0.00055)
                points, normals, body_distance = strand_path(root, normal, scalp_tree, body_tree, rng, 10, clearance + 0.00055, True)
                append_ribbon(vertices, faces, uvs, points, normals, width * 1.70, rng)
                root_clearances.append(clearance + 0.00055)
                minimum_body = min(minimum_body, body_distance)
                roots += 1
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_role"] = role
    obj["aevrynd_groom_revision"] = 57
    obj["aevrynd_strand_count"] = roots
    obj["aevrynd_root_clearance_m"] = min(root_clearances)
    obj["aevrynd_minimum_free_body_clearance_m"] = minimum_body
    obj["aevrynd_part_x_m"] = PART_X
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
TEXTURE.parent.mkdir(parents=True, exist_ok=True)
scalp = bpy.data.objects["HairScalp"]
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
scalp_tree = evaluated_tree(scalp)
body_tree = evaluated_tree(body)
removed = remove_old_groom()
tune_scalp(scalp)
material = make_material(make_texture())
base = build_fiber_layer("HairFiberBase", "hair_fiber_base", scalp_tree, body_tree, rig, material, 35, 48, 0.00220, 0.00105, 55011)
detail = build_fiber_layer("HairFiberDetail", "hair_fiber_detail", scalp_tree, body_tree, rig, material, 23, 32, 0.00128, 0.00205, 55029)
lod1 = build_fiber_layer("HairFiberLOD1", "hair_fiber_lod1", scalp_tree, body_tree, rig, material, 20, 30, 0.00285, 0.00145, 55043)
lod1.hide_render = True
bpy.context.scene["aevrynd_hair_revision"] = 57
bpy.context.scene["aevrynd_groom_strategy"] = "stratified_narrow_fiber_clumps"
bpy.context.scene["aevrynd_release_state"] = "AUTHORING"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
for name, location, target, lens in (
    ("female-hairline-front", (0.0, -0.72, 1.62), (0.0, -0.005, 1.59), 88),
    ("female-hairline-three-quarter", (0.30, -0.64, 1.64), (0.0, 0.0, 1.59), 88),
    ("female-hairline-left", (-0.72, -0.02, 1.62), (0.0, 0.0, 1.59), 88),
    ("female-hairline-right", (0.72, -0.02, 1.62), (0.0, 0.0, 1.59), 88),
    ("female-hairline-top", (0.0, -0.015, 2.17), (-0.005, -0.005, 1.67), 96),
    ("female-hairline-back", (0.0, 0.76, 1.62), (0.0, 0.01, 1.58), 88),
):
    render(camera, name, location, target, lens)

print("AEVRYND_HAIRLINE_V57=" + json.dumps({
    "state": "AUTHORING",
    "removed": removed,
    "base_strands": base["aevrynd_strand_count"],
    "detail_strands": detail["aevrynd_strand_count"],
    "base_vertices": len(base.data.vertices),
    "detail_vertices": len(detail.data.vertices),
    "lod1_strands": lod1["aevrynd_strand_count"],
    "lod1_vertices": len(lod1.data.vertices),
    "base_minimum_free_body_clearance_m": base["aevrynd_minimum_free_body_clearance_m"],
    "detail_minimum_free_body_clearance_m": detail["aevrynd_minimum_free_body_clearance_m"],
}))
