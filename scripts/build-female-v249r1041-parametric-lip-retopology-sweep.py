"""Reparameterize the six welded mouth rings as an even lip surface."""

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
OUTPUT = ASSETS / "aevrynd-female-cc0-parametric-lip-retopology-r1041-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1041-parametric-lip-retopology-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1041-parametric-lip-retopology-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
VARIANTS = (
    ("f-locked-seam-035", 0.35),
)
SELECTED = "f-locked-seam-035"
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


def reshape_parametric_lips(body, strength):
    points, rings = welded_ring_stack(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    targets = {}
    radii = (0.0228, 0.0233, 0.0240, 0.0248, 0.0256, 0.02615)
    upper_amplitudes = (0.00075, 0.00125, 0.00200, 0.00305, 0.00410, 0.00445)
    lower_amplitudes = (0.00038, 0.00082, 0.00155, 0.00255, 0.00355, 0.00405)
    y_offsets = (0.00260, 0.00120, -0.00005, -0.00070, -0.00105, 0.0)
    outer_ring = rings[5]
    for order_index, outer_index in enumerate(outer_ring):
        outer_point = points[outer_index]
        # ordered_mouth_boundary starts at the left commissure and follows
        # the lower arc first. A monotonic analytic angle prevents the local
        # reversals produced by inferring theta from the irregular cut edge.
        theta = math.pi + 2.0 * math.pi * order_index / len(outer_ring)
        cosine, sine = math.cos(theta), math.sin(theta)
        upper = sine >= 0.0
        for ring_index, ring in enumerate(rings):
            vertex_index = ring[order_index]
            if ring_index == 5:
                targets[vertex_index] = points[vertex_index].copy()
                continue
            amplitude = upper_amplitudes[ring_index] if upper else lower_amplitudes[ring_index]
            x = radii[ring_index] * cosine
            z = CENTER_Z + math.copysign(amplitude * abs(sine), sine)
            if upper and ring_index >= 3:
                cupid = math.exp(-0.5 * ((abs(x) - 0.0105) / 0.0038) ** 2)
                notch = math.exp(-0.5 * (x / 0.0035) ** 2)
                z += (0.00042 * cupid - 0.00024 * notch) * ((ring_index - 2) / 3.0)
            depth_factor = 0.84 if upper else 1.12
            target = Vector((x, outer_point.y + y_offsets[ring_index] * depth_factor, z))
            targets[vertex_index] = points[vertex_index].copy().lerp(target, strength)
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
        "parameterizationStrength": strength,
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
    label, strength = values
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
    topology = reshape_parametric_lips(body, strength)
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
        "parameters": {"parameterizationStrength": strength, "weldedRings": 6, "commissureMode": "shared angular endpoints"},
        "topology": topology,
        "states": states,
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL",
    }
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1041-parametric-lip-retopology"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REJECTED_SCORE_31"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "single-angle six-ring parameterization with bounded face seam, staged lip curvature, inner wetline and shared commissure endpoints",
    "variants": variants,
    "technicalSelection": SELECTED,
    "selectedVariant": SELECTED if next(item for item in variants if item["label"] == SELECTED)["status"] == "TECHNICAL_PASS" else None,
    "skinToneContract": "No skin material, scene light, exposure or color-management change; website v83 remains 5.56% darker than committed mainline",
    "strictVisualReview": {
        "mouthScore": 31,
        "retainedMainlineMouthScore": 39,
        "verdict": "REJECTED_BELOW_R1033",
        "failures": [
            "upper lip reads as a hard attached strip",
            "lower lip carries a broad white highlight band",
            "commissures terminate in visible spikes",
            "oral cavity and dental layers remain planar",
        ],
    },
    "rejectedHigherBound": {
        "label": "g-locked-seam-050",
        "parameterizationStrength": 0.50,
        "verdict": "TECHNICAL_FAIL",
        "reason": "All four rig frames plus mouth-open and smile produced non-adjacent body self-collision in the completed diagnostic run; excluded from the final rerun after Blender crashed during its last redundant render.",
    },
    "websitePromotionApproved": False,
    "status": "TECHNICAL_PASS_VISUAL_REJECTED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1041_PARAMETRIC_LIP=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "states": [state["status"] for state in item["states"]], "status": item["status"]} for item in variants]}, sort_keys=True))
