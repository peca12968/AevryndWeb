"""Measure fitted brow/lash vertex clearance against the evaluated r962-derived body."""

import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-face-fiber-restore-r987.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-face-fiber-restore-r987.clearance-audit.json"
BODY = "AevryndFemaleCC0Baseline_v259"
FEATURES = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_LowerLashes", "Eye_L_UpperLashes",
    "Eye_R_LowerLashes", "Eye_R_UpperLashes",
)


def body_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def percentile(values, fraction):
    values = sorted(values)
    return values[min(len(values) - 1, int((len(values) - 1) * fraction))]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
tree = body_tree(bpy.data.objects[BODY])
objects = {}
for name in FEATURES:
    obj = bpy.data.objects[name]
    distances = []
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        hit = tree.find_nearest(point, 0.04)
        if hit is None or hit[1] is None:
            continue
        distances.append((point - hit[0]).dot(hit[1].normalized()))
    objects[name] = {
        "sampleCount": len(distances),
        "minimumSignedM": min(distances),
        "p05SignedM": percentile(distances, 0.05),
        "medianSignedM": percentile(distances, 0.50),
        "p95SignedM": percentile(distances, 0.95),
        "maximumSignedM": max(distances),
        "penetratingVertexCount": sum(value < -1e-7 for value in distances),
        "within0p2mmVertexCount": sum(value < 0.0002 for value in distances),
    }

status = "PASS" if all(item["penetratingVertexCount"] == 0 for item in objects.values()) else "FAIL"
report = {"source": str(SOURCE), "frame": 1, "objects": objects, "status": status}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R987_FACE_FEATURE_CLEARANCE=" + json.dumps(report, sort_keys=True))
