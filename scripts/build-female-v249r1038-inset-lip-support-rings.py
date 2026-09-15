"""Add gradual weighted support rings inside the collision-safe r1035 mouth."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-contiguous-mouth-aperture-r1035-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-inset-lip-support-r1038-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1038-inset-lip-support-rings.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1038-inset-lip-support-rings"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
VARIANTS = (
    ("a-soft-slit", 0.00120, 0.00065, 0.00120),
    ("b-natural-slit", 0.00090, 0.00045, 0.00145),
    ("c-tight-slit", 0.00065, 0.00032, 0.00170),
)
SELECTED = "b-natural-slit"
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


def mouth_boundary_edges(body):
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
            lookup = {tuple(sorted(edge.vertices)): edge.index for edge in body.data.edges}
            return [lookup[tuple(sorted(all_edges[index]))] for index in component]
    raise RuntimeError("The welded 120-edge r1035 mouth boundary was not found")


def extrude_support_rings(body, upper_gap, lower_gap, depth_step):
    boundary_edges = mouth_boundary_edges(body)
    before = len(body.data.vertices)
    lip_material = max(polygon.material_index for polygon in body.data.polygons)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.edges.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    source_edges = [bm.edges[index] for index in boundary_edges]
    mappings = []
    for ring_number in range(3):
        source_vertices = {vertex for edge in source_edges for vertex in edge.verts}
        result = bmesh.ops.extrude_edge_only(bm, edges=source_edges)
        new_vertices = [item for item in result["geom"] if isinstance(item, bmesh.types.BMVert)]
        new_set = set(new_vertices)
        for vertex in new_vertices:
            source = min(source_vertices, key=lambda item: (item.co - vertex.co).length_squared)
            for group, weight in source[deform].items():
                vertex[deform][group] = weight
            mappings.append((ring_number, source, vertex))
        for face in [item for item in result["geom"] if isinstance(item, bmesh.types.BMFace)]:
            face.material_index = lip_material
        source_edges = [item for item in result["geom"] if isinstance(item, bmesh.types.BMEdge) and all(vertex in new_set for vertex in item.verts) and len(item.link_faces) == 1]
    bm.verts.index_update()
    index_mappings = [(ring, source.index, target.index) for ring, source, target in mappings]
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()

    points = mixed_coordinates(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    targets = {}
    ring_scales = ((0.985, 0.74), (0.970, 0.43), (0.955, 0.0))
    for ring, source_index, target_index in index_mappings:
        source = points[source_index]
        horizontal_scale, vertical_scale = ring_scales[ring]
        target = source.copy()
        target.x *= horizontal_scale
        if ring < 2:
            target.z = CENTER_Z + (source.z - CENTER_Z) * vertical_scale
        else:
            sign = 1.0 if source.z >= CENTER_Z else -1.0
            target.z = CENTER_Z + sign * (upper_gap if sign > 0 else lower_gap) * abs(math.sin(math.atan2((source.z - CENTER_Z) / 0.0043, source.x / 0.0233)))
        target.y += depth_step * (ring + 1)
        targets[target_index] = target
    deltas = {index: inverse3 @ (target - points[index]) for index, target in targets.items()}
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    basis = body.data.shape_keys.key_blocks[0]
    open_block = body.data.shape_keys.key_blocks[OPEN_KEY]
    smile_block = body.data.shape_keys.key_blocks[SMILE_KEY]
    open_factors = (0.82, 0.64, 0.46)
    smile_factors = (0.68, 0.42, 0.22)
    for ring, source_index, target_index in index_mappings:
        open_delta = open_block.data[source_index].co - open_block.relative_key.data[source_index].co
        smile_delta = smile_block.data[source_index].co - smile_block.relative_key.data[source_index].co
        open_block.data[target_index].co = basis.data[target_index].co + open_delta * open_factors[ring]
        smile_block.data[target_index].co = basis.data[target_index].co + smile_delta * smile_factors[ring]
    body.data.update()
    after = len(body.data.vertices)
    lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    weights = [len(body.data.vertices[index].groups) for index in range(before, after)]
    return {
        "beforeVertices": before,
        "afterVertices": after,
        "addedVertices": after - before,
        "supportRings": 3,
        "verticesPerRing": 120,
        "changedVertices": len(targets),
        "maximumDeltaMm": max(delta.length for delta in deltas.values()) * 1000.0,
        "shapeKeyCount": len(lengths),
        "shapeKeyCompatibility": len(set(lengths.values())) == 1,
        "newVerticesWithWeights": sum(value > 0 for value in weights),
        "newVertexMinimumWeightGroupCount": min(weights),
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
    label, upper_gap, lower_gap, depth_step = values
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
    topology = extrude_support_rings(body, upper_gap, lower_gap, depth_step)
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
        "parameters": {"neutralGapM": [upper_gap, lower_gap], "depthStepM": depth_step, "supportRings": 3},
        "topology": topology,
        "states": states,
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL",
    }
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1038-inset-lip-support-rings"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "extrude three additional weighted 120-vertex support rings inward from the welded r1035 boundary and close the neutral slit gradually",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED if next(item for item in variants if item["label"] == SELECTED)["status"] == "TECHNICAL_PASS" else None,
    "skinToneContract": "No skin material, scene light, exposure or color-management change; website v83 remains 5.56% darker than committed mainline",
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1038_INSET_LIP=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "states": [state["status"] for state in item["states"]], "status": item["status"]} for item in variants]}, sort_keys=True))
