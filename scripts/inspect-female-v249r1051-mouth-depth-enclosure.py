"""Measure whether deeper deletion collapses the r1050 two-loop field to one clean loop."""

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1051-mouth-depth-enclosure.inspect.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862
RADIUS_X = 0.034
RADIUS_Z = 0.005
Y_MAXIMA = (-0.105, -0.095, -0.085, -0.075, -0.065, -0.050, -0.025, 0.0, 0.025)


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


def mixed_world(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coords[index] += block.value * (item.co - relative.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coords]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_world(body)
edge_faces = defaultdict(set)
face_edges = defaultdict(set)
for polygon in mesh.polygons:
    ids = list(polygon.vertices)
    for offset, first in enumerate(ids):
        edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)

face_groups = connected(
    range(len(mesh.polygons)),
    lambda face: set().union(*(edge_faces[edge] for edge in face_edges[face])),
)
main = face_groups[0]
records = []
for y_max in Y_MAXIMA:
    selected = set()
    for face in main:
        polygon = mesh.polygons[face]
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / RADIUS_X) ** 2 + ((center.z - CENTER_Z) / RADIUS_Z) ** 2
        if center.y < y_max and ellipse < 1.0:
            selected.add(face)
    components = connected(
        selected,
        lambda face: set().union(*(edge_faces[edge] for edge in face_edges[face])),
    )
    primary = components[0] if components else set()
    boundary = {
        edge for face in primary for edge in face_edges[face]
        if len(edge_faces[edge] & primary) == 1 and bool(edge_faces[edge] - primary)
    }
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    loops = connected(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))
    loop_records = []
    for loop in loops:
        vertices = {vertex for edge in loop for vertex in edge}
        local = [points[index] for index in vertices]
        selected_users = {face for edge in loop for face in edge_faces[edge] if face in primary}
        outside_users = {face for edge in loop for face in edge_faces[edge] if face not in primary}
        outside_details = []
        for face in sorted(outside_users):
            polygon = mesh.polygons[face]
            center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
            face_points = [points[index] for index in polygon.vertices]
            outside_details.append({
                "face": face,
                "vertices": list(polygon.vertices),
                "center": list(center),
                "bounds": {
                    "x": [min(point.x for point in face_points), max(point.x for point in face_points)],
                    "y": [min(point.y for point in face_points), max(point.y for point in face_points)],
                    "z": [min(point.z for point in face_points), max(point.z for point in face_points)],
                },
            })
        loop_records.append({
            "edges": len(loop),
            "selectedAdjacentFaces": len(selected_users),
            "outsideAdjacentFaces": len(outside_users),
            "outsideFaceDetails": outside_details,
            "bounds": {
                "x": [min(point.x for point in local), max(point.x for point in local)],
                "y": [min(point.y for point in local), max(point.y for point in local)],
                "z": [min(point.z for point in local), max(point.z for point in local)],
            },
        })
    records.append({
        "yMaximum": y_max,
        "candidateFaces": len(selected),
        "faceComponents": [len(group) for group in components],
        "selectedFaces": len(primary),
        "boundaryEdges": len(boundary),
        "boundaryLoops": loop_records,
        "degreeHistogram": {
            str(degree): sum(1 for edges in vertex_edges.values() if len(edges) == degree)
            for degree in sorted({len(edges) for edges in vertex_edges.values()})
        },
        "singleCleanLoop": len(loops) == 1 and all(len(edges) == 2 for edges in vertex_edges.values()),
    })

single = [record for record in records if record["singleCleanLoop"]]
report = {
    "revision": "v249r1051-mouth-depth-enclosure",
    "source": str(SOURCE),
    "field": {"radiusXmm": 34, "radiusZmm": 5, "centerZ": CENTER_Z},
    "records": records,
    "preferred": single[0] if single else None,
    "status": "MEASUREMENT_ONLY_NO_GEOMETRY_CHANGE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1051_ENCLOSURE=" + json.dumps({"preferred": report["preferred"]}, sort_keys=True))
