import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-sclera-r496.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-lower-lashes-r498.blend"
REPORT = ASSETS / "female-v249-mainline-natural-lower-lashes-r498.build-report.json"
REVIEW_DIR = ASSETS / "reviews" / "v249r498-natural-lower-lashes"
BODY_NAME = "AevryndFemaleBodyBaseV118"


def geometry_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def boundary_data(body):
    edge_uses = {}
    for polygon in body.data.polygons:
        indices = list(polygon.vertices)
        for index, a in enumerate(indices):
            b = indices[(index + 1) % len(indices)]
            key = tuple(sorted((a, b)))
            edge_uses[key] = edge_uses.get(key, 0) + 1
    adjacency = {}
    for (a, b), count in edge_uses.items():
        if count == 1:
            adjacency.setdefault(a, []).append(b)
            adjacency.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in adjacency:
        if start in seen:
            continue
        stack, component = [start], []
        seen.add(start)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        if len(component) == 52:
            loops.append(component)
    if len(loops) != 2:
        raise RuntimeError(f"Expected two eye boundaries, found {[len(value) for value in loops]}")
    return loops, adjacency


def walk(adjacency, start, first, end):
    path = [start, first]
    previous, current = start, first
    while current != end:
        candidates = [value for value in adjacency[current] if value != previous]
        if len(candidates) != 1:
            raise RuntimeError("Eye boundary is not a simple loop")
        previous, current = current, candidates[0]
        path.append(current)
    return path


def lower_lid_paths(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    world = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    loops, adjacency = boundary_data(body)
    result = {}
    for loop in loops:
        center_x = sum(world[index].x for index in loop) / len(loop)
        side = "L" if center_x > 0.0 else "R"
        left = min(loop, key=lambda index: world[index].x)
        right = max(loop, key=lambda index: world[index].x)
        paths = [walk(adjacency, left, first, right) for first in adjacency[left]]
        paths.sort(key=lambda path: sum(world[index].z for index in path) / len(path))
        result[side] = [world[index].copy() for index in paths[0]]
    evaluated.to_mesh_clear()
    return result


def sample_polyline(points, fraction):
    lengths = [(points[index + 1] - points[index]).length for index in range(len(points) - 1)]
    target = fraction * sum(lengths)
    travelled = 0.0
    for index, length in enumerate(lengths):
        if travelled + length >= target or index == len(lengths) - 1:
            amount = 0.0 if length == 0.0 else (target - travelled) / length
            return points[index].lerp(points[index + 1], amount)
        travelled += length
    return points[-1].copy()


def front_point(body_tree, x, z, clearance):
    location, normal, _, _ = body_tree.ray_cast(Vector((x, -0.34, z)), Vector((0.0, 1.0, 0.0)), 0.6)
    if location is None:
        raise RuntimeError(f"Lower-lash root ray missed at x={x:.6f}, z={z:.6f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def add_fiber(vertices, faces, points, radius, sides=3):
    base = len(vertices)
    rows = len(points)
    for row, point in enumerate(points):
        previous = points[max(0, row - 1)]
        following = points[min(rows - 1, row + 1)]
        tangent = (following - previous).normalized()
        axis_a = tangent.cross(Vector((1.0, 0.0, 0.0)))
        if axis_a.length < 1e-8:
            axis_a = tangent.cross(Vector((0.0, 0.0, 1.0)))
        axis_a.normalize()
        axis_b = tangent.cross(axis_a).normalized()
        progress = row / (rows - 1)
        row_radius = radius * max(0.035, (1.0 - progress) ** 1.35)
        for side in range(sides):
            angle = math.tau * side / sides
            vertices.append(tuple(point + axis_a * math.cos(angle) * row_radius + axis_b * math.sin(angle) * row_radius))
    for row in range(rows - 1):
        for side in range(sides):
            a = base + row * sides + side
            b = base + row * sides + (side + 1) % sides
            c = base + (row + 1) * sides + (side + 1) % sides
            d = base + (row + 1) * sides + side
            faces.append((a, b, c, d))
    faces.append(tuple(base + side for side in reversed(range(sides))))
    tip = base + (rows - 1) * sides
    faces.append(tuple(tip + side for side in range(sides)))


def material():
    value = bpy.data.materials.get("Aevrynd_Lash_Hair_R498") or bpy.data.materials.new("Aevrynd_Lash_Hair_R498")
    value.use_nodes = True
    shader = next(node for node in value.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.0048, 0.00155, 0.00082, 1.0)
    shader.inputs["Roughness"].default_value = 0.48
    shader.inputs["Specular IOR Level"].default_value = 0.12
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.28
    value["aevrynd_runtime_owned"] = True
    return value


def build_lower(body_tree, rig, side, rim_points, value, seed):
    name = f"Eye_{side}_LowerLashes"
    rng = random.Random(seed)
    vertices, faces, lengths = [], [], []
    count, scale = 16, 0.94
    center_x = sum(point.x for point in rim_points) / len(rim_points)
    half_width = max(abs(point.x - center_x) for point in rim_points)
    for index in range(count):
        fraction = 0.055 + 0.89 * ((index + 0.5 + rng.uniform(-0.27, 0.27)) / count)
        rim = sample_polyline(rim_points, fraction)
        rim.z += rng.uniform(-0.000055, 0.000055)
        root = front_point(body_tree, rim.x, rim.z, 0.00042)
        t = max(-1.0, min(1.0, (rim.x - center_x) / half_width))
        outer_fraction = fraction if side == "L" else 1.0 - fraction
        envelope = math.sin(math.pi * fraction) ** 0.62
        pair_lean = (0.030 if index % 2 == 0 else -0.030) * rng.uniform(0.72, 1.18)
        length = scale * (0.00072 + 0.00142 * envelope) * (0.76 + 0.24 * outer_fraction) * rng.uniform(0.86, 1.12)
        direction = Vector((0.12 * t + pair_lean * 0.65, -1.0, -rng.uniform(0.12, 0.26))).normalized()
        curl = Vector((0.0, rng.uniform(0.00008, 0.00018), -rng.uniform(0.00018, 0.00034)))
        points = [root]
        for row in range(1, 7):
            progress = row / 6.0
            points.append(root + direction * length * progress + curl * progress * progress)
        add_fiber(vertices, faces, points, rng.uniform(0.000016, 0.000027))
        lengths.append((points[-1] - points[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshR498")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(value)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "lower_lashes"
    obj["aevrynd_revision"] = "v249r498-natural-lower-lashes"
    obj["aevrynd_fiber_count"] = count
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = 0.00042
    obj["aevrynd_ownership"] = "Aevrynd deterministic authored geometry"
    group = obj.vertex_groups.new(name="head")
    group.add(list(range(len(vertices))), 1.0, "REPLACE")
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_world = Matrix.Identity(4)
    modifier = obj.modifiers.new("Aevrynd Head Follow", "ARMATURE")
    modifier.object = rig
    modifier.use_vertex_groups = True
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY_NAME]
rig = bpy.data.objects["AevryndFemaleRig"]
depsgraph = bpy.context.evaluated_depsgraph_get()
body_tree = geometry_tree(body, depsgraph)
paths = lower_lid_paths(body)
lash_material = material()
lashes = [
    build_lower(body_tree, rig, "L", paths["L"], lash_material, 50201),
    build_lower(body_tree, rig, "R", paths["R"], lash_material, 50211),
]
scene["aevrynd_mainline_revision"] = "v249r498-natural-lower-lashes"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "NATURAL_LOWER_LASH_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for values in (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-lash-oblique-f01", (0.18, -0.34, 1.616), (0.033, -0.113, 1.609), 125, (1200, 900)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selection": "f-lower-natural",
    "selectionReason": "Sixteen fibers per eye remain visibly sparse at macro range without forming a continuous cosmetic lower-lid shadow.",
    "preservedUpperLashes": True,
    "layers": {
        obj.name: {
            "fibers": int(obj["aevrynd_fiber_count"]),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "lengthRangeM": [float(obj["aevrynd_length_min_m"]), float(obj["aevrynd_length_max_m"])],
        }
        for obj in lashes
    },
    "ownedAssetOnly": True,
    "reviewDirectory": str(REVIEW_DIR),
    "status": "FORMAL_GATES_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R498_LOWER_LASHES=" + json.dumps(report, sort_keys=True))
