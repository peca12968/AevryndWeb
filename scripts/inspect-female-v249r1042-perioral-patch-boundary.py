"""Measure closed replacement boundaries for a full perioral retopology patch."""

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-cc0-separated-vermilion-r1039-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r1042-perioral-boundary.study.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.4823
BOUNDS = (
    ("g-minimal", 0.038, 0.012),
    ("h-tight", 0.040, 0.014),
    ("d-tight", 0.040, 0.016),
)


def components(items, neighbours):
    remaining = set(items)
    result = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = neighbours(stack.pop()) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        result.append(group)
    return sorted(result, key=len, reverse=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = [body.matrix_world @ vertex.co for vertex in mesh.vertices]

edge_faces = defaultdict(set)
face_edges = defaultdict(set)
for polygon in mesh.polygons:
    ids = list(polygon.vertices)
    for offset, first in enumerate(ids):
        edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)

records = []
for label, radius_x, radius_z in BOUNDS:
    candidates = set()
    for polygon in mesh.polygons:
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / radius_x) ** 2 + ((center.z - CENTER_Z) / radius_z) ** 2
        if center.y < -0.105 and ellipse < 1.0:
            candidates.add(polygon.index)
    face_groups = components(candidates, lambda face: set().union(*(edge_faces[e] for e in face_edges[face])))
    selected = face_groups[0] if face_groups else set()
    component_summaries = []
    for group in face_groups:
        group_vertices = sorted({vertex for face in group for vertex in mesh.polygons[face].vertices})
        group_points = [points[index] for index in group_vertices]
        component_summaries.append({
            "faces": len(group),
            "vertices": len(group_vertices),
            "materials": {str(index): sum(1 for face in group if mesh.polygons[face].material_index == index) for index in range(len(mesh.materials))},
            "worldBounds": {
                "x": [min(p.x for p in group_points), max(p.x for p in group_points)],
                "y": [min(p.y for p in group_points), max(p.y for p in group_points)],
                "z": [min(p.z for p in group_points), max(p.z for p in group_points)],
            },
        })
    boundary = {
        edge for edge, users in edge_faces.items()
        if len(users & selected) == 1 and len(users - selected) >= 1
    }
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    edge_groups = components(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))
    vertices = sorted({vertex for edge in boundary for vertex in edge})
    local = [points[index] for index in vertices]
    records.append({
        "label": label,
        "radiusM": [radius_x, radius_z],
        "candidateFaces": len(candidates),
        "candidateFaceComponents": [len(group) for group in face_groups],
        "candidateComponentDetails": component_summaries,
        "selectedFaces": len(selected),
        "boundaryEdges": len(boundary),
        "boundaryVertices": len(vertices),
        "boundaryComponents": [len(group) for group in edge_groups],
        "boundaryDegreeHistogram": {str(degree): sum(1 for edges in vertex_edges.values() if len(edges) == degree) for degree in sorted({len(edges) for edges in vertex_edges.values()})},
        "closedSingleLoop": len(edge_groups) == 1 and all(len(edges) == 2 for edges in vertex_edges.values()),
        "worldBounds": {
            "x": [min(p.x for p in local), max(p.x for p in local)],
            "y": [min(p.y for p in local), max(p.y for p in local)],
            "z": [min(p.z for p in local), max(p.z for p in local)],
        } if local else None,
        "materialFaces": {str(index): sum(1 for face in selected if mesh.polygons[face].material_index == index) for index in range(len(mesh.materials))},
    })

report = {
    "source": str(SOURCE),
    "body": BODY,
    "bodyVertices": len(mesh.vertices),
    "bodyPolygons": len(mesh.polygons),
    "shapeKeys": [block.name for block in mesh.shape_keys.key_blocks],
    "materialInventory": [
        {
            "index": material_index,
            "name": material.name,
            "faces": len(faces),
            "worldBounds": {
                "x": [min(points[v].x for face in faces for v in mesh.polygons[face].vertices), max(points[v].x for face in faces for v in mesh.polygons[face].vertices)],
                "y": [min(points[v].y for face in faces for v in mesh.polygons[face].vertices), max(points[v].y for face in faces for v in mesh.polygons[face].vertices)],
                "z": [min(points[v].z for face in faces for v in mesh.polygons[face].vertices), max(points[v].z for face in faces for v in mesh.polygons[face].vertices)],
            } if faces else None,
        }
        for material_index, material in enumerate(mesh.materials)
        for faces in [[polygon.index for polygon in mesh.polygons if polygon.material_index == material_index]]
    ],
    "bounds": records,
    "status": "MEASUREMENT_ONLY_NO_GEOMETRY_CHANGE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1042_PERIORAL_BOUNDARY=" + json.dumps(records, sort_keys=True))
