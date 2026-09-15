"""Regularize the single r1017 aperture ring against the authored almond guide."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-contiguous-open-aperture-r1017-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-regularized-open-aperture-r1019-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1019-aperture-ring-regularization-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1019-aperture-ring-regularization-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
EXTENT = 0.88
UPPER_HEIGHT = 0.40
LOWER_DEPTH = 0.26
VARIANTS = (("a-restrained", 0.35), ("b-balanced", 0.65), ("c-authored", 1.0))


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


def visible_aperture_vertices(body, frames):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    for polygon in body.data.polygons:
        for index, first in enumerate(polygon.vertices):
            second = polygon.vertices[(index + 1) % len(polygon.vertices)]
            users[tuple(sorted((first, second)))] += 1
    candidates = {"L": [], "R": []}
    for edge in body.data.edges:
        if users[tuple(sorted(edge.vertices))] != 1:
            continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if abs(midpoint.x - center.x) < radius.x * 1.25 and abs(midpoint.z - center.z) < radius.z * 0.85 and midpoint.y < -0.070:
                candidates[side].append(edge.index)
                break
    result = {}
    inventory = {}
    for side, indices in candidates.items():
        vertex_edges = defaultdict(set)
        for edge_index in indices:
            for vertex_index in body.data.edges[edge_index].vertices:
                vertex_edges[vertex_index].add(edge_index)
        remaining = set(indices)
        components = []
        while remaining:
            seed = remaining.pop()
            stack = [seed]
            component = {seed}
            while stack:
                edge_index = stack.pop()
                neighbours = set()
                for vertex_index in body.data.edges[edge_index].vertices:
                    neighbours.update(vertex_edges[vertex_index])
                fresh = neighbours & remaining
                remaining.difference_update(fresh)
                component.update(fresh)
                stack.extend(fresh)
            components.append(component)
        selected = min(components, key=lambda component: abs(len(component) - 24))
        result[side] = sorted({vertex for edge_index in selected for vertex in body.data.edges[edge_index].vertices})
        inventory[side] = {"selectedEdges": len(selected), "selectedVertices": len(result[side]), "allComponentEdgeCounts": sorted((len(component) for component in components), reverse=True)}
    return result, inventory, points


def regularize(body, frames, vertices, points, strength):
    inverse = body.matrix_world.inverted()
    deltas = {}
    for side, indices in vertices.items():
        center, radius = frames[side]
        temple_sign = 1.0 if side == "L" else -1.0
        for index in indices:
            point = points[index]
            u = max(-EXTENT, min(EXTENT, (point.x - center.x) / radius.x))
            temporal = u * temple_sign
            arc = math.sqrt(max(0.0, 1.0 - (u / EXTENT) ** 2))
            canthus_z = -0.035 + (temporal + EXTENT) / (2.0 * EXTENT) * 0.145
            current_z = (point.z - center.z) / radius.z
            guide_z = canthus_z + UPPER_HEIGHT * arc if current_z >= canthus_z else canthus_z - LOWER_DEPTH * arc
            target = point.copy()
            target.z = center.z + guide_z * radius.z
            # Apply the world-space correction relative to the currently
            # evaluated mixed pose.  Comparing against Basis here would also
            # bake the active expression offsets and can jump by centimetres.
            deltas[index] = (inverse.to_3x3() @ (target - point)) * strength
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    body.data.update()
    return {"movedVertices": len(deltas), "maximumDeltaMm": max(delta.length for delta in deltas.values()) * 1000.0, "meanDeltaMm": sum(delta.length for delta in deltas.values()) / len(deltas) * 1000.0}


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear(); return tree


def collision(body):
    tree = world_tree(body); values = {}
    for side in ("L", "R"):
        values[side] = {layer: len(tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"]))) for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes")}
    return values, sum(value for layers in values.values() for value in layers.values())


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True)
results = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]; frames = eye_frames()
    vertices, inventory, points = visible_aperture_vertices(body, frames)
    edit = regularize(body, frames, vertices, points, strength)
    bpy.context.view_layer.update(); overlaps, total = collision(body)
    hidden = []
    for obj in scene.objects:
        if (obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES" or obj.name.endswith(("UpperLashes", "LowerLashes"))) and not obj.hide_render:
            obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 900
    camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    results.append({"label": label, "strength": strength, "boundary": inventory, "edit": edit, "frame1BodyTriangleOverlaps": overlaps, "totalFrame1BodyTriangleOverlaps": total, "rendered": rendered, "status": "TECHNICAL_PASS" if total == 0 else "TECHNICAL_FAIL"})

scene["aevrynd_mainline_revision"] = "v249r1019-aperture-ring-regularization-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "move the r1017 24-vertex visible aperture ring toward the owned r1014 b-balanced anatomical guide while preserving shape-key deltas", "variants": results, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1019_APERTURE_RING_REGULARIZATION=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "edit": item["edit"], "overlaps": item["totalFrame1BodyTriangleOverlaps"], "status": item["status"]} for item in results]}, sort_keys=True))
