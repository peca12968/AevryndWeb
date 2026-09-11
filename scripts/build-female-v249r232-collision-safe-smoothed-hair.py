import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-smoothed-long-hair-r231.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-smoothed-hair-r232.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-smoothed-hair-r232.build-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
FRAMES = (1, 20)
CLEARANCE = 0.0015
NEAR = 0.025
ITERATIONS = 6


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[MAIN]
initial = [point.position.copy() for point in hair.data.points]
iteration_reports = []
for iteration in range(ITERATIONS):
    per_frame = {}
    changed = 0
    maximum_correction = 0.0
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = evaluated_tree(bpy.data.objects[BODY], depsgraph)
        matrix = hair.matrix_world.copy()
        inverse_vector = matrix.inverted().to_3x3()
        frame_changed = 0
        frame_minimum = math.inf
        for curve in hair.data.curves:
            start = curve.first_point_index
            end = start + curve.points_length
            for index in range(start + 1, end - 1):
                point = hair.data.points[index]
                world = matrix @ point.position
                nearest = tree.find_nearest(world)
                if nearest is None or nearest[1] is None or nearest[3] > NEAR:
                    continue
                normal = nearest[1].normalized()
                signed = (world - nearest[0]).dot(normal)
                frame_minimum = min(frame_minimum, signed)
                if signed < CLEARANCE:
                    correction = normal * (CLEARANCE - signed)
                    point.position += inverse_vector @ correction
                    frame_changed += 1
                    changed += 1
                    maximum_correction = max(maximum_correction, correction.length)
        hair.data.update_tag()
        bpy.context.view_layer.update()
        per_frame[str(frame)] = {
            "correctedPoints": frame_changed,
            "minimumSignedBeforeM": frame_minimum if math.isfinite(frame_minimum) else None,
        }
    iteration_reports.append({
        "iteration": iteration + 1,
        "frames": per_frame,
        "correctedPoints": changed,
        "maximumSingleCorrectionMm": maximum_correction * 1000.0,
    })
    if changed == 0:
        break

maximum_total = 0.0
changed_total = 0
for index, point in enumerate(hair.data.points):
    delta = (point.position - initial[index]).length
    if delta > 1e-8:
        changed_total += 1
        maximum_total = max(maximum_total, delta)
hair["aevrynd_revision"] = "v249r232-collision-safe-smoothed-hair"
hair["aevrynd_collision_guard_frames"] = "1,20"
hair["aevrynd_collision_clearance_m"] = CLEARANCE
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "frames": list(FRAMES),
    "clearanceM": CLEARANCE,
    "iterations": iteration_reports,
    "uniquePointsMovedFromR231": changed_total,
    "maximumTotalRepairMm": maximum_total * 1000.0,
    "status": "FULL_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R232_COLLISION_SAFE_SMOOTHED_HAIR=" + json.dumps(report, sort_keys=True))
