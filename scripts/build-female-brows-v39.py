import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v38.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v39.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v39.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v39-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "brows-v39"


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_point(tree, x, z, clearance):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.36, z)), Vector((0.0, 1.0, 0.0)), 0.7)
    if location is None:
        raise RuntimeError(f"brow ray missed at {x:.5f}, {z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def hair_material(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.53
    shader.inputs["Specular IOR Level"].default_value = 0.13
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.30
    mat["aevrynd_runtime_owned"] = True
    return mat


def density_material():
    mat = bpy.data.materials.get("Aevrynd_Brow_Density_v39") or bpy.data.materials.new("Aevrynd_Brow_Density_v39")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    vertex_color = nodes.get("Aevrynd Brow Density") or nodes.new("ShaderNodeVertexColor")
    vertex_color.name = "Aevrynd Brow Density"
    vertex_color.layer_name = "AevryndBrowDensity"
    for socket in (shader.inputs["Base Color"], shader.inputs["Alpha"]):
        for link in list(socket.links):
            links.remove(link)
    links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    links.new(vertex_color.outputs["Alpha"], shader.inputs["Alpha"])
    shader.inputs["Roughness"].default_value = 0.67
    shader.inputs["Specular IOR Level"].default_value = 0.10
    mat.surface_render_method = "DITHERED"
    mat.use_transparency_overlap = False
    mat["aevrynd_runtime_owned"] = True
    return mat


def add_fiber(vertices, faces, material_indices, points, radius, material_index, sides=3):
    base = len(vertices)
    for row, point in enumerate(points):
        previous = points[max(0, row - 1)]
        following = points[min(len(points) - 1, row + 1)]
        tangent = (following - previous).normalized()
        axis_a = tangent.cross(Vector((1.0, 0.0, 0.0)))
        if axis_a.length < 1e-8:
            axis_a = tangent.cross(Vector((0.0, 0.0, 1.0)))
        axis_a.normalize()
        axis_b = tangent.cross(axis_a).normalized()
        progress = row / (len(points) - 1)
        row_radius = radius * max(0.05, (1.0 - progress) ** 1.30)
        for side in range(sides):
            angle = math.tau * side / sides
            vertices.append(tuple(point + axis_a * math.cos(angle) * row_radius + axis_b * math.sin(angle) * row_radius))
    for row in range(len(points) - 1):
        for side in range(sides):
            a = base + row * sides + side
            b = base + row * sides + (side + 1) % sides
            c = base + (row + 1) * sides + (side + 1) % sides
            d = base + (row + 1) * sides + side
            faces.append((a, b, c, d))
            material_indices.append(material_index)


def brow_center_z(u):
    return 1.6334 + 0.0076 * math.sin(math.pi * u) ** 0.88 - 0.0015 * u


def build_density(tree, rig, side_name, sign, material):
    name = f"Brow_{side_name}_Density"
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    columns, rows = 35, 5
    vertices, faces, alphas = [], [], []
    for column in range(columns):
        u = column / (columns - 1)
        center_z = brow_center_z(u)
        thickness = (0.00225 + 0.00175 * math.sin(math.pi * u) ** 0.72) * (1.0 - 0.34 * u)
        end_taper = min(1.0, u / 0.10, (1.0 - u) / 0.12)
        for row in range(rows):
            q = row / (rows - 1) * 2.0 - 1.0
            x = sign * (0.0120 + 0.0490 * u)
            z = center_z + q * thickness
            vertices.append(front_point(tree, x, z, 0.00024))
            across = max(0.0, 1.0 - abs(q) ** 1.45)
            alphas.append(0.025 + 0.40 * across * end_taper)
    for column in range(columns - 1):
        for row in range(rows - 1):
            a = column * rows + row
            b = (column + 1) * rows + row
            faces.append((a, b, b + 1, a + 1))
    mesh = bpy.data.meshes.new(name + "MeshV39")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    density = mesh.color_attributes.new(name="AevryndBrowDensity", type="BYTE_COLOR", domain="POINT")
    for index, alpha in enumerate(alphas):
        density.data[index].color = (0.026, 0.0075, 0.0028, alpha)
    mesh.color_attributes.active_color = density
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "brow_density"
    obj["aevrynd_face_revision"] = 39
    obj["aevrynd_surface_clearance_m"] = 0.00024
    obj["aevrynd_alpha_min"] = min(alphas)
    obj["aevrynd_alpha_max"] = max(alphas)
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj


def rebuild_brow(tree, rig, side_name, sign, materials, seed):
    rng = random.Random(seed)
    name = f"Brow_{side_name}"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    count = 120
    vertices, faces, material_indices = [], [], []
    lengths = []
    for index in range(count):
        u = max(0.0, min(0.985, (index + 0.5 + rng.uniform(-0.42, 0.42)) / count))
        thickness = (0.0022 + 0.0017 * math.sin(math.pi * u) ** 0.7) * (1.0 - 0.36 * u)
        root_z = brow_center_z(u) + rng.uniform(-1.0, 1.0) * thickness
        root_x = sign * (0.0120 + 0.0490 * u)
        length = (0.0030 + 0.0028 * math.sin(math.pi * u) ** 0.55) * rng.uniform(0.72, 1.16)
        length *= 1.0 - 0.28 * max(0.0, (u - 0.82) / 0.18)
        vertical = 0.86 * (1.0 - u) - 0.20 * u + rng.uniform(-0.10, 0.10)
        horizontal = 0.44 + 0.46 * u + rng.uniform(-0.08, 0.08)
        direction = Vector((sign * horizontal, 0.0, vertical)).normalized()
        points = []
        for row in range(5):
            progress = row / 4
            target_x = root_x + direction.x * length * progress
            target_z = root_z + direction.z * length * progress - 0.00035 * progress * progress
            max_abs_x = 0.0640 + rng.uniform(-0.00015, 0.00015)
            target_x = sign * min(abs(target_x), max_abs_x)
            clearance = 0.00040 + 0.00018 * math.sin(math.pi * progress)
            points.append(front_point(tree, target_x, target_z, clearance))
        add_fiber(
            vertices, faces, material_indices, points,
            rng.uniform(0.000035, 0.000060), 1 if index % 7 in (0, 1) else 0,
        )
        lengths.append((points[-1] - points[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshV39")
    mesh.from_pydata(vertices, [], faces)
    for mat in materials:
        mesh.materials.append(mat)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.use_smooth = True
        polygon.material_index = material_index
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "brow"
    obj["aevrynd_face_revision"] = 39
    obj["aevrynd_fiber_count"] = count
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = 0.00040
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, width=900, height=900):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
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
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
tree = surface(body)
materials = (
    hair_material("Aevrynd_Brow_Hair_v39_Dark", (0.014, 0.0048, 0.0020)),
    hair_material("Aevrynd_Brow_Hair_v39_Warm", (0.035, 0.0105, 0.0038)),
)
density_mat = density_material()
brow_density = (
    build_density(tree, rig, "L", 1.0, density_mat),
    build_density(tree, rig, "R", -1.0, density_mat),
)
brows = (
    rebuild_brow(tree, rig, "L", 1.0, materials, 3901),
    rebuild_brow(tree, rig, "R", -1.0, materials, 3902),
)
bpy.context.scene["aevrynd_face_revision"] = 39
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-brows-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 96)
render(camera, "female-brows-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 96)
render(camera, "female-brows-close", (0.0, -0.43, 1.622), (0.0, -0.09, 1.622), 115, 1000, 700)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_BROWS_V39_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "layers": {obj.name: {
        "fibers": int(obj["aevrynd_fiber_count"]),
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "length_range_m": [float(obj["aevrynd_length_min_m"]), float(obj["aevrynd_length_max_m"])],
    } for obj in brows},
    "density_layers": {obj.name: {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "alpha_range": [float(obj["aevrynd_alpha_min"]), float(obj["aevrynd_alpha_max"])],
    } for obj in brow_density},
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
