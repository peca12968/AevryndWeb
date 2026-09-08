import json
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v40.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v41.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v41.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v41-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "groom-v41"
TEXTURE = ROOT / "assets-source" / "aevrynd-character" / "textures" / "aevrynd-hair-clump-alpha-v41.png"
RNG = random.Random(4101)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def centerlines(obj, stride=27, sides=3):
    lines = []
    for start in range(0, len(obj.data.vertices), stride):
        if start + stride > len(obj.data.vertices):
            break
        points = []
        for row in range(stride // sides):
            point = sum(
                (obj.matrix_world @ obj.data.vertices[start + row * sides + side].co for side in range(sides)),
                Vector(),
            ) / sides
            points.append(point)
        lines.append(points)
    return lines


def create_alpha_texture():
    width, height = 256, 512
    image = bpy.data.images.get("AevryndHairClumpAlphaV41")
    if image:
        bpy.data.images.remove(image)
    image = bpy.data.images.new("AevryndHairClumpAlphaV41", width=width, height=height, alpha=True)
    pixels = [0.0] * (width * height * 4)
    phases = [RNG.uniform(0.0, math.tau) for _ in range(17)]
    for y in range(height):
        v = y / (height - 1)
        root = smoothstep(v / 0.035)
        tip = 1.0 - smoothstep((v - 0.76) / 0.24)
        for x in range(width):
            u = x / (width - 1)
            edge = 1.0 - smoothstep((abs(u - 0.5) - 0.37) / 0.13)
            fibers = 0.0
            for index, phase in enumerate(phases):
                center = (index + 0.5) / len(phases)
                center += 0.012 * math.sin(v * (2.1 + index % 4) * math.tau + phase)
                fibers = max(fibers, math.exp(-((u - center) / 0.018) ** 2))
            alpha = max(0.0, min(1.0, edge * root * tip * (0.56 + 0.44 * fibers)))
            tone = 0.72 + 0.28 * fibers
            offset = (y * width + x) * 4
            pixels[offset:offset + 4] = (0.042 * tone, 0.010 * tone, 0.004 * tone, alpha)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def create_material(image):
    material = bpy.data.materials.get("Aevrynd_Hair_Clumps_v41") or bpy.data.materials.new(
        "Aevrynd_Hair_Clumps_v41"
    )
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Base Color"].default_value = (0.026, 0.0042, 0.0014, 1.0)
    shader.inputs["Roughness"].default_value = 0.48
    shader.inputs["Specular IOR Level"].default_value = 0.22
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.36
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_runtime_owned"] = True
    return material


def build_cards(main, body, rig, material, name, offset, stride, width_range, role, loft_bias):
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    tree = body_tree(body)
    lines = centerlines(main)
    selected = lines[offset::stride]
    vertices, faces, uvs = [], [], []
    built_count = 0
    minimum_clearance = 999.0
    for index, original_source in enumerate(selected):
        if any(abs(point.x) > 0.078 and 1.575 < point.z < 1.630 and abs(point.y) < 0.045 for point in original_source):
            continue
        source = list(original_source)
        built_count += 1
        clipped = False
        root = source[0]
        if root.y > -0.04 or abs(root.x) > 0.075:
            cutoff = 1.578 + 0.010 * min(1.0, abs(root.x) / 0.10) + RNG.uniform(-0.003, 0.003)
            kept = [source[0]]
            for point in source[1:]:
                if point.z >= cutoff:
                    kept.append(point)
                    continue
                previous = kept[-1]
                if previous.z > cutoff:
                    factor = (previous.z - cutoff) / max(1e-8, previous.z - point.z)
                    kept.append(previous.lerp(point, factor))
                clipped = True
                break
            if len(kept) >= 4:
                source = kept
        dense = []
        for first, second in zip(source, source[1:]):
            dense.extend((first, first.lerp(second, 1.0 / 3.0), first.lerp(second, 2.0 / 3.0)))
        dense.append(source[-1])
        source = dense
        base = len(vertices)
        width = RNG.uniform(*width_range)
        phase = RNG.uniform(-math.pi, math.pi)
        for row, original in enumerate(source):
            t = row / (len(source) - 1)
            location, normal, _, distance = tree.find_nearest(original)
            normal = normal.normalized() if location is not None else Vector((0.0, 0.0, 1.0))
            previous = source[max(0, row - 1)]
            following = source[min(len(source) - 1, row + 1)]
            tangent = (following - previous).normalized()
            axis = tangent.cross(normal)
            if axis.length < 1e-8:
                axis = Vector((1.0, 0.0, 0.0))
            axis.normalize()
            loft = (0.0007 + loft_bias + 0.0027 * math.sin(math.pi * t) ** 1.35)
            ripple = 0.00045 * math.sin(math.tau * t + phase) * math.sin(math.pi * t)
            center = original + normal * loft + axis * ripple
            back = source[0].y > 0.0
            end_keep = 0.16 if clipped else (0.46 if back else 0.30)
            profile = 0.42 + 0.58 * math.sin(math.pi * min(0.96, t + 0.07))
            taper = profile * (1.0 - (1.0 - end_keep) * t)
            half_width = width * taper
            sides = (center - axis * half_width, center + axis * half_width)
            safe_sides = []
            for point in sides:
                surface, surface_normal, _, _ = tree.find_nearest(point)
                clearance = 0.00055 + loft_bias
                if surface is not None and surface_normal.dot(point - surface) < clearance:
                    point = surface + surface_normal.normalized() * clearance
                safe_sides.append(tuple(point))
            vertices.extend(safe_sides)
            uvs.extend(((0.0, t), (1.0, t)))
            minimum_clearance = min(minimum_clearance, distance + loft - half_width * 0.08)
        for row in range(len(source) - 1):
            a = base + row * 2
            faces.append((a, a + 2, a + 3, a + 1))
    mesh = bpy.data.meshes.new(name + "MeshV41")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = role
    obj["aevrynd_groom_revision"] = 41
    obj["aevrynd_clump_count"] = built_count
    obj["aevrynd_minimum_authored_clearance_m"] = minimum_clearance
    obj["aevrynd_source"] = "Aevrynd authored hierarchical card groom"
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj


def remove_crossing_faces(subject, obstacle):
    def make_tree(obj):
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        faces = [tuple(polygon.vertices) for polygon in obj.data.polygons]
        return BVHTree.FromPolygons(points, faces, all_triangles=False)
    crossings = make_tree(subject).overlap(make_tree(obstacle))
    indices = {subject_index for subject_index, _ in crossings}
    if not indices:
        subject["aevrynd_removed_crossing_faces"] = 0
        return 0
    mesh = subject.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(indices)], context="FACES_ONLY")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    subject["aevrynd_removed_crossing_faces"] = len(indices)
    return len(indices)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = 82
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
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
TEXTURE.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
main = bpy.data.objects["HairMain"]
card_material = create_material(create_alpha_texture())
large = build_cards(main, body, rig, card_material, "HairClumpsLarge", 2, 7, (0.00145, 0.00270), "hair_clumps_large", 0.0)
medium = build_cards(main, body, rig, card_material, "HairClumpsMediumCards", 5, 7, (0.00075, 0.00135), "hair_clumps_medium_cards", 0.0060)
removed_crossings = remove_crossing_faces(medium, large)
bpy.context.scene["aevrynd_hair_revision"] = 41
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-groom-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-groom-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-groom-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-groom-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-groom-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways", "HairGuides"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_GROOM_V41_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "large_clumps": int(large["aevrynd_clump_count"]),
    "medium_clumps": int(medium["aevrynd_clump_count"]),
    "large_vertices": len(large.data.vertices),
    "medium_vertices": len(medium.data.vertices),
    "removed_medium_crossing_faces": removed_crossings,
    "minimum_authored_clearance_m": min(float(large["aevrynd_minimum_authored_clearance_m"]), float(medium["aevrynd_minimum_authored_clearance_m"])),
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
