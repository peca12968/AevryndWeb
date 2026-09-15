import json
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_SELF_COLLISION_SOURCE",
    ASSETS / "aevrynd-female-cc0-dynamic-validation-r631.blend",
))
REPORT = Path(os.environ.get(
    "AEVRYND_SELF_COLLISION_REPORT",
    ASSETS / "female-v249-mainline-cc0-dynamic-validation-r631.self-collision.json",
))
FRAMES = tuple(int(value) for value in os.environ.get(
    "AEVRYND_SELF_COLLISION_FRAMES", "1,20,33,61,80,90,100,110"
).split(","))
BODY = "AevryndFemaleCC0Baseline_v259"
CAGE_ONLY = os.environ.get("AEVRYND_SELF_COLLISION_CAGE", "0") == "1"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
if CAGE_ONLY:
    for modifier in body.modifiers:
        if modifier.type == "SUBSURF":
            modifier.show_viewport = False
scene.frame_set(1)
bpy.context.view_layer.update()
neutral_evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
neutral_mesh = neutral_evaluated.to_mesh()
neutral_points = [neutral_evaluated.matrix_world @ vertex.co for vertex in neutral_mesh.vertices]
neutral_evaluated.to_mesh_clear()
frame_reports = {}
passed = True
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    tree = BVHTree.FromPolygons(points, triangles, all_triangles=True)
    raw_pairs = tree.overlap(tree)
    disjoint_pairs = []
    for first, second in raw_pairs:
        if first >= second:
            continue
        if set(triangles[first]).isdisjoint(triangles[second]):
            disjoint_pairs.append((first, second))
    collision_points = [
        sum((points[index] for index in triangles[triangle]), points[0] * 0.0) / 3.0
        for pair in disjoint_pairs
        for triangle in pair
    ]
    collision_vertex_indices = {
        index
        for pair in disjoint_pairs
        for triangle in pair
        for index in triangles[triangle]
    }
    collision_rest_points = [neutral_points[index] for index in collision_vertex_indices]
    if collision_points:
        bounds_min = [min(point[axis] for point in collision_points) for axis in range(3)]
        bounds_max = [max(point[axis] for point in collision_points) for axis in range(3)]
        center = [
            sum(point[axis] for point in collision_points) / len(collision_points)
            for axis in range(3)
        ]
    else:
        bounds_min = bounds_max = center = None
    if collision_rest_points:
        rest_bounds_min = [min(point[axis] for point in collision_rest_points) for axis in range(3)]
        rest_bounds_max = [max(point[axis] for point in collision_rest_points) for axis in range(3)]
        rest_center = [
            sum(point[axis] for point in collision_rest_points) / len(collision_rest_points)
            for axis in range(3)
        ]
    else:
        rest_bounds_min = rest_bounds_max = rest_center = None
    check = len(disjoint_pairs) == 0
    passed = passed and check
    frame_reports[str(frame)] = {
        "vertices": len(points),
        "triangles": len(triangles),
        "rawOverlapPairs": len(raw_pairs),
        "nonAdjacentSelfCollisionPairs": len(disjoint_pairs),
        "samplePairs": [list(pair) for pair in disjoint_pairs[:40]],
        "collisionBoundsMin": bounds_min,
        "collisionBoundsMax": bounds_max,
        "collisionCenter": center,
        "collisionRestBoundsMin": rest_bounds_min,
        "collisionRestBoundsMax": rest_bounds_max,
        "collisionRestCenter": rest_center,
        "sampleDetails": [
            {
                "triangles": [first, second],
                "vertices": [list(triangles[first]), list(triangles[second])],
                "centroids": [
                    list(sum((points[index] for index in triangles[triangle]), points[0] * 0.0) / 3.0)
                    for triangle in (first, second)
                ],
            }
            for first, second in disjoint_pairs[:40]
        ],
        "check": check,
    }

report = {
    "source": str(SOURCE),
    "frames": list(FRAMES),
    "frameReports": frame_reports,
    "method": "evaluated triangle BVH self-overlap excluding pairs sharing any vertex",
    "cageOnly": CAGE_ONLY,
    "status": "PASS" if passed else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SELF_COLLISION_AUDIT=" + json.dumps({
    "status": report["status"],
    "pairs": {frame: item["nonAdjacentSelfCollisionPairs"] for frame, item in frame_reports.items()},
}, sort_keys=True))
if not passed:
    raise SystemExit(2)
