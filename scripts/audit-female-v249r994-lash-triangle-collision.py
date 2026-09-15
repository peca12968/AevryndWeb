"""Audit r994 lashes with triangle overlap, suitable for lifted fibre tips."""

import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-curled-lash-profile-r994.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-curled-lash-profile-r994.triangle-collision-audit.json"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree, len(vertices), len(polygons)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
failures = []
frames = {}
topology = {}
for frame in FRAMES:
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body, _body_vertices, _body_polygons = world_tree(bpy.data.objects[BODY], depsgraph)
    frame_data = {}
    for side in ("L", "R"):
        upper_name = f"Eye_{side}_UpperLashes"
        lower_name = f"Eye_{side}_LowerLashes"
        upper, upper_vertices, upper_polygons = world_tree(bpy.data.objects[upper_name], depsgraph)
        lower, lower_vertices, lower_polygons = world_tree(bpy.data.objects[lower_name], depsgraph)
        sclera, _sv, _sp = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
        cornea, _cv, _cp = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
        if frame == FRAMES[0]:
            topology[upper_name] = {"vertices": upper_vertices, "polygons": upper_polygons}
            topology[lower_name] = {"vertices": lower_vertices, "polygons": lower_polygons}
        counts = {
            "upperBody": len(upper.overlap(body)), "lowerBody": len(lower.overlap(body)),
            "upperSclera": len(upper.overlap(sclera)), "lowerSclera": len(lower.overlap(sclera)),
            "upperCornea": len(upper.overlap(cornea)), "lowerCornea": len(lower.overlap(cornea)),
            "upperLower": len(upper.overlap(lower)),
        }
        frame_data[side] = counts
        for label, count in counts.items():
            if count:
                failures.append({"frame": frame, "side": side, "pair": label, "triangleOverlapCount": count})
    frames[str(frame)] = frame_data

non_finite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for name in ("Eye_L_LowerLashes", "Eye_L_UpperLashes", "Eye_R_LowerLashes", "Eye_R_UpperLashes")
    for vertex in bpy.data.objects[name].data.vertices
)
if non_finite:
    failures.append({"nonFiniteVertexCount": non_finite})
report = {"source": str(SOURCE), "frames": frames, "topology": topology,
          "nonFiniteVertexCount": non_finite, "failures": failures,
          "status": "PASS" if not failures else "FAIL"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R994_LASH_TRIANGLE_COLLISION=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
