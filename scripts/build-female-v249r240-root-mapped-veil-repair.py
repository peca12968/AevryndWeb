import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-head-bound-clearance-hair-r238.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-root-mapped-veil-repair-r240.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-root-mapped-veil-repair-r240.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
RIGHT = "AevryndFemaleHair_CrownRootVeil_v338_R"
TARGET = 0.0012
NEAR = 0.025
ITERATIONS = 8


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def repair_iteration(obj, body_tree, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    base_curve_count = len(obj.data.curves)
    evaluated_curve_count = len(evaluated.data.curves)
    if evaluated_curve_count % base_curve_count:
        raise RuntimeError(f"Evaluated curve count {evaluated_curve_count} is not a multiple of {base_curve_count}")
    duplicates = evaluated_curve_count // base_curve_count
    root_tree = KDTree(base_curve_count)
    for curve_index, curve in enumerate(obj.data.curves):
        root_tree.insert(obj.matrix_world @ obj.data.points[curve.first_point_index].position, curve_index)
    root_tree.balance()
    curve_map = {}
    maximum_root_match = 0.0
    for evaluated_curve_index, curve in enumerate(evaluated.data.curves):
        root_world = evaluated.matrix_world @ evaluated.data.points[curve.first_point_index].position
        _co, base_curve_index, distance = root_tree.find(root_world)
        curve_map[evaluated_curve_index] = base_curve_index
        maximum_root_match = max(maximum_root_match, distance)
    corrections = {}
    penetrating = 0
    minimum = math.inf
    for evaluated_curve_index, curve in enumerate(evaluated.data.curves):
        base_curve_index = curve_map[evaluated_curve_index]
        base_curve = obj.data.curves[base_curve_index]
        if curve.points_length != base_curve.points_length:
            raise RuntimeError("Geometry Nodes changed per-curve point count; evaluated-to-authored mapping is ambiguous")
        for local_index in range(curve.points_length):
            evaluated_index = curve.first_point_index + local_index
            world = evaluated.matrix_world @ evaluated.data.points[evaluated_index].position
            nearest = body_tree.find_nearest(world)
            if nearest is None or nearest[1] is None or nearest[3] > NEAR:
                continue
            location, normal = nearest[0], nearest[1].normalized()
            signed = (world - location).dot(normal)
            minimum = min(minimum, signed)
            if signed >= TARGET:
                continue
            penetrating += 1
            base_index = base_curve.first_point_index + local_index
            correction = normal * (TARGET - signed)
            previous = corrections.get(base_index)
            if previous is None or correction.length > previous.length:
                corrections[base_index] = correction
    inverse_vector = obj.matrix_world.inverted().to_3x3()
    maximum = 0.0
    for base_index, correction in corrections.items():
        obj.data.points[base_index].position += inverse_vector @ correction
        maximum = max(maximum, correction.length)
    obj.data.update_tag()
    bpy.context.view_layer.update()
    return {
        "evaluatedCurves": evaluated_curve_count,
        "evaluatedPoints": len(evaluated.data.points),
        "duplicatesPerAuthoredCurve": duplicates,
        "maximumRootMatchMm": maximum_root_match * 1000.0,
        "penetratingEvaluatedPointsBefore": penetrating,
        "authoredPointsMoved": len(corrections),
        "minimumSignedBeforeMm": minimum * 1000.0 if math.isfinite(minimum) else None,
        "maximumSingleCorrectionMm": maximum * 1000.0,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
obj = bpy.data.objects[RIGHT]
obj.data = obj.data.copy()
original = [point.position.copy() for point in obj.data.points]
reports = []
for iteration in range(ITERATIONS):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = evaluated_tree(bpy.data.objects[BODY], depsgraph)
    values = repair_iteration(obj, body_tree, depsgraph)
    values["iteration"] = iteration + 1
    reports.append(values)
    if values["penetratingEvaluatedPointsBefore"] == 0:
        break

changed = 0
maximum_total = 0.0
for index, point in enumerate(obj.data.points):
    delta = (point.position - original[index]).length
    if delta > 1e-8:
        changed += 1
        maximum_total = max(maximum_total, delta)

obj["aevrynd_revision"] = "v249r240-root-mapped-veil-repair"
obj["aevrynd_collision_method"] = "evaluated Geometry Nodes child root KD mapping to authored parent repair"
obj["aevrynd_collision_clearance_m"] = TARGET
scene["aevrynd_mainline_revision"] = "v249r240-root-mapped-veil-repair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_COLLISION_AND_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "object": RIGHT,
    "targetClearanceMm": TARGET * 1000.0,
    "iterations": reports,
    "uniqueAuthoredPointsMoved": changed,
    "maximumTotalAuthoredMoveMm": maximum_total * 1000.0,
    "status": "FULL_COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R240_ROOT_MAPPED_VEIL_REPAIR=" + json.dumps(report, sort_keys=True))
