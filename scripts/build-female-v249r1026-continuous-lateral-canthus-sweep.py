"""Close the temporal canthus with faces continuous with the r1025 inner lid ring."""

import json
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-visible-lash-fibers-r1025-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-continuous-lateral-canthus-r1026-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1026-continuous-lateral-canthus-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1026-continuous-lateral-canthus-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-one-segment", 1), ("b-two-segment", 2), ("c-three-segment", 3))


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks; coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8: continue
        for index, coordinate in enumerate(coordinates): coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def eye_frames():
    result = {}
    for side in ("L", "R"):
        points = []
        for name in (f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"):
            obj = bpy.data.objects[name]; points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3))); maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        result[side] = ((minimum + maximum) * 0.5, (maximum - minimum) * 0.5)
    return result


def visible_boundary(body, frames, expected=48):
    points = mixed_coordinates(body); users = defaultdict(int)
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices): users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    candidates = {"L": [], "R": []}
    for edge in body.data.edges:
        if users[tuple(sorted(edge.vertices))] != 1: continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if abs(midpoint.x - center.x) < radius.x * 1.25 and abs(midpoint.z - center.z) < radius.z * 0.85 and midpoint.y < -0.070:
                candidates[side].append(edge.index); break
    selected = {}; inventory = {}
    for side, indices in candidates.items():
        vertex_edges = defaultdict(set)
        for edge_index in indices:
            for vertex_index in body.data.edges[edge_index].vertices: vertex_edges[vertex_index].add(edge_index)
        remaining = set(indices); components = []
        while remaining:
            seed = remaining.pop(); stack = [seed]; component = {seed}
            while stack:
                edge_index = stack.pop(); neighbours = set()
                for vertex_index in body.data.edges[edge_index].vertices: neighbours.update(vertex_edges[vertex_index])
                fresh = neighbours & remaining; remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
            components.append(component)
        chosen = min(components, key=lambda component: abs(len(component) - expected)); selected[side] = sorted(chosen); inventory[side] = sorted((len(component) for component in components), reverse=True)
    return selected, inventory, points


def ordered_loop(body, edge_indices):
    neighbours = defaultdict(list)
    for edge_index in edge_indices:
        first, second = body.data.edges[edge_index].vertices; neighbours[first].append(second); neighbours[second].append(first)
    start = next(iter(neighbours)); order = [start]; previous = None; current = start
    while True:
        choices = [item for item in neighbours[current] if item != previous]
        nxt = choices[0]
        if nxt == start: break
        order.append(nxt); previous, current = current, nxt
        if len(order) > len(neighbours) + 1: raise RuntimeError("boundary traversal did not close")
    if len(order) != len(neighbours): raise RuntimeError(f"expected closed loop, traversed {len(order)} of {len(neighbours)} vertices")
    return order


def add_continuous_wedges(body, edges, points, steps):
    before_polygons = len(body.data.polygons); before_vertices = len(body.data.vertices); before_keys = [block.name for block in body.data.shape_keys.key_blocks]
    paths = {}
    for side in ("L", "R"):
        loop = ordered_loop(body, edges[side]); temporal = max(range(len(loop)), key=lambda index: points[loop[index]].x) if side == "L" else min(range(len(loop)), key=lambda index: points[loop[index]].x)
        paths[side] = [loop[(temporal + offset) % len(loop)] for offset in range(-steps, steps + 1)]
    bpy.context.view_layer.objects.active = body; body.select_set(True); body.active_shape_key_index = 0; bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data); bm.verts.ensure_lookup_table(); created = []
    for side in ("L", "R"):
        vertices = [bm.verts[index] for index in paths[side]]; face = bm.faces.new(vertices); face.material_index = 0; face.smooth = True; face.normal_update()
        if face.normal.y > 0.0: face.normal_flip()
        created.append({"side": side, "vertices": paths[side], "polygonSides": len(paths[side])})
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True); bpy.ops.object.mode_set(mode="OBJECT"); body.data.update()
    after_keys = [block.name for block in body.data.shape_keys.key_blocks]
    return {"beforeVertices": before_vertices, "afterVertices": len(body.data.vertices), "beforePolygons": before_polygons, "afterPolygons": len(body.data.polygons), "shapeKeysBefore": before_keys, "shapeKeysAfter": after_keys, "shapeKeyCompatibility": before_keys == after_keys and all(len(block.data) == before_vertices for block in body.data.shape_keys.key_blocks), "createdFaces": created}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def collision_frames(body):
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body_tree = world_tree(body, depsgraph); frame_result = {}
        for side in ("L", "R"):
            values = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                values[layer] = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
                if values[layer]: failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": values[layer]})
            patch_name = f"Eye_{side}_MedialCaruncle_R1023"
            if patch_name in bpy.data.objects:
                values["MedialCaruncle"] = len(body_tree.overlap(world_tree(bpy.data.objects[patch_name], depsgraph)))
                if values["MedialCaruncle"]: failures.append({"frame": frame, "side": side, "layer": "MedialCaruncle", "triangleOverlapCount": values["MedialCaruncle"]})
            frame_result[side] = values
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, steps in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); body = bpy.data.objects[BODY]; frames = eye_frames(); edges, before_inventory, points = visible_boundary(body, frames)
    edit = add_continuous_wedges(body, edges, points, steps); bpy.context.view_layer.update(); _after_edges, after_inventory, _after_points = visible_boundary(body, frames, expected=49 - 2 * steps)
    collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"; is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_brow_or_lash and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    status = "TECHNICAL_PASS" if edit["shapeKeyCompatibility"] and not failures else "TECHNICAL_FAIL"; variants.append({"label": label, "closedSegmentsPerDirection": steps, "boundaryBefore": before_inventory, "boundaryAfter": after_inventory, "edit": edit, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": status})
    if label == "b-two-segment" and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1026-two-segment-continuous-lateral-canthus"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "add one skin-material face per eye across the temporal arc of the existing 48-edge inner lid ring; no detached object and no new vertex", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1026_CONTINUOUS_LATERAL_CANTHUS=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "boundaryAfter": item["boundaryAfter"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
