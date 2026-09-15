"""Reshape the welded r1035 mouth rings into a continuous facial lip annulus."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-contiguous-mouth-aperture-r1035-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-welded-lip-annulus-r1037-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1037-welded-lip-annulus-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1037-welded-lip-annulus-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
VARIANTS = (
    ("g-strength-015", 0.0270, 0.0255, 0.0235, 0.0050, 0.0045, 0.00090, 0.00045, 0.0010, 0.15),
    ("h-strength-030", 0.0270, 0.0255, 0.0235, 0.0050, 0.0045, 0.00090, 0.00045, 0.0010, 0.30),
    ("i-strength-045", 0.0270, 0.0255, 0.0235, 0.0050, 0.0045, 0.00090, 0.00045, 0.0010, 0.45),
)
SELECTED = "h-strength-030"
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


def topology_maps(body):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    vertex_edges = defaultdict(set)
    adjacency = defaultdict(set)
    boundary_edges = []
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    all_edges = [edge for edge, count in users.items() if count == 1]
    for index, edge in enumerate(all_edges):
        for vertex in edge:
            vertex_edges[vertex].add(index)
    remaining = set(range(len(all_edges)))
    components = []
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
        components.append(component)
    for component in components:
        vertices = {vertex for edge_index in component for vertex in all_edges[edge_index]}
        center = sum((points[index] for index in vertices), Vector()) / len(vertices)
        if len(component) == 120 and abs(center.x) < 0.002 and abs(center.z - CENTER_Z) < 0.010:
            boundary_edges = [all_edges[index] for index in component]
            break
    if not boundary_edges:
        raise RuntimeError("The welded 120-edge r1035 mouth boundary was not found")
    for edge in body.data.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    inner = {vertex for edge in boundary_edges for vertex in edge}
    middle = {next(iter(adjacency[vertex] - inner)) for vertex in inner}
    outer = set()
    inner_to_middle = {}
    middle_to_outer = {}
    for vertex in inner:
        candidates = adjacency[vertex] & middle
        if len(candidates) != 1:
            raise RuntimeError(f"Inner-to-middle mapping is not one-to-one at {vertex}: {sorted(candidates)}")
        inner_to_middle[vertex] = next(iter(candidates))
    for middle_vertex in middle:
        candidates = adjacency[middle_vertex] - inner - middle
        if len(candidates) != 1:
            raise RuntimeError(f"Middle-to-outer mapping is not one-to-one at {middle_vertex}: {sorted(candidates)}")
        outer_vertex = next(iter(candidates))
        middle_to_outer[middle_vertex] = outer_vertex
        outer.add(outer_vertex)
    if not (len(inner) == len(middle) == len(outer) == 120):
        raise RuntimeError(f"Unexpected welded ring sizes: {len(inner)}, {len(middle)}, {len(outer)}")
    return points, inner_to_middle, middle_to_outer


def lip_z(x, sine, upper_amp, lower_amp, scale):
    upper = sine >= 0.0
    z = CENTER_Z + (upper_amp * abs(sine) if upper else -lower_amp * abs(sine)) * scale
    if upper:
        cupid = math.exp(-0.5 * ((abs(x) - 0.0105) / 0.0040) ** 2)
        notch = math.exp(-0.5 * (x / 0.0038) ** 2)
        z += scale * (0.00085 * cupid - 0.00048 * notch)
    return z


def reshape(body, outer_radius, middle_radius, inner_radius, upper_amp, lower_amp, upper_gap, lower_gap, bulge, strength):
    points, inner_to_middle, middle_to_outer = topology_maps(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    targets = {}
    metadata = []
    for inner, middle in inner_to_middle.items():
        outer = middle_to_outer[middle]
        point = points[inner]
        theta = math.atan2((point.z - CENTER_Z) / 0.0043, point.x / 0.0233)
        cosine, sine = math.cos(theta), math.sin(theta)
        outer_point = points[outer]
        target_outer = Vector((outer_radius * cosine, outer_point.y, lip_z(outer_radius * cosine, sine, upper_amp, lower_amp, 1.0)))
        target_middle = Vector((middle_radius * cosine, outer_point.y - bulge * (0.75 + 0.25 * abs(sine)), lip_z(middle_radius * cosine, sine, upper_amp, lower_amp, 0.60)))
        gap = upper_gap if sine >= 0.0 else lower_gap
        target_inner = Vector((inner_radius * cosine, outer_point.y + 0.0012, CENTER_Z + math.copysign(gap * abs(sine), sine)))
        targets[outer] = points[outer].copy().lerp(target_outer, strength)
        targets[middle] = points[middle].copy().lerp(target_middle, strength)
        targets[inner] = points[inner].copy().lerp(target_inner, strength)
        metadata.append((inner, middle, outer, sine, cosine))
    deltas = {index: inverse3 @ (target - points[index]) for index, target in targets.items()}
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    # Re-author restrained expressions directly on the welded rings. The
    # relative keys remain part of the body, so there is no layer seam.
    open_block = body.data.shape_keys.key_blocks[OPEN_KEY]
    smile_block = body.data.shape_keys.key_blocks[SMILE_KEY]
    for inner, middle, outer, sine, cosine in metadata:
        radial = ((outer, 0.20), (middle, 0.62), (inner, 1.0))
        for index, influence in radial:
            if sine >= 0.0:
                open_block.data[index].co.z += strength * 0.00065 * influence * abs(sine)
            else:
                open_block.data[index].co.z -= strength * 0.0030 * influence * abs(sine)
                open_block.data[index].co.y += strength * 0.00025 * influence * abs(sine)
            corner = abs(cosine) ** 5
            smile_block.data[index].co.x += strength * math.copysign(0.0020 * influence * corner, cosine)
            smile_block.data[index].co.z += strength * 0.0015 * influence * corner
    body.data.update()
    lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    return {
        "ringVertices": {"outer": 120, "middle": 120, "inner": 120},
        "changedVertices": len(targets),
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
    label, outer_radius, middle_radius, inner_radius, upper_amp, lower_amp, upper_gap, lower_gap, bulge, strength = values
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
    topology = reshape(body, outer_radius, middle_radius, inner_radius, upper_amp, lower_amp, upper_gap, lower_gap, bulge, strength)
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
        "parameters": {"outerRadiusM": outer_radius, "middleRadiusM": middle_radius, "innerRadiusM": inner_radius, "upperAmplitudeM": upper_amp, "lowerAmplitudeM": lower_amp, "neutralGapM": [upper_gap, lower_gap], "bulgeM": bulge, "strength": strength},
        "topology": topology,
        "states": states,
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL",
    }
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1037-welded-lip-annulus"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "reshape the existing welded 120-vertex outer, middle and inner body rings; no detached lip object",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED if next(item for item in variants if item["label"] == SELECTED)["status"] == "TECHNICAL_PASS" else None,
    "skinToneContract": "No skin material, scene light, exposure or color-management change; website v83 remains 5.56% darker than committed mainline",
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1037_WELDED_LIP=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "states": [state["status"] for state in item["states"]], "status": item["status"]} for item in variants]}, sort_keys=True))
