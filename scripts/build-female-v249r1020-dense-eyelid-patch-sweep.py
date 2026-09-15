"""Build a denser attached eyelid patch from the r1017 locator boundary."""

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
SOURCE = ASSETS / "aevrynd-female-cc0-contiguous-open-aperture-r1017-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-dense-eyelid-patch-r1020-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1020-dense-eyelid-patch-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1020-dense-eyelid-patch-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
EXTENT = 0.88
UPPER_HEIGHT = 0.40
LOWER_DEPTH = 0.26
REGULARIZATION = 0.35
VARIANTS = (
    ("a-shallow", 0.00014, 0.00025, 0.004, 0.008),
    ("b-balanced", 0.00020, 0.00035, 0.006, 0.012),
    ("c-deep", 0.00026, 0.00045, 0.008, 0.016),
)


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def eye_frames():
    result = {}
    for side in ("L", "R"):
        points = []
        for name in (f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"):
            obj = bpy.data.objects[name]
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        result[side] = ((minimum + maximum) * 0.5, (maximum - minimum) * 0.5)
    return result


def visible_boundary_edges(body, frames, expected_edges):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    candidates = {"L": [], "R": []}
    for edge in body.data.edges:
        if users[tuple(sorted(edge.vertices))] != 1:
            continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if abs(midpoint.x - center.x) < radius.x * 1.25 and abs(midpoint.z - center.z) < radius.z * 0.85 and midpoint.y < -0.070:
                candidates[side].append(edge.index)
                break
    selected = {}
    inventory = {}
    for side, indices in candidates.items():
        vertex_edges = defaultdict(set)
        for edge_index in indices:
            for vertex_index in body.data.edges[edge_index].vertices:
                vertex_edges[vertex_index].add(edge_index)
        remaining = set(indices)
        components = []
        while remaining:
            seed = remaining.pop(); stack = [seed]; component = {seed}
            while stack:
                edge_index = stack.pop(); neighbours = set()
                for vertex_index in body.data.edges[edge_index].vertices:
                    neighbours.update(vertex_edges[vertex_index])
                fresh = neighbours & remaining
                remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
            components.append(component)
        chosen = min(components, key=lambda component: abs(len(component) - expected_edges))
        selected[side] = sorted(chosen)
        inventory[side] = sorted((len(component) for component in components), reverse=True)
    return selected, inventory


def subdivide_visible_boundary(body, edge_indices):
    before = len(body.data.vertices)
    bpy.context.view_layer.objects.active = body; body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data); bm.edges.ensure_lookup_table()
    edges = [bm.edges[index] for values in edge_indices.values() for index in values]
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT"); body.data.update()
    return {"beforeVertices": before, "afterVertices": len(body.data.vertices), "addedVertices": len(body.data.vertices) - before}


def regularize_visible_ring(body, frames, edge_indices):
    points = mixed_coordinates(body); inverse3 = body.matrix_world.inverted().to_3x3()
    vertices = {side: sorted({vertex for edge_index in indices for vertex in body.data.edges[edge_index].vertices}) for side, indices in edge_indices.items()}
    deltas = {}
    for side, indices in vertices.items():
        center, radius = frames[side]; temple_sign = 1.0 if side == "L" else -1.0
        for index in indices:
            point = points[index]; u = max(-EXTENT, min(EXTENT, (point.x - center.x) / radius.x))
            temporal = u * temple_sign; arc = math.sqrt(max(0.0, 1.0 - (u / EXTENT) ** 2))
            canthus_z = -0.035 + (temporal + EXTENT) / (2.0 * EXTENT) * 0.145
            current_z = (point.z - center.z) / radius.z
            guide_z = canthus_z + UPPER_HEIGHT * arc if current_z >= canthus_z else canthus_z - LOWER_DEPTH * arc
            target = point.copy(); target.z = center.z + guide_z * radius.z
            deltas[index] = (inverse3 @ (target - point)) * REGULARIZATION
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    body.data.update()
    return {"ringVerticesBySide": {side: len(indices) for side, indices in vertices.items()}, "maximumDeltaMm": max(delta.length for delta in deltas.values()) * 1000.0, "meanDeltaMm": sum(delta.length for delta in deltas.values()) / len(deltas) * 1000.0}


def extrude_support_rings(body, frames, edge_indices, first_depth, total_depth, first_shrink, total_shrink):
    before = len(body.data.vertices); before_keys = [block.name for block in body.data.shape_keys.key_blocks]
    inverse = body.matrix_world.inverted(); centers = {side: inverse @ center for side, (center, _radius) in frames.items()}
    bpy.context.view_layer.objects.active = body; body.select_set(True); body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    first_edges = [bm.edges[index] for values in edge_indices.values() for index in values]
    first_sources = {vertex for edge in first_edges for vertex in edge.verts}
    result1 = bmesh.ops.extrude_edge_only(bm, edges=first_edges)
    ring1 = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMVert)]
    for vertex in ring1:
        source = min(first_sources, key=lambda item: (item.co - vertex.co).length_squared)
        if not vertex[deform]: vertex[deform].update(dict(source[deform]))
        side = "L" if source.co.x >= 0.0 else "R"; center = centers[side]
        vertex.co.x = center.x + (vertex.co.x - center.x) * (1.0 - first_shrink)
        vertex.co.z = center.z + (vertex.co.z - center.z) * (1.0 - first_shrink)
        vertex.co += inverse.to_3x3() @ Vector((0.0, first_depth, 0.0))
    ring1_set = set(ring1)
    ring1_edges = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMEdge) and all(vertex in ring1_set for vertex in item.verts) and len(item.link_faces) == 1]
    result2 = bmesh.ops.extrude_edge_only(bm, edges=ring1_edges)
    ring2 = [item for item in result2["geom"] if isinstance(item, bmesh.types.BMVert)]
    extra_shrink = 1.0 - (1.0 - total_shrink) / (1.0 - first_shrink)
    for vertex in ring2:
        source = min(ring1, key=lambda item: (item.co - vertex.co).length_squared)
        if not vertex[deform]: vertex[deform].update(dict(source[deform]))
        side = "L" if source.co.x >= 0.0 else "R"; center = centers[side]
        vertex.co.x = center.x + (vertex.co.x - center.x) * (1.0 - extra_shrink)
        vertex.co.z = center.z + (vertex.co.z - center.z) * (1.0 - extra_shrink)
        vertex.co += inverse.to_3x3() @ Vector((0.0, total_depth - first_depth, 0.0))
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT"); body.data.update()
    after = len(body.data.vertices); key_lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    weighted = [len(body.data.vertices[index].groups) for index in range(before, after)]
    return {"beforeVertices": before, "afterVertices": after, "addedVertices": after - before, "firstRingVertices": len(ring1), "secondRingVertices": len(ring2), "beforeShapeKeys": before_keys, "afterShapeKeys": list(key_lengths), "shapeKeyLengths": key_lengths, "shapeKeyCompatibility": before_keys == list(key_lengths) and all(length == after for length in key_lengths.values()), "newVerticesWithWeights": sum(value > 0 for value in weighted), "newVertexMinimumWeightGroupCount": min(weighted) if weighted else 0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear(); return tree


def collision_frames(body):
    results = {}; failures = []; scene = bpy.context.scene
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body_tree = world_tree(body, depsgraph)
        frame_result = {}
        for side in ("L", "R"):
            values = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                values[layer] = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
                if values[layer]: failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": values[layer]})
            frame_result[side] = values
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, first_depth, total_depth, first_shrink, total_shrink in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]; frames = eye_frames()
    edges24, inventory24 = visible_boundary_edges(body, frames, 24)
    subdivision = subdivide_visible_boundary(body, edges24); bpy.context.view_layer.update()
    edges48, inventory48 = visible_boundary_edges(body, frames, 48)
    regularization = regularize_visible_ring(body, frames, edges48); bpy.context.view_layer.update()
    edges48, _inventory48b = visible_boundary_edges(body, frames, 48)
    patch = extrude_support_rings(body, frames, edges48, first_depth, total_depth, first_shrink, total_shrink); bpy.context.view_layer.update()
    collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update()
    hidden = []
    for obj in scene.objects:
        if (obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES" or obj.name.endswith(("UpperLashes", "LowerLashes"))) and not obj.hide_render:
            obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 900; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    technical = subdivision["addedVertices"] == 48 and regularization["ringVerticesBySide"] == {"L": 48, "R": 48} and patch["shapeKeyCompatibility"] and patch["newVerticesWithWeights"] == patch["addedVertices"] and not failures
    variants.append({"label": label, "depthM": {"first": first_depth, "total": total_depth}, "radialShrink": {"first": first_shrink, "total": total_shrink}, "sourceBoundaryComponents": inventory24, "denseBoundaryComponents": inventory48, "subdivision": subdivision, "regularization": regularization, "patch": patch, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL"})
    if label == "a-shallow":
        scene["aevrynd_mainline_revision"] = "v249r1020-dense-eyelid-patch-shallow-study"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"; scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "subdivide each 24-edge visible aperture to 48 edges, regularize against the owned guide, then add two attached inward support rings", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1020_DENSE_EYELID_PATCH=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "subdivision": item["subdivision"], "ring": item["regularization"], "patch": item["patch"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
