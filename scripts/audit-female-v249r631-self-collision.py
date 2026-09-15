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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
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
    check = len(disjoint_pairs) == 0
    passed = passed and check
    frame_reports[str(frame)] = {
        "vertices": len(points),
        "triangles": len(triangles),
        "rawOverlapPairs": len(raw_pairs),
        "nonAdjacentSelfCollisionPairs": len(disjoint_pairs),
        "samplePairs": [list(pair) for pair in disjoint_pairs[:40]],
        "check": check,
    }

report = {
    "source": str(SOURCE),
    "frames": list(FRAMES),
    "frameReports": frame_reports,
    "method": "evaluated triangle BVH self-overlap excluding pairs sharing any vertex",
    "status": "PASS" if passed else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SELF_COLLISION_AUDIT=" + json.dumps({
    "status": report["status"],
    "pairs": {frame: item["nonAdjacentSelfCollisionPairs"] for frame, item in frame_reports.items()},
}, sort_keys=True))
if not passed:
    raise SystemExit(2)
