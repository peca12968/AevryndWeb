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
REPORT = ASSETS / "female-v249-mainline-lash-density-r497.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r497-lash-density-sweep"
BODY_NAME = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-r496-current", None),
    ("b-natural-light", {"upper": 52, "lower": 18, "upperScale": 0.92, "lowerScale": 0.88}),
    ("c-balanced", {"upper": 58, "lower": 22, "upperScale": 1.00, "lowerScale": 1.00}),
    ("d-full", {"upper": 64, "lower": 26, "upperScale": 1.08, "lowerScale": 1.12}),
    ("e-lower-sparse", {"upper": None, "lower": 12, "lowerScale": 0.82}),
    ("f-lower-natural", {"upper": None, "lower": 16, "lowerScale": 0.94}),
    ("g-lower-full", {"upper": None, "lower": 20, "lowerScale": 1.04}),
)


def mesh_geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = mesh_geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def boundary_loops(body):
    edge_uses = {}
    for polygon in body.data.polygons:
        indices = list(polygon.vertices)
        for index, a in enumerate(indices):
            b = indices[(index + 1) % len(indices)]
            key = tuple(sorted((a, b)))
            edge_uses[key] = edge_uses.get(key, 0) + 1
    adjacency = {}
    for (a, b), count in edge_uses.items():
        if count != 1:
            continue
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
    loops = []
    seen = set()
    for start in adjacency:
        if start in seen:
            continue
        component = []
        stack = [start]
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
        raise RuntimeError(f"Expected two 52-vertex eye loops, found {[len(loop) for loop in loops]}")
    return loops, adjacency


def walk_path(adjacency, start, first, end):
    path = [start, first]
    previous, current = start, first
    while current != end:
        candidates = [value for value in adjacency[current] if value != previous]
        if len(candidates) != 1:
            raise RuntimeError("Eye boundary is not a simple loop")
        previous, current = current, candidates[0]
        if current in path and current != end:
            raise RuntimeError("Eye boundary path looped before the opposite canthus")
        path.append(current)
    return path


def ordered_lid_paths(body):
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    world = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    loops, adjacency = boundary_loops(body)
    result = {}
    for loop in loops:
        center_x = sum(world[index].x for index in loop) / len(loop)
        side = "L" if center_x > 0.0 else "R"
        left = min(loop, key=lambda index: world[index].x)
        right = max(loop, key=lambda index: world[index].x)
        first, second = adjacency[left]
        paths = [walk_path(adjacency, left, first, right), walk_path(adjacency, left, second, right)]
        paths.sort(key=lambda path: sum(world[index].z for index in path) / len(path), reverse=True)
        result[side] = {
            "upper": [world[index].copy() for index in paths[0]],
            "lower": [world[index].copy() for index in paths[1]],
            "centerX": center_x,
        }
    evaluated.to_mesh_clear()
    return result


def sample_polyline(points, fraction):
    lengths = [(points[index + 1] - points[index]).length for index in range(len(points) - 1)]
    target = max(0.0, min(1.0, fraction)) * sum(lengths)
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
        raise RuntimeError(f"Lash root ray missed at x={x:.6f}, z={z:.6f}")
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


def lash_material():
    material = bpy.data.materials.get("Aevrynd_Lash_Hair_R497") or bpy.data.materials.new("Aevrynd_Lash_Hair_R497")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.0048, 0.00155, 0.00082, 1.0)
    shader.inputs["Roughness"].default_value = 0.48
    shader.inputs["Specular IOR Level"].default_value = 0.12
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.28
    material["aevrynd_runtime_owned"] = True
    return material


def rebuild_layer(body_tree, rig, side, points, upper, count, scale, material, seed):
    kind = "Upper" if upper else "Lower"
    name = f"Eye_{side}_{kind}Lashes"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    rng = random.Random(seed)
    vertices, faces, lengths = [], [], []
    center_x = sum(point.x for point in points) / len(points)
    half_width = max(abs(point.x - center_x) for point in points)
    for index in range(count):
        fraction = 0.055 + 0.89 * ((index + 0.5 + rng.uniform(-0.27, 0.27)) / count)
        rim = sample_polyline(points, fraction)
        rim.z += rng.uniform(-0.000055, 0.000055)
        clearance = 0.00038 if upper else 0.00042
        root = front_point(body_tree, rim.x, rim.z, clearance)
        t = max(-1.0, min(1.0, (rim.x - center_x) / half_width))
        outer_fraction = fraction if side == "L" else 1.0 - fraction
        envelope = math.sin(math.pi * fraction) ** 0.62
        pair_lean = (0.030 if index % 2 == 0 else -0.030) * rng.uniform(0.72, 1.18)
        lateral = 0.16 * t + pair_lean
        if upper:
            length = scale * (0.00215 + 0.00345 * envelope) * (0.78 + 0.22 * outer_fraction) * rng.uniform(0.88, 1.10)
            direction = Vector((lateral, -1.0, rng.uniform(0.10, 0.24))).normalized()
            curl_z = rng.uniform(0.00120, 0.00172)
            curl_y = rng.uniform(0.00025, 0.00042)
            radius = rng.uniform(0.000025, 0.000041)
        else:
            length = scale * (0.00072 + 0.00142 * envelope) * (0.76 + 0.24 * outer_fraction) * rng.uniform(0.86, 1.12)
            direction = Vector((0.12 * t + pair_lean * 0.65, -1.0, -rng.uniform(0.12, 0.26))).normalized()
            curl_z = -rng.uniform(0.00018, 0.00034)
            curl_y = rng.uniform(0.00008, 0.00018)
            radius = rng.uniform(0.000016, 0.000027)
        fiber = [root]
        for row in range(1, 7):
            progress = row / 6.0
            fiber.append(root + direction * length * progress + Vector((0.0, curl_y, curl_z)) * progress * progress)
        add_fiber(vertices, faces, fiber, radius)
        lengths.append((fiber[-1] - fiber[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshR497")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "upper_lashes" if upper else "lower_lashes"
    obj["aevrynd_revision"] = "v249r497"
    obj["aevrynd_fiber_count"] = count
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = clearance
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


def collision_snapshot(scene):
    result = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY_NAME], depsgraph)
        frame_report = {}
        for side in ("L", "R"):
            colliders = {
                "body": body_tree,
                "cornea": tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph),
                "sclera": tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph),
                "tear": tree(bpy.data.objects[f"Eye_{side}_TearMeniscus"], depsgraph),
                "caruncle": tree(bpy.data.objects[f"Eye_{side}_Caruncle"], depsgraph),
            }
            upper = tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
            lower = tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
            values = {
                "upper": {label: len(upper.overlap(value)) for label, value in colliders.items()},
                "lower": {label: len(lower.overlap(value)) for label, value in colliders.items()},
                "upperLower": len(upper.overlap(lower)),
            }
            frame_report[side] = values
        result[str(frame)] = frame_report
    return result


def collision_pass(snapshot):
    return all(
        count == 0
        for frame in snapshot.values()
        for side in frame.values()
        for count in list(side["upper"].values()) + list(side["lower"].values()) + [side["upperLower"]]
    )


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "renderDirectory": str(RENDER_DIR)}
for variant_index, (label, settings) in enumerate(VARIANTS):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    objects = []
    snapshot = None
    if settings is not None:
        body = bpy.data.objects[BODY_NAME]
        rig = bpy.data.objects["AevryndFemaleRig"]
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(body, depsgraph)
        paths = ordered_lid_paths(body)
        material = lash_material()
        for side_index, side in enumerate(("L", "R")):
            if settings["upper"] is not None:
                objects.append(rebuild_layer(body_tree, rig, side, paths[side]["upper"], True, settings["upper"], settings["upperScale"], material, 49700 + variant_index * 100 + side_index * 10))
            objects.append(rebuild_layer(body_tree, rig, side, paths[side]["lower"], False, settings["lower"], settings["lowerScale"], material, 49701 + variant_index * 100 + side_index * 10))
        snapshot = collision_snapshot(scene)
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    render(scene, camera, label + "-lash-oblique", (0.18, -0.34, 1.616), (0.033, -0.113, 1.609), 125, (1200, 900))
    report["variants"][label] = {
        "settings": settings,
        "layers": {
            obj.name: {
                "fibers": int(obj["aevrynd_fiber_count"]),
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "lengthRangeM": [float(obj["aevrynd_length_min_m"]), float(obj["aevrynd_length_max_m"])],
            }
            for obj in objects
        },
        "collision": snapshot,
        "collisionStatus": "NOT_APPLICABLE_BASELINE" if snapshot is None else ("PASS" if collision_pass(snapshot) else "FAIL"),
    }
report["status"] = "VISUAL_REVIEW_REQUIRED"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R497_LASH_SWEEP=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))
