"""Sweep an integrated inner eyelid wall from the r1015 true aperture."""

import json
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-balanced-open-aperture-r1015-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1016-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1016-eyelid-inner-wall-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1016-eyelid-inner-wall-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("a-shallow", 0.00035, 0.012),
    ("b-balanced", 0.00065, 0.025),
    ("c-deep", 0.00100, 0.040),
)


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


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def boundary_edges(body, frames):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    for polygon in body.data.polygons:
        for index, first in enumerate(polygon.vertices):
            second = polygon.vertices[(index + 1) % len(polygon.vertices)]
            users[tuple(sorted((first, second)))] += 1
    result = {"L": [], "R": []}
    for edge in body.data.edges:
        key = tuple(sorted(edge.vertices))
        if users[key] != 1:
            continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if (
                abs(midpoint.x - center.x) < radius.x * 1.25
                and abs(midpoint.z - center.z) < radius.z * 0.85
                and midpoint.y < -0.070
            ):
                result[side].append(edge.index)
                break
    return result


def extrude_wall(body, edge_indices, depth, shrink):
    before_vertices = len(body.data.vertices)
    before_keys = [block.name for block in body.data.shape_keys.key_blocks]
    body.active_shape_key_index = 0
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    selected_edges = [bm.edges[index] for indices in edge_indices.values() for index in indices]
    original_boundary = {vertex for edge in selected_edges for vertex in edge.verts}
    center_by_side = {}
    for side, indices in edge_indices.items():
        side_vertices = {vertex for index in indices for vertex in bm.edges[index].verts}
        center_by_side[side] = sum((vertex.co for vertex in side_vertices), Vector()) / len(side_vertices)
    result = bmesh.ops.extrude_edge_only(bm, edges=selected_edges)
    new_vertices = [item for item in result["geom"] if isinstance(item, bmesh.types.BMVert)]
    deform = bm.verts.layers.deform.verify()
    missing_weights_before_copy = 0
    for vertex in new_vertices:
        source = min(original_boundary, key=lambda item: (item.co - vertex.co).length_squared)
        if not vertex[deform]:
            missing_weights_before_copy += 1
            vertex[deform].update(dict(source[deform]))
        side = "L" if source.co.x >= 0.0 else "R"
        center = center_by_side[side]
        vertex.co.x = center.x + (vertex.co.x - center.x) * (1.0 - shrink)
        vertex.co.z = center.z + (vertex.co.z - center.z) * (1.0 - shrink)
        vertex.co.y += depth
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    after_vertices = len(body.data.vertices)
    after_keys = [block.name for block in body.data.shape_keys.key_blocks]
    key_lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    new_indices = range(before_vertices, after_vertices)
    new_weight_counts = [len(body.data.vertices[index].groups) for index in new_indices]
    return {
        "beforeVertices": before_vertices,
        "afterVertices": after_vertices,
        "addedVertices": after_vertices - before_vertices,
        "beforeShapeKeys": before_keys,
        "afterShapeKeys": after_keys,
        "shapeKeyLengths": key_lengths,
        "shapeKeyCompatibility": before_keys == after_keys and all(value == after_vertices for value in key_lengths.values()),
        "missingWeightsBeforeCopy": missing_weights_before_copy,
        "newVerticesWithWeights": sum(value > 0 for value in new_weight_counts),
        "newVertexMinimumWeightGroupCount": min(new_weight_counts) if new_weight_counts else 0,
    }


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def collision(body):
    body_tree = world_tree(body)
    values = {}
    for side in ("L", "R"):
        values[side] = {}
        for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
            values[side][layer] = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"])))
    return values, sum(count for layers in values.values() for count in layers.values())


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True)
results = []
for label, depth, shrink in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    frames = eye_frames()
    edges = boundary_edges(body, frames)
    edit = extrude_wall(body, edges, depth, shrink)
    bpy.context.view_layer.update()
    overlaps, total = collision(body)
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_lash = obj.name.endswith(("UpperLashes", "LowerLashes"))
        if (is_hair or is_lash) and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 900
    camera = scene.camera
    camera.data.lens = 105
    rendered = []
    for view, location, target in (
        ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
        ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
        ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ):
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    result = {
        "label": label,
        "depthM": depth,
        "radialShrink": shrink,
        "boundaryEdgesBySide": {side: len(indices) for side, indices in edges.items()},
        "edit": edit,
        "frame1BodyTriangleOverlaps": overlaps,
        "totalFrame1BodyTriangleOverlaps": total,
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if edit["shapeKeyCompatibility"] and edit["newVerticesWithWeights"] == edit["addedVertices"] and total == 0 else "TECHNICAL_FAIL",
    }
    results.append(result)

scene["aevrynd_mainline_revision"] = "v249r1016-eyelid-inner-wall-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "extrude the true r1015 boundary into the socket while preserving all shape-key blocks and copying deform weights",
    "variants": results,
    "selectedVariant": None,
    "status": "VISUAL_REVIEW_REQUIRED",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1016_EYELID_INNER_WALL=" + json.dumps({
    "output": str(OUTPUT),
    "variants": [{"label": item["label"], "edges": item["boundaryEdgesBySide"], "added": item["edit"]["addedVertices"], "overlaps": item["totalFrame1BodyTriangleOverlaps"], "status": item["status"]} for item in results],
    "status": report["status"],
}, sort_keys=True))
