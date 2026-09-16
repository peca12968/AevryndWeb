"""Classify face-connected components and mouth boundary ownership in r1046."""

import json
from collections import defaultdict, deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1049-mouth-face-components.inspect.json"
BODY = "AevryndFemaleCC0Baseline_v259"


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    result = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-9:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(result):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_coordinates(body)
edge_faces = defaultdict(set)
face_edges = defaultdict(set)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for index, first in enumerate(vertices):
        edge = tuple(sorted((first, vertices[(index + 1) % len(vertices)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)

pending = set(range(len(mesh.polygons)))
components = []
while pending:
    root = pending.pop()
    found = {root}
    queue = deque([root])
    while queue:
        face = queue.popleft()
        neighbors = set().union(*(edge_faces[edge] for edge in face_edges[face])) & pending
        pending.difference_update(neighbors)
        found.update(neighbors)
        queue.extend(neighbors)
    components.append(found)
components.sort(key=len, reverse=True)

records = []
mouth_records = []
for component_index, faces in enumerate(components):
    vertices = sorted({vertex for face in faces for vertex in mesh.polygons[face].vertices})
    boundary = {
        edge for face in faces for edge in face_edges[face]
        if len(edge_faces[edge] & faces) == 1
    }
    bounds = {
        axis: [round(min(getattr(points[index], axis) for index in vertices), 7), round(max(getattr(points[index], axis) for index in vertices), 7)]
        for axis in ("x", "y", "z")
    }
    materials = defaultdict(int)
    for face in faces:
        polygon = mesh.polygons[face]
        name = mesh.materials[polygon.material_index].name if polygon.material_index < len(mesh.materials) and mesh.materials[polygon.material_index] else f"slot-{polygon.material_index}"
        materials[name] += 1
    record = {
        "component": component_index,
        "faces": len(faces),
        "vertices": len(vertices),
        "boundaryEdges": len(boundary),
        "bounds": bounds,
        "materials": dict(materials),
        "faceIndices": sorted(faces) if len(faces) <= 500 else None,
    }
    records.append(record)
    if bounds["x"][0] < 0.040 and bounds["x"][1] > -0.040 and bounds["z"][0] < 1.411 and bounds["z"][1] > 1.361:
        mouth_records.append(record)

report = {
    "revision": "v249r1049-mouth-face-components",
    "source": str(SOURCE),
    "componentCount": len(components),
    "largestComponentFaces": len(components[0]),
    "components": records,
    "mouthOverlappingComponents": mouth_records,
    "removableMouthIslandComponents": [record["component"] for record in mouth_records if record["faces"] <= 500],
    "status": "MEASURED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1049_COMPONENTS=" + json.dumps({
    "components": len(components),
    "largest": len(components[0]),
    "mouth": [(item["component"], item["faces"], item["vertices"], item["boundaryEdges"]) for item in mouth_records],
    "removable": report["removableMouthIslandComponents"],
}, sort_keys=True))
