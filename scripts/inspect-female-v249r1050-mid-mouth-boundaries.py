"""Find a clean mid-sized attachment boundary for the r1033 mouth retopology.

This is measurement-only.  It searches between the proven-too-small r1044 slit
and the proven-too-large r1042 perioral replacement, and records only simple
closed boundaries on the main connected body component.
"""

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1050-mid-mouth-boundaries.inspect.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862
X_RADII_MM = (24, 26, 28, 30, 32, 34, 36)
Z_RADII_MM = (3, 4, 5, 6, 8, 10, 12, 14)
FRONT_Y = -0.105


def connected(items, neighbours):
    remaining = set(items)
    groups = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = neighbours(stack.pop()) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        groups.append(group)
    return sorted(groups, key=len, reverse=True)


def mixed_world_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - relative.data[index].co)
    return [body.matrix_world @ point for point in coordinates]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_world_coordinates(body)

edge_faces = defaultdict(set)
face_edges = defaultdict(set)
vertex_faces = defaultdict(set)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for vertex in vertices:
        vertex_faces[vertex].add(polygon.index)
    for offset, first in enumerate(vertices):
        edge = tuple(sorted((first, vertices[(offset + 1) % len(vertices)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)

face_groups = connected(
    range(len(mesh.polygons)),
    lambda face: set().union(*(edge_faces[edge] for edge in face_edges[face])),
)
main_faces = face_groups[0]
main_vertices = {vertex for face in main_faces for vertex in mesh.polygons[face].vertices}

lip_group = body.vertex_groups.get("lips")
lip_vertices = set()
if lip_group is not None:
    for vertex in mesh.vertices:
        try:
            if lip_group.weight(vertex.index) > 0.0:
                lip_vertices.add(vertex.index)
        except RuntimeError:
            pass
main_lip_vertices = lip_vertices & main_vertices
main_lip_faces = {face for vertex in main_lip_vertices for face in vertex_faces[vertex]} & main_faces

records = []
for radius_x_mm in X_RADII_MM:
    for radius_z_mm in Z_RADII_MM:
        radius_x = radius_x_mm / 1000.0
        radius_z = radius_z_mm / 1000.0
        candidates = set()
        for face in main_faces:
            polygon = mesh.polygons[face]
            center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
            ellipse = (center.x / radius_x) ** 2 + ((center.z - CENTER_Z) / radius_z) ** 2
            if center.y < FRONT_Y and ellipse < 1.0:
                candidates.add(face)
        groups = connected(
            candidates,
            lambda face: set().union(*(edge_faces[edge] for edge in face_edges[face])),
        )
        selected = groups[0] if groups else set()
        boundary = {
            edge
            for face in selected
            for edge in face_edges[face]
            if len(edge_faces[edge] & selected) == 1 and bool(edge_faces[edge] - selected)
        }
        vertex_edges = defaultdict(set)
        for edge in boundary:
            for vertex in edge:
                vertex_edges[vertex].add(edge)
        boundary_groups = connected(
            boundary,
            lambda edge: set().union(*(vertex_edges[v] for v in edge)),
        )
        group_details = []
        for group in boundary_groups:
            group_vertices = {vertex for edge in group for vertex in edge}
            group_points = [points[index] for index in group_vertices]
            group_details.append({
                "edges": len(group),
                "vertices": len(group_vertices),
                "lipVertices": len(group_vertices & main_lip_vertices),
                "bounds": {
                    "x": [min(point.x for point in group_points), max(point.x for point in group_points)],
                    "y": [min(point.y for point in group_points), max(point.y for point in group_points)],
                    "z": [min(point.z for point in group_points), max(point.z for point in group_points)],
                },
            })
        boundary_vertices = set(vertex_edges)
        selected_vertices = {vertex for face in selected for vertex in mesh.polygons[face].vertices}
        simple = bool(boundary) and all(len(edges) == 2 for edges in vertex_edges.values())
        boundary_points = [points[index] for index in boundary_vertices]
        selected_lip_vertices = selected_vertices & main_lip_vertices
        records.append({
            "radiusXmm": radius_x_mm,
            "radiusZmm": radius_z_mm,
            "selectedFaces": len(selected),
            "candidateComponents": [len(group) for group in groups],
            "boundaryEdges": len(boundary),
            "boundaryComponents": [len(group) for group in boundary_groups],
            "boundaryComponentDetails": group_details,
            "boundaryDegreeHistogram": {
                str(degree): sum(1 for edges in vertex_edges.values() if len(edges) == degree)
                for degree in sorted({len(edges) for edges in vertex_edges.values()})
            },
            "simpleClosedBoundary": simple,
            "selectedLipVertices": len(selected_lip_vertices),
            "mainLipCoverage": round(len(selected_lip_vertices) / max(1, len(main_lip_vertices)), 6),
            "selectedLipFaces": len(selected & main_lip_faces),
            "boundaryLipVertices": len(boundary_vertices & main_lip_vertices),
            "boundaryBounds": {
                "x": [min(point.x for point in boundary_points), max(point.x for point in boundary_points)],
                "y": [min(point.y for point in boundary_points), max(point.y for point in boundary_points)],
                "z": [min(point.z for point in boundary_points), max(point.z for point in boundary_points)],
            } if boundary_points else None,
        })

valid = [
    record for record in records
    if record["simpleClosedBoundary"] and len(record["boundaryComponents"]) == 2
]
middle = [
    record for record in valid
    if 50 <= max(record["boundaryComponents"]) <= 84
    and 0.45 <= record["mainLipCoverage"] <= 0.90
]
middle.sort(key=lambda record: (
    abs(record["mainLipCoverage"] - 0.68),
    abs(max(record["boundaryComponents"]) - 64),
    record["selectedFaces"],
))

report = {
    "revision": "v249r1050-mid-mouth-boundaries",
    "source": str(SOURCE),
    "body": BODY,
    "bodyFaces": len(mesh.polygons),
    "bodyVertices": len(mesh.vertices),
    "shapeKeys": len(mesh.shape_keys.key_blocks),
    "faceComponents": [len(group) for group in face_groups[:12]],
    "mainComponentFaces": len(main_faces),
    "mainComponentVertices": len(main_vertices),
    "mainLipVertices": len(main_lip_vertices),
    "scan": records,
    "qualifiedMiddleBoundaries": middle,
    "preferred": middle[0] if middle else None,
    "status": "MEASUREMENT_ONLY_NO_GEOMETRY_CHANGE",
    "decision": (
        "Use the larger loop as the outer attachment and the smaller loop only as evidence for the existing aperture; rebuild the interior as independent upper/lower paths."
        if middle else
        "No safe middle boundary found; derive a topology path from explicit edge rings before rebuilding."
    ),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1050_BOUNDARY=" + json.dumps({
    "valid": len(valid),
    "qualified": len(middle),
    "preferred": report["preferred"],
}, sort_keys=True))
