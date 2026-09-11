import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-back-seam-closure-r246.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-seam-clearance-r247.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-baked-seam-clearance-r247.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
TARGET_LAYERS = ("hair.main", "hair.overlay")
FRAMES = (1, 20)
CLEARANCE = 0.0012
NEAR = 0.025
ITERATIONS = 3


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def target_objects():
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == "CURVES"
        and any(str(obj.get("aevrynd_layer", "")).startswith(prefix) for prefix in TARGET_LAYERS)
    ]


def bake_evaluated_curves(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    before = {
        "authoredCurves": len(obj.data.curves),
        "authoredPoints": len(obj.data.points),
        "evaluatedCurves": len(evaluated.data.curves),
        "evaluatedPoints": len(evaluated.data.points),
        "removedModifiers": [modifier.name for modifier in obj.modifiers],
    }
    baked = evaluated.data.copy()
    baked.name = obj.data.name + "_v249r247_baked"
    obj.data = baked
    obj.modifiers.clear()
    return before


def project_points(obj, body_tree):
    inverse_vector = obj.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    minimum = math.inf
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        nearest = body_tree.find_nearest(world)
        if nearest is None or nearest[1] is None or nearest[3] > NEAR:
            continue
        location, normal = nearest[0], nearest[1].normalized()
        signed = (world - location).dot(normal)
        minimum = min(minimum, signed)
        if signed >= CLEARANCE:
            continue
        correction = normal * (CLEARANCE - signed)
        point.position += inverse_vector @ correction
        moved += 1
        maximum = max(maximum, correction.length)
    obj.data.update_tag()
    return {
        "pointsMoved": moved,
        "minimumSignedBeforeMm": minimum * 1000.0 if math.isfinite(minimum) else None,
        "maximumSingleCorrectionMm": maximum * 1000.0,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
objects = target_objects()
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
bake_report = {obj.name: bake_evaluated_curves(obj, depsgraph) for obj in objects}
bpy.context.view_layer.update()

original = {
    obj.name: [point.position.copy() for point in obj.data.points]
    for obj in objects
}
iteration_reports = []
for iteration in range(ITERATIONS):
    frame_reports = {}
    total_moved = 0
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = evaluated_tree(bpy.data.objects[BODY], depsgraph)
        frame_reports[str(frame)] = {}
        for obj in objects:
            values = project_points(obj, body_tree)
            frame_reports[str(frame)][obj.name] = values
            total_moved += values["pointsMoved"]
    iteration_reports.append({"iteration": iteration + 1, "frames": frame_reports, "pointsMoved": total_moved})
    if total_moved == 0:
        break

movement = {}
for obj in objects:
    changed = 0
    maximum = 0.0
    for index, point in enumerate(obj.data.points):
        delta = (point.position - original[obj.name][index]).length
        if delta > 1e-8:
            changed += 1
            maximum = max(maximum, delta)
    movement[obj.name] = {"uniquePointsMoved": changed, "maximumTotalMoveMm": maximum * 1000.0}
    obj["aevrynd_revision"] = "v249r247-baked-seam-clearance"
    obj["aevrynd_collision_method"] = "baked evaluated main and overlay curves with two-frame clearance projection"
    obj["aevrynd_collision_clearance_m"] = CLEARANCE

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r247-baked-seam-clearance"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_COLLISION_AND_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "baked": bake_report,
    "frames": list(FRAMES),
    "targetClearanceMm": CLEARANCE * 1000.0,
    "iterations": iteration_reports,
    "movement": movement,
    "status": "FULL_COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R247_BAKED_SEAM_CLEARANCE=" + json.dumps(report, sort_keys=True))
