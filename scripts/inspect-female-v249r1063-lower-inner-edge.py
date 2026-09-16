"""Locate the low-density edges responsible for the bright lower inner-lip turn."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1063-lower-inner-edge.inspect.json"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
EXCLUDED = {"Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030"}


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.name in EXCLUDED or block.mute or abs(block.value) < 1e-8:
            continue
        for index, point in enumerate(points):
            point += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ point for point in points]


def polygon_normal(polygon, points):
    first = points[polygon.vertices[0]]
    normal = Vector()
    for offset in range(1, len(polygon.vertices) - 1):
        normal += (points[polygon.vertices[offset]] - first).cross(points[polygon.vertices[offset + 1]] - first)
    return normal.normalized() if normal.length else Vector((0.0, 0.0, 1.0))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_coordinates(body)
normals = [polygon_normal(polygon, points) for polygon in mesh.polygons]
edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
edge_faces = {edge.index: [] for edge in mesh.edges}
for polygon in mesh.polygons:
    for edge_key in polygon.edge_keys:
        edge_faces[edge_lookup[tuple(sorted(edge_key))]].append(polygon.index)
lips = body.vertex_groups.get("lips")

def lip_weight(vertex):
    if lips is None:
        return 0.0
    return next((item.weight for item in mesh.vertices[vertex].groups if item.group == lips.index), 0.0)

candidates = []
crease_attribute = mesh.attributes.get("crease_edge")
sharp_attribute = mesh.attributes.get("sharp_edge")
for edge in mesh.edges:
    faces = edge_faces[edge.index]
    if len(faces) != 2:
        continue
    center = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
    if abs(center.x) > 0.048 or center.y > -0.100 or not (1.374 < center.z < 1.390):
        continue
    angle = math.degrees(normals[faces[0]].angle(normals[faces[1]]))
    candidates.append({
        "edge": edge.index,
        "vertices": list(edge.vertices),
        "faces": faces,
        "center": [round(value, 8) for value in center],
        "dihedralDegrees": angle,
        "lipWeights": [lip_weight(vertex) for vertex in edge.vertices],
        "lengthMm": (points[edge.vertices[0]] - points[edge.vertices[1]]).length * 1000.0,
        "crease": crease_attribute.data[edge.index].value if crease_attribute else 0.0,
        "sharp": bool(sharp_attribute.data[edge.index].value) if sharp_attribute else False,
    })
candidates.sort(key=lambda item: item["dihedralDegrees"], reverse=True)
report = {
    "revision": "v249r1063-lower-inner-edge-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "method": "active-neutral low-density dihedral measurement in the lower inner-lip band",
    "candidateCount": len(candidates),
    "over20Degrees": sum(item["dihedralDegrees"] >= 20.0 for item in candidates),
    "over10Degrees": sum(item["dihedralDegrees"] >= 10.0 for item in candidates),
    "candidates": candidates,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1063_EDGE_INSPECT=" + json.dumps({
    "candidateCount": len(candidates),
    "over10": report["over10Degrees"],
    "over20": report["over20Degrees"],
    "top": candidates[:12],
}, sort_keys=True))
