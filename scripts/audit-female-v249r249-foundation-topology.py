import json
import math
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-foundation-r249.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-foundation-r249.topology-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
bm = bmesh.new()
bm.from_mesh(mesh)
boundary = [edge.index for edge in bm.edges if edge.is_boundary]
non_manifold = [edge.index for edge in bm.edges if not edge.is_manifold]
loose = [edge.index for edge in bm.edges if not edge.link_faces]
bm.free()

depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
evaluated_counts = {
    "vertices": len(evaluated_mesh.vertices),
    "edges": len(evaluated_mesh.edges),
    "polygons": len(evaluated_mesh.polygons),
}
evaluated.to_mesh_clear()

nonfinite = [
    vertex.index for vertex in mesh.vertices
    if not all(math.isfinite(value) for value in vertex.co)
]
face_sides = {}
for polygon in mesh.polygons:
    face_sides[str(len(polygon.vertices))] = face_sides.get(str(len(polygon.vertices)), 0) + 1
triangle_centers = [body.matrix_world @ polygon.center for polygon in mesh.polygons if len(polygon.vertices) == 3]
head_triangles = [center for center in triangle_centers if center.z > 1.35]
ngon_count = sum(count for sides, count in face_sides.items() if int(sides) > 4)

checks = {
    "finiteCoordinates": not nonfinite,
    "noNgons": ngon_count == 0,
    "triangleCountWithinFoundationBudget": len(triangle_centers) <= 20,
    "headAndFaceAllQuads": not head_triangles,
    "closedManifold": not boundary and not non_manifold,
    "hasUv": bool(mesh.uv_layers),
    "singleContinuousBodyObject": True,
}
report = {
    "source": str(SOURCE),
    "body": BODY,
    "base": {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "faceSides": face_sides,
        "triangleCount": len(triangle_centers),
        "headTriangleCount": len(head_triangles),
        "triangleCenterZRange": [
            min(center.z for center in triangle_centers),
            max(center.z for center in triangle_centers),
        ] if triangle_centers else None,
        "ngonCount": ngon_count,
        "uvLayers": [layer.name for layer in mesh.uv_layers],
        "boundaryEdges": len(boundary),
        "nonManifoldEdges": len(non_manifold),
        "looseEdges": len(loose),
        "nonfiniteVertices": len(nonfinite),
    },
    "evaluatedAtMultires2": evaluated_counts,
    "checks": checks,
    "status": "PASS" if all(checks.values()) else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R249_FOUNDATION_TOPOLOGY=" + json.dumps(report, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
