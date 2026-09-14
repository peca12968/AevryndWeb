import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-upper-lash-clumps-r500.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r500-upper-lash-clump-sweep"
BODY_NAME = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-r499-current", None),
    ("b-sparse-clumps", {"clusters": 16, "meanFibers": 1.85, "lengthScale": 0.90}),
    ("c-natural-clumps", {"clusters": 19, "meanFibers": 2.20, "lengthScale": 1.00}),
    ("d-full-clumps", {"clusters": 22, "meanFibers": 2.40, "lengthScale": 1.07}),
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
        raise RuntimeError(f"Expected two 52-vertex eye boundaries, found {[len(value) for value in loops]}")
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


def upper_paths(body):
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
        paths.sort(key=lambda path: sum(world[index].z for index in path) / len(path), reverse=True)
        result[side] = [world[index].copy() for index in paths[0]]
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
        raise RuntimeError(f"Upper-lash root ray missed at x={x:.6f}, z={z:.6f}")
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
        row_radius = radius * max(0.03, (1.0 - progress) ** 1.42)
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
    source = bpy.data.materials["Aevrynd_Lash_Hair_v51"]
    material = source.copy()
    material.name = "Aevrynd_Lash_Hair_R500"
    material["aevrynd_runtime_owned"] = True
    material["aevrynd_revision"] = "v249r500-upper-lash-clumps"
    return material


def fiber_count(rng, mean):
    lower = int(math.floor(mean))
    return lower + (1 if rng.random() < mean - lower else 0)


def rebuild_upper(body_tree, rig, side, rim_points, settings, material, seed):
    name = f"Eye_{side}_UpperLashes"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    rng = random.Random(seed)
    vertices, faces, lengths, clump_sizes = [], [], [], []
    center_x = sum(point.x for point in rim_points) / len(rim_points)
    half_width = max(abs(point.x - center_x) for point in rim_points)
    clusters = settings["clusters"]
    for cluster_index in range(clusters):
        center_fraction = 0.06 + 0.88 * ((cluster_index + 0.5 + rng.uniform(-0.20, 0.20)) / clusters)
        center_rim = sample_polyline(rim_points, center_fraction)
        center_root = front_point(body_tree, center_rim.x, center_rim.z, 0.00044)
        t = max(-1.0, min(1.0, (center_rim.x - center_x) / half_width))
        outer_fraction = center_fraction if side == "L" else 1.0 - center_fraction
        envelope = math.sin(math.pi * center_fraction) ** 0.62
        count = max(1, min(3, fiber_count(rng, settings["meanFibers"])))
        clump_sizes.append(count)
        cluster_length = settings["lengthScale"] * (0.0020 + 0.00335 * envelope) * (0.76 + 0.24 * outer_fraction) * rng.uniform(0.90, 1.08)
        cluster_lateral = 0.15 * t + rng.uniform(-0.035, 0.035)
        direction = Vector((cluster_lateral, -1.0, rng.uniform(0.015, 0.15))).normalized()
        shared_tip = center_root + direction * cluster_length + Vector((
            math.copysign(rng.uniform(0.00005, 0.00022), t if abs(t) > 0.05 else (1.0 if side == "L" else -1.0)),
            rng.uniform(0.00016, 0.00034),
            rng.uniform(0.00048, 0.00105),
        ))
        for fiber_index in range(count):
            centered = fiber_index - (count - 1) * 0.5
            root_fraction = center_fraction + centered * rng.uniform(0.0033, 0.0048)
            rim = sample_polyline(rim_points, root_fraction)
            rim.z += rng.uniform(-0.00004, 0.00004)
            root = front_point(body_tree, rim.x, rim.z, 0.00044)
            tip = shared_tip + Vector((
                centered * rng.uniform(0.000025, 0.000065),
                rng.uniform(-0.000045, 0.000045),
                centered * rng.uniform(-0.000035, 0.000035),
            ))
            control = root + direction * cluster_length * rng.uniform(0.42, 0.52) + Vector((0.0, -0.00010, rng.uniform(0.00006, 0.00018)))
            points = []
            for row in range(7):
                progress = row / 6.0
                inverse = 1.0 - progress
                points.append(root * (inverse * inverse) + control * (2.0 * inverse * progress) + tip * (progress * progress))
            add_fiber(vertices, faces, points, rng.uniform(0.000026, 0.000043))
            lengths.append((points[-1] - points[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshR500")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "upper_lashes"
    obj["aevrynd_revision"] = "v249r500-upper-lash-clumps"
    obj["aevrynd_clump_count"] = clusters
    obj["aevrynd_clump_sizes"] = clump_sizes
    obj["aevrynd_fiber_count"] = sum(clump_sizes)
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = 0.00044
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
                "lower": tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph),
            }
            upper = tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
            frame_report[side] = {label: len(upper.overlap(value)) for label, value in colliders.items()}
        result[str(frame)] = frame_report
    return result


def collision_pass(snapshot):
    return all(count == 0 for frame in snapshot.values() for side in frame.values() for count in side.values())


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
    objects, snapshot = [], None
    if settings is not None:
        body = bpy.data.objects[BODY_NAME]
        rig = bpy.data.objects["AevryndFemaleRig"]
        body_tree = tree(body, bpy.context.evaluated_depsgraph_get())
        paths = upper_paths(body)
        material = lash_material()
        for side_index, side in enumerate(("L", "R")):
            objects.append(rebuild_upper(body_tree, rig, side, paths[side], settings, material, 50000 + variant_index * 100 + side_index * 10))
        snapshot = collision_snapshot(scene)
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-lash-oblique", (0.18, -0.34, 1.616), (0.033, -0.113, 1.609), 125, (1200, 900))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    report["variants"][label] = {
        "settings": settings,
        "layers": {
            obj.name: {
                "clumps": int(obj["aevrynd_clump_count"]),
                "clumpSizes": list(obj["aevrynd_clump_sizes"]),
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
report["visualAssessment"] = {"status": "REJECTED", "reason": "Rebuilt fibers disappear into the lid surface and leave skin-colored folds instead of readable lashes.", "promotion": None}
report["status"] = "REJECTED_VISUAL_GATE"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R500_UPPER_LASH_CLUMPS=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))
