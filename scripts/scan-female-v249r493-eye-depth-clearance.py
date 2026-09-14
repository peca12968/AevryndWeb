import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r492.blend"
REPORT = ASSETS / "female-v249-mainline-eye-depth-r493.scan.json"
BODY = "AevryndFemaleBodyBaseV118"
OPTICAL = tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Sclera", "Iris", "Pupil", "Cornea", "Catchlight")
)
TESTED = (-0.0040, -0.0030, -0.0020, -0.0010, -0.0005, 0.0005, 0.0010, 0.0020, 0.0030, 0.0040)
BASELINE_LIMIT = {
    "1": {"Eye_L_Cornea": 29, "Eye_R_Cornea": 24, "Eye_L_Sclera": 0, "Eye_R_Sclera": 0},
    "20": {"Eye_L_Cornea": 29, "Eye_R_Cornea": 24, "Eye_L_Sclera": 0, "Eye_R_Sclera": 0},
}


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


rows = []
for depth in TESTED:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    for name in OPTICAL:
        obj = bpy.data.objects[name]
        obj.matrix_world.translation.y += depth
    frames = {}
    passing = True
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        counts = {}
        for side in ("L", "R"):
            for part in ("Cornea", "Sclera"):
                name = f"Eye_{side}_{part}"
                counts[name] = len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
                if counts[name] > BASELINE_LIMIT[str(frame)][name]:
                    passing = False
        frames[str(frame)] = counts
    rows.append({"depthMm": depth * 1000.0, "frames": frames, "passesR491Limits": passing})

passing_rows = [row for row in rows if row["passesR491Limits"]]
report = {
    "source": str(SOURCE),
    "method": "scan the coherent sclera/iris/pupil/cornea/catchlight optical group in both world -Y and +Y; negative depths move toward the viewer and positive depths move into the orbit",
    "baselineLimits": BASELINE_LIMIT,
    "rows": rows,
    "minimumPassingDepthMm": passing_rows[0]["depthMm"] if passing_rows else None,
    "status": "PASSING_DEPTH_FOUND" if passing_rows else "NO_PASSING_DEPTH",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R493_EYE_DEPTH_SCAN=" + json.dumps(report, sort_keys=True))
if not passing_rows:
    raise SystemExit(2)
