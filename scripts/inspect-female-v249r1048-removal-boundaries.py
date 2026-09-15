"""Simulate r1047 strip-face removal and measure weldable mouth boundaries."""

import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
ISOLATION = ASSETS / "female-v249-mainline-r1047-boundary-face-isolation.inspect.json"
REPORT = ASSETS / "female-v249-mainline-r1048-removal-boundaries.inspect.json"
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


def boundary_components(mesh, removed, points):
    edge_faces = defaultdict(set)
    for polygon in mesh.polygons:
        if polygon.index in removed:
            continue
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            edge_faces[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))].add(polygon.index)
    mouth_edges = {
        edge for edge, users in edge_faces.items()
        if len(users) == 1
        and max(abs(points[index].x) for index in edge) < 0.040
        and max(abs(points[index].z - 1.3862) for index in edge) < 0.025
        and min(points[index].y for index in edge) < -0.115
    }
    vertex_edges = defaultdict(set)
    for edge in mouth_edges:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    pending = set(mouth_edges)
    components = []
    while pending:
        root = pending.pop()
        found = {root}
        queue = deque(root)
        while queue:
            vertex = queue.popleft()
            for edge in vertex_edges[vertex] & pending:
                pending.remove(edge)
                found.add(edge)
                queue.extend(edge)
        vertices = sorted(set().union(*map(set, found)))
        degrees = CounterLike()
        for edge in found:
            degrees[edge[0]] += 1
            degrees[edge[1]] += 1
        components.append({
            "edges": len(found),
            "vertices": vertices,
            "degreeCounts": dict(sorted(defaultdict_count(degrees.values()).items())),
            "closedDegreeTwo": all(value == 2 for value in degrees.values()),
            "bounds": {
                axis: [round(min(getattr(points[index], axis) for index in vertices), 7), round(max(getattr(points[index], axis) for index in vertices), 7)]
                for axis in ("x", "y", "z")
            },
        })
    return sorted(components, key=lambda item: item["edges"], reverse=True)


class CounterLike(defaultdict):
    def __init__(self):
        super().__init__(int)


def defaultdict_count(values):
    result = defaultdict(int)
    for value in values:
        result[value] += 1
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_coordinates(body)
isolation = json.loads(ISOLATION.read_text(encoding="utf-8"))
strip = {
    item["face"] for item in isolation["faces"]
    if item["group"] == "mid" and item["center"][2] > 1.38
}
rear = {item["face"] for item in isolation["faces"] if item["group"] == "rear"}

edge_faces = defaultdict(set)
face_edges = defaultdict(set)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for index, first in enumerate(vertices):
        edge = tuple(sorted((first, vertices[(index + 1) % len(vertices)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)
neighbors = set()
for face in strip:
    for edge in face_edges[face]:
        neighbors.update(edge_faces[edge])
neighbors -= strip
interior_neighbors = set()
for face in neighbors:
    polygon = mesh.polygons[face]
    center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
    if center.y > -0.132 and abs(center.z - 1.3862) < 0.010:
        interior_neighbors.add(face)

sets = {
    "strip8": strip,
    "strip8_plus_rear": strip | rear,
    "strip8_plus_interior_neighbors": strip | interior_neighbors,
    "strip8_plus_rear_and_interior_neighbors": strip | rear | interior_neighbors,
}
report = {
    "revision": "v249r1048-removal-boundaries",
    "source": str(SOURCE),
    "stripFaces": sorted(strip),
    "rearFaces": sorted(rear),
    "interiorNeighborFaces": sorted(interior_neighbors),
    "variants": {
        name: {"removedFaces": sorted(faces), "components": boundary_components(mesh, faces, points)}
        for name, faces in sets.items()
    },
    "status": "MEASURED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1048_BOUNDARIES=" + json.dumps({
    name: {"removed": len(faces), "components": [(item["edges"], item["closedDegreeTwo"]) for item in report["variants"][name]["components"][:8]]}
    for name, faces in sets.items()
}, sort_keys=True))
