import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v37.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v38.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v38.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v38-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "lashes-v38"
RNG = random.Random(3801)


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_point(tree, x, z, clearance):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.36, z)), Vector((0.0, 1.0, 0.0)), 0.7)
    if location is None:
        raise RuntimeError(f"lash ray missed at {x:.5f}, {z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def lash_material():
    mat = bpy.data.materials.get("Aevrynd_Lash_Hair_v38") or bpy.data.materials.new("Aevrynd_Lash_Hair_v38")
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.0042, 0.0013, 0.00065, 1.0)
    shader.inputs["Roughness"].default_value = 0.46
    shader.inputs["Specular IOR Level"].default_value = 0.14
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.32
    mat["aevrynd_runtime_owned"] = True
    return mat


def add_tapered_fiber(vertices, faces, points, radius, sides=3):
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
        row_radius = radius * max(0.06, (1.0 - progress) ** 1.25)
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


def rebuild_lashes(tree, rig, side, center_x, upper, material):
    kind = "Upper" if upper else "Lower"
    name = f"Eye_{side}_{kind}Lashes"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    count = 26 if upper else 12
    vertices, faces = [], []
    lengths = []
    for index in range(count):
        fraction = (index + 0.5 + RNG.uniform(-0.31, 0.31)) / count
        t = fraction * 2.0 - 1.0
        x = center_x + t * (0.0174 if upper else 0.0167)
        arc = math.sqrt(max(0.0, 1.0 - t * t))
        z = 1.60755 + (0.00515 * arc if upper else -0.00410 * arc)
        z += RNG.uniform(-0.00012, 0.00012)
        root = front_point(tree, x, z, 0.00046)
        envelope = math.sin(math.pi * fraction) ** 0.55
        temple_sign = 1.0 if center_x > 0.0 else -1.0
        outward_position = t * temple_sign
        outer_length = 0.58 + 0.42 * (outward_position + 1.0) * 0.5
        if upper:
            length = (0.0030 + 0.0050 * envelope) * outer_length * RNG.uniform(0.68, 1.24)
            z_sign = RNG.uniform(0.38, 0.82) + 0.08 * envelope
            forward = RNG.uniform(0.72, 0.92)
        else:
            length = (0.0019 + 0.0027 * envelope) * outer_length * RNG.uniform(0.65, 1.20)
            z_sign = -RNG.uniform(0.32, 0.60)
            forward = RNG.uniform(0.76, 0.94)
        outward_sign = 1.0 if t >= 0.0 else -1.0
        lateral = temple_sign * (0.06 + 0.25 * max(0.0, outward_position))
        # Neighboring pairs lean slightly toward a shared direction, creating
        # natural micro-clumps without the regular picket-fence silhouette.
        cluster = 0.13 if index % 2 == 0 else -0.13
        cluster *= RNG.uniform(0.72, 1.18)
        direction = Vector((lateral + cluster, -forward, z_sign)).normalized()
        points = [root]
        for row in range(1, 5):
            progress = row / 4
            curl = Vector((
                temple_sign * RNG.uniform(0.00022, 0.00048) * progress * progress,
                -0.00055 * math.sin(math.pi * progress),
                (0.00075 if upper else -0.00032) * progress * progress,
            ))
            points.append(root + direction * length * progress + curl)
        add_tapered_fiber(vertices, faces, points, RNG.uniform(0.000048, 0.000080))
        lengths.append((points[-1] - points[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshV38")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "upper_lashes" if upper else "lower_lashes"
    obj["aevrynd_eye_revision"] = 38
    obj["aevrynd_fiber_count"] = count
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = 0.00046
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
mat = lash_material()
lashes = []
for side, center_x in (("L", 0.0345), ("R", -0.0345)):
    lashes.append(rebuild_lashes(tree, rig, side, center_x, True, mat))
    lashes.append(rebuild_lashes(tree, rig, side, center_x, False, mat))
bpy.context.scene["aevrynd_eye_revision"] = 38
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-lashes-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 96)
render(camera, "female-lashes-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 96)
render(camera, "female-lashes-close", (0.0, -0.43, 1.603), (0.0, -0.09, 1.605), 115, 1000, 700)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_LASHES_V38_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "layers": {obj.name: {
        "fibers": int(obj["aevrynd_fiber_count"]),
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "length_range_m": [float(obj["aevrynd_length_min_m"]), float(obj["aevrynd_length_max_m"])],
    } for obj in lashes},
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
