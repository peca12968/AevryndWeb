"""Inspect evaluated open eyelid boundaries on the r995 target face."""

import json
from collections import defaultdict, deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-target-native-lashes-r995.eyelid-boundary-inspection.json"
BODY = "AevryndFemaleCC0Baseline_v259"


def evaluated_mesh(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    edges = [tuple(edge.vertices) for edge in mesh.edges]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    return evaluated, mesh, points, edges, polygons


def components(edges):
    adjacency = defaultdict(list)
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    unseen = set(adjacency)
    result = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        group = [seed]
        while queue:
            current = queue.popleft()
            for linked in adjacency[current]:
                if linked in unseen:
                    unseen.remove(linked)
                    queue.append(linked)
                    group.append(linked)
        result.append((group, adjacency))
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
evaluated, mesh, points, edges, polygons = evaluated_mesh(bpy.data.objects[BODY])
edge_users = defaultdict(int)
for poly in polygons:
    for index, a in enumerate(poly):
        b = poly[(index + 1) % len(poly)]
        edge_users[tuple(sorted((a, b)))] += 1
boundary = [edge for edge in edges if edge_users[tuple(sorted(edge))] == 1]
near_eyes = []
for edge in boundary:
    midpoint = (points[edge[0]] + points[edge[1]]) * 0.5
    if abs(midpoint.x) < 0.052 and abs(midpoint.x) > 0.006 and midpoint.y < -0.070 and 1.415 < midpoint.z < 1.485:
        near_eyes.append(edge)

reports = []
for vertices, adjacency in components(near_eyes):
    component_edges = [edge for edge in near_eyes if edge[0] in vertices and edge[1] in vertices]
    degrees = {index: len([linked for linked in adjacency[index] if linked in vertices]) for index in vertices}
    coords = [points[index] for index in vertices]
    reports.append({
        "side": "L" if sum(point.x for point in coords) / len(coords) > 0.0 else "R",
        "vertexCount": len(vertices),
        "edgeCount": len(component_edges),
        "closed": all(degree == 2 for degree in degrees.values()),
        "degreeHistogram": {str(degree): sum(value == degree for value in degrees.values()) for degree in sorted(set(degrees.values()))},
        "bounds": {
            "minimum": [min(point[axis] for point in coords) for axis in range(3)],
            "maximum": [max(point[axis] for point in coords) for axis in range(3)],
        },
        "orderedVertexIndices": vertices,
    })

# The body is manifold: the visible opening is closed by an inner socket surface.
# Detect that lid/socket seam as a sharp world-Y depth transition instead.
eye_region_edges = []
depth_histogram = {}
for threshold in (0.0005, 0.0010, 0.0020, 0.0040, 0.0080):
    selected_edges = []
    for edge in edges:
        midpoint = (points[edge[0]] + points[edge[1]]) * 0.5
        if not (0.010 < abs(midpoint.x) < 0.045 and midpoint.y < -0.075 and 1.425 < midpoint.z < 1.470):
            continue
        if abs(points[edge[0]].y - points[edge[1]].y) >= threshold:
            selected_edges.append(edge)
    depth_histogram[f"{threshold:.4f}"] = len(selected_edges)
    if abs(threshold - 0.0020) < 1e-8:
        eye_region_edges = selected_edges

depth_components = []
for vertices, adjacency in components(eye_region_edges):
    coords = [points[index] for index in vertices]
    component_edges = [edge for edge in eye_region_edges if edge[0] in vertices and edge[1] in vertices]
    degrees = {index: len([linked for linked in adjacency[index] if linked in vertices]) for index in vertices}
    depth_components.append({
        "side": "L" if sum(point.x for point in coords) / len(coords) > 0.0 else "R",
        "vertexCount": len(vertices), "edgeCount": len(component_edges),
        "closed": all(degree == 2 for degree in degrees.values()),
        "degreeHistogram": {str(degree): sum(value == degree for value in degrees.values()) for degree in sorted(set(degrees.values()))},
        "bounds": {"minimum": [min(point[axis] for point in coords) for axis in range(3)],
                   "maximum": [max(point[axis] for point in coords) for axis in range(3)]},
    })

evaluated.to_mesh_clear()
reports.sort(key=lambda item: item["side"])
failures = []
if len(reports) != 2:
    failures.append(f"expected two eyelid boundary components, found {len(reports)}")
for item in reports:
    if not item["closed"]:
        failures.append(f"{item['side']} boundary is not a simple closed loop")
report = {"source": str(SOURCE), "frame": 1, "evaluatedBody": BODY,
          "totalBoundaryEdgeCount": len(boundary), "eyeBoundaryEdgeCount": len(near_eyes),
          "components": reports, "depthTransitionEdgeCounts": depth_histogram,
          "depthTransitionThresholdM": 0.002,
          "depthTransitionComponents": sorted(depth_components, key=lambda item: (item["side"], -item["edgeCount"])),
          "failures": failures,
          "status": "PASS" if not failures else "FAIL"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R995_EYELID_BOUNDARY=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
