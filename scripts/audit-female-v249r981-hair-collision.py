"""Audit every r976 groom point against the evaluated r962 body surface."""

import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-cc0-coherent-clump-waves-r981.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-coherent-clump-waves-r981.collision-audit.json"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = "AevryndFemaleCoherentClumpGroom_R981"
NEAR_M = 0.075
LIMIT_M = -0.0005


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
tree = evaluated_tree(bpy.data.objects[BODY], depsgraph)
hair = bpy.data.objects[HAIR]
points = [hair.matrix_world @ point.position for point in hair.data.points]
minimum = math.inf
penetrating = []
near_count = 0
for index, point in enumerate(points):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None or hit[3] > NEAR_M:
        continue
    near_count += 1
    signed = (point - hit[0]).dot(hit[1].normalized())
    minimum = min(minimum, signed)
    if signed < LIMIT_M:
        penetrating.append(index)

report = {
    "source": str(SOURCE),
    "frame": 1,
    "hair": HAIR,
    "body": BODY,
    "pointCount": len(points),
    "nearSurfacePointCount": near_count,
    "minimumSignedM": minimum if math.isfinite(minimum) else None,
    "penetrationLimitM": LIMIT_M,
    "penetratingPointCount": len(penetrating),
    "penetratingPointSample": penetrating[:40],
    "status": "PASS" if not penetrating else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R981_HAIR_COLLISION=" + json.dumps(report, sort_keys=True))
if penetrating:
    raise SystemExit(2)
