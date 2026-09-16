"""Grow the r1050 face field by topology to find the smallest clean replacement seam."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1052-mouth-topology-dilation.inspect.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862


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


def ordered_loop(edges, points):
    adjacency = defaultdict(set)
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    if not adjacency or any(len(items) != 2 for items in adjacency.values()):
        return None
    start = min(adjacency, key=lambda index: points[index].x)
    current = max(adjacency[start], key=lambda index: points[index].z)
    result = [start]
    previous = start
    while current != start:
        result.append(current)
        following = adjacency[current] - {previous}
        if not following:
            return None
        previous, current = current, next(iter(following))
        if len(result) > len(adjacency):
            return None
    return result if len(result) == len(adjacency) else None


def roughness(order, points):
    if not order:
        return None
    turns = []
    laplacian = []
    for position, index in enumerate(order):
        previous = points[order[(position - 1) % len(order)]]
        current = points[index]
        following = points[order[(position + 1) % len(order)]]
        first = Vector((current.x - previous.x, current.z - previous.z))
        second = Vector((following.x - current.x, following.z - current.z))
        if first.length > 1e-9 and second.length > 1e-9:
            turns.append(math.degrees(first.angle(second)))
        midpoint = (previous + following) * 0.5
        laplacian.append(math.hypot(current.x - midpoint.x, current.z - midpoint.z) * 1000.0)
    turns.sort()
    laplacian.sort()
    return {
        "turnP95Degrees": turns[min(len(turns) - 1, int(0.95 * len(turns)))],
        "turnMaximumDegrees": max(turns),
        "laplacianP95mm": laplacian[min(len(laplacian) - 1, int(0.95 * len(laplacian)))],
        "laplacianMaximumMm": max(laplacian),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
points = mixed_world(body)
edge_faces = defaultdict(set)
face_edges = defaultdict(set)
face_centers = {}
for polygon in mesh.polygons:
    ids = list(polygon.vertices)
    face_centers[polygon.index] = sum((points[index] for index in ids), Vector()) / len(ids)
    for offset, first in enumerate(ids):
        edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)
face_groups = connected(range(len(mesh.polygons)), lambda face: set().union(*(edge_faces[e] for e in face_edges[face])))
main = face_groups[0]
selected = {
    face for face in main
    if face_centers[face].y < -0.105
    and (face_centers[face].x / 0.034) ** 2 + ((face_centers[face].z - CENTER_Z) / 0.005) ** 2 < 1.0
}

records = []
for step in range(17):
    boundary = {
        edge for face in selected for edge in face_edges[face]
        if len(edge_faces[edge] & selected) == 1 and bool(edge_faces[edge] - selected)
    }
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    loops = connected(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))
    loop_records = []
    for loop in loops:
        order = ordered_loop(loop, points)
        vertices = {vertex for edge in loop for vertex in edge}
        local = [points[index] for index in vertices]
        loop_records.append({
            "edges": len(loop),
            "bounds": {
                "x": [min(point.x for point in local), max(point.x for point in local)],
                "y": [min(point.y for point in local), max(point.y for point in local)],
                "z": [min(point.z for point in local), max(point.z for point in local)],
            },
            "roughness": roughness(order, points),
        })
    records.append({
        "dilationSteps": step,
        "selectedFaces": len(selected),
        "boundaryEdges": len(boundary),
        "boundaryLoops": loop_records,
        "allDegreeTwo": all(len(items) == 2 for items in vertex_edges.values()),
    })
    neighbours = {
        other
        for face in selected
        for edge in face_edges[face]
        for other in edge_faces[edge]
        if other in main and other not in selected
    }
    guarded = {
        face for face in neighbours
        if abs(face_centers[face].x) < 0.050
        and abs(face_centers[face].z - CENTER_Z) < 0.020
        and face_centers[face].y < 0.100
    }
    selected.update(guarded)

report = {
    "revision": "v249r1052-mouth-topology-dilation",
    "source": str(SOURCE),
    "seedFaces": records[0]["selectedFaces"],
    "guard": "abs(x)<50mm, abs(z-center)<20mm, y<100mm",
    "records": records,
    "status": "MEASUREMENT_ONLY_NO_GEOMETRY_CHANGE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1052_DILATION=" + json.dumps([
    {"step": record["dilationSteps"], "faces": record["selectedFaces"], "loops": [loop["edges"] for loop in record["boundaryLoops"]]}
    for record in records
], sort_keys=True))
