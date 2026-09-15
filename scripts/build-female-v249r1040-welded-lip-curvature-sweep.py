"""Smooth the six welded mouth rings and author upper/lower lip curvature."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-separated-vermilion-r1039-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-welded-lip-curvature-r1040-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1040-welded-lip-curvature-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1040-welded-lip-curvature-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
VARIANTS = (
    ("a-soft", 0.40, 0.00055),
    ("b-balanced", 0.62, 0.00085),
)
SELECTED = "b-balanced"
CENTER_Z = 1.3893


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coords):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coords]


def ordered_mouth_boundary(body):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    vertex_edges = defaultdict(set)
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    all_edges = [edge for edge, count in users.items() if count == 1]
    for index, edge in enumerate(all_edges):
        for vertex in edge:
            vertex_edges[vertex].add(index)
    remaining = set(range(len(all_edges)))
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            edge_index = stack.pop()
            neighbours = set()
            for vertex in all_edges[edge_index]:
                neighbours.update(vertex_edges[vertex])
            fresh = neighbours & remaining
            remaining.difference_update(fresh)
            component.update(fresh)
            stack.extend(fresh)
        vertices = {vertex for edge_index in component for vertex in all_edges[edge_index]}
        center = sum((points[index] for index in vertices), Vector()) / len(vertices)
        if len(component) == 120 and abs(center.x) < 0.002 and abs(center.z - CENTER_Z) < 0.010:
            component_edges = [all_edges[index] for index in component]
            adjacency = defaultdict(set)
            for first, second in component_edges:
                adjacency[first].add(second)
                adjacency[second].add(first)
            if any(len(neighbours) != 2 for neighbours in adjacency.values()):
                raise RuntimeError("Mouth boundary is not a simple closed loop")
            start = min(adjacency, key=lambda index: (points[index].x, points[index].z))
            ordered = [start]
            previous = None
            current = start
            while True:
                candidates = adjacency[current] - ({previous} if previous is not None else set())
                if previous is None:
                    nxt = min(candidates, key=lambda index: points[index].z)
                else:
                    nxt = next(iter(candidates))
                if nxt == start:
                    break
                ordered.append(nxt)
                previous, current = current, nxt
            if len(ordered) != 120:
                raise RuntimeError(f"Ordered mouth boundary has {len(ordered)} vertices")
            return ordered
    raise RuntimeError("The welded 120-edge r1035 mouth boundary was not found")


def welded_ring_stack(body):
    points = mixed_coordinates(body)
    adjacency = defaultdict(set)
    for edge in body.data.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    rings = [ordered_mouth_boundary(body)]
    previous = set()
    for _ in range(5):
        current = rings[-1]
        current_set = set(current)
        next_ring = []
        for vertex in current:
            candidates = adjacency[vertex] - current_set - previous
            if len(candidates) != 1:
                raise RuntimeError(f"Welded ring mapping is not one-to-one at {vertex}: {sorted(candidates)}")
            next_ring.append(next(iter(candidates)))
        if len(set(next_ring)) != 120:
            raise RuntimeError("Welded ring mapping contains duplicates")
        rings.append(next_ring)
        previous = current_set
    return points, rings


def preserve_extents(original, smoothed):
    ox0, ox1 = min(point.x for point in original), max(point.x for point in original)
    oz0, oz1 = min(point.z for point in original), max(point.z for point in original)
    sx0, sx1 = min(point.x for point in smoothed), max(point.x for point in smoothed)
    sz0, sz1 = min(point.z for point in smoothed), max(point.z for point in smoothed)
    ocx, ocz = (ox0 + ox1) * 0.5, (oz0 + oz1) * 0.5
    scx, scz = (sx0 + sx1) * 0.5, (sz0 + sz1) * 0.5
    scale_x = (ox1 - ox0) / max(1e-9, sx1 - sx0)
    scale_z = (oz1 - oz0) / max(1e-9, sz1 - sz0)
    return [Vector((ocx + (point.x - scx) * scale_x, point.y, ocz + (point.z - scz) * scale_z)) for point in smoothed]


def smooth_ring(original, strength):
    work = [point.copy() for point in original]
    for _ in range(4):
        averaged = []
        for index, point in enumerate(work):
            neighbour_average = (work[index - 1] + work[(index + 1) % len(work)]) * 0.5
            averaged.append(point.copy().lerp(neighbour_average, 0.28 * strength))
        work = preserve_extents(original, averaged)
    return work


def reshape_welded_curvature(body, smoothing_strength, bulge):
    points, rings = welded_ring_stack(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    targets = {}
    depth_offsets = (0.65, 0.38, -0.12, -0.58, -1.0, 0.0)
    for ring_index, ring in enumerate(rings):
        original = [points[index] for index in ring]
        smoothed = smooth_ring(original, smoothing_strength)
        for vertex_index, target in zip(ring, smoothed):
            upper_factor = 0.82 if target.z >= CENTER_Z else 1.12
            if ring_index == 4:
                target.y -= bulge * upper_factor
            else:
                target.y += bulge * depth_offsets[ring_index] * upper_factor
            if target.z >= CENTER_Z and ring_index in (3, 4, 5):
                cupid = math.exp(-0.5 * ((abs(target.x) - 0.0105) / 0.0040) ** 2)
                notch = math.exp(-0.5 * (target.x / 0.0038) ** 2)
                target.z += smoothing_strength * (0.00020 * cupid - 0.00010 * notch) * ((ring_index - 2) / 3.0)
            targets[vertex_index] = target
    deltas = {index: inverse3 @ (target - points[index]) for index, target in targets.items()}
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    body.data.update()
    lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    return {
        "vertices": len(body.data.vertices),
        "weldedRings": 6,
        "verticesPerRing": 120,
        "changedVertices": 720,
        "maximumDeltaMm": max(delta.length for delta in deltas.values()) * 1000.0,
        "meanDeltaMm": sum(delta.length for delta in deltas.values()) / len(deltas) * 1000.0,
        "shapeKeyCount": len(lengths),
        "shapeKeyCompatibility": len(set(lengths.values())) == 1,
        "weldedSingleObject": True,
    }


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = evaluated_tree(body, depsgraph)
    pairs = [(first, second) for first, second in tree.overlap(tree) if first < second and set(triangles[first]).isdisjoint(triangles[second])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


def oral_collision(body, layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = evaluated_tree(body, depsgraph)
    overlaps = {}
    for layer in layers:
        tree, _ = evaluated_tree(layer, depsgraph)
        overlaps[layer.name] = len(body_tree.overlap(tree))
    return {"triangleOverlap": overlaps, "status": "PASS" if not any(overlaps.values()) else "FAIL"}


def audit_state(scene, body, layers, frame, expression=None):
    scene.frame_set(frame)
    keys = body.data.shape_keys.key_blocks
    old_open, old_smile = float(keys[OPEN_KEY].value), float(keys[SMILE_KEY].value)
    keys[OPEN_KEY].value = 1.0 if expression == OPEN_KEY else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == SMILE_KEY else 0.0
    bpy.context.view_layer.update()
    result = {"frame": frame, "expression": expression or "neutral", "bodySelf": body_self_collision(body), "bodyOral": oral_collision(body, layers)}
    result["status"] = "PASS" if result["bodySelf"]["status"] == "PASS" and result["bodyOral"]["status"] == "PASS" else "FAIL"
    keys[OPEN_KEY].value, keys[SMILE_KEY].value = old_open, old_smile
    bpy.context.view_layer.update()
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / (label + ".png")
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for values in VARIANTS:
    label, smoothing_strength, bulge = values
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
    topology = reshape_welded_curvature(body, smoothing_strength, bulge)
    states = [audit_state(scene, body, layers, frame) for frame in (1, 20, 33, 61)]
    states.extend(audit_state(scene, body, layers, 1, expression) for expression in (OPEN_KEY, SMILE_KEY))
    scene.frame_set(1)
    body.data.shape_keys.key_blocks[OPEN_KEY].value = 0.0
    body.data.shape_keys.key_blocks[SMILE_KEY].value = 0.0
    hidden = hide_hair(scene)
    rendered = [
        render(scene, label + "-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
        render(scene, label + "-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
        render(scene, label + "-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
    ]
    for expression, suffix in ((OPEN_KEY, "open"), (SMILE_KEY, "smile")):
        body.data.shape_keys.key_blocks[expression].value = 1.0
        bpy.context.view_layer.update()
        rendered.append(render(scene, label + "-" + suffix, (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
        body.data.shape_keys.key_blocks[expression].value = 0.0
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    technical = all(state["status"] == "PASS" for state in states)
    item = {
        "label": label,
        "parameters": {"smoothingStrength": smoothing_strength, "lipBulgeM": bulge, "weldedRings": 6},
        "topology": topology,
        "states": states,
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL",
    }
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1040-welded-lip-curvature"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "extent-preserving tangential smoothing across six welded rings plus separate upper/lower lip depth curvature",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED if next(item for item in variants if item["label"] == SELECTED)["status"] == "TECHNICAL_PASS" else None,
    "skinToneContract": "No skin material, scene light, exposure or color-management change; website v83 remains 5.56% darker than committed mainline",
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1040_WELDED_CURVATURE=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "states": [state["status"] for state in item["states"]], "status": item["status"]} for item in variants]}, sort_keys=True))
