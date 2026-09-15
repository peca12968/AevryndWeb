"""Extract r446 open eyelid loops and map them into the r1001 eye frame."""

from collections import defaultdict, deque
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
OPEN_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"
TARGET_SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
REPORT = ASSETS / "female-v249-mainline-r1011-open-eyelid-loop-transfer.json"
OPEN_BODY = "AevryndFemaleBodyBaseV118"
TARGET_BODY = "AevryndFemaleCC0Baseline_v259"


def evaluated_snapshot(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    edges = [tuple(edge.vertices) for edge in mesh.edges]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    return evaluated, mesh, points, edges, polygons


def boundary_edges(edges, polygons):
    users = defaultdict(int)
    for poly in polygons:
        for index, first in enumerate(poly):
            second = poly[(index + 1) % len(poly)]
            users[tuple(sorted((first, second)))] += 1
    return [edge for edge in edges if users[tuple(sorted(edge))] == 1]


def components(edges):
    adjacency = defaultdict(list)
    for first, second in edges:
        adjacency[first].append(second)
        adjacency[second].append(first)
    unseen = set(adjacency)
    groups = []
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
        groups.append((group, adjacency))
    return groups


def ordered_loop(vertices, adjacency):
    allowed = set(vertices)
    start = min(vertices)
    ordered = [start]
    previous = None
    current = start
    for _ in range(len(vertices) + 1):
        choices = [item for item in adjacency[current] if item in allowed and item != previous]
        if not choices:
            break
        next_index = choices[0]
        if next_index == start:
            return ordered
        ordered.append(next_index)
        previous, current = current, next_index
    return ordered


def trace_quad_rings(start_order, polygons, points, maximum=20):
    edge_faces = defaultdict(list)
    for face_index, poly in enumerate(polygons):
        for index, first in enumerate(poly):
            second = poly[(index + 1) % len(poly)]
            edge_faces[tuple(sorted((first, second)))].append(face_index)
    current = list(start_order)
    used_faces = set()
    rings = []
    for depth in range(maximum + 1):
        ring_points = [points[index] for index in current]
        rings.append({
            "depth": depth,
            "closed": len(current) >= 3,
            "vertexCount": len(current),
            "meanWorldY": sum(point.y for point in ring_points) / len(ring_points),
            "minimumWorldY": min(point.y for point in ring_points),
            "maximumWorldY": max(point.y for point in ring_points),
            "bounds": {
                "minimum": [min(point[axis] for point in ring_points) for axis in range(3)],
                "maximum": [max(point[axis] for point in ring_points) for axis in range(3)],
            },
            "evaluatedVertexIndices": current,
            "worldCoordinates": [list(point) for point in ring_points],
        })
        current_edges = [tuple(sorted((current[index], current[(index + 1) % len(current)]))) for index in range(len(current))]
        next_edges = []
        step_faces = set()
        failed = False
        for edge in current_edges:
            candidates = [face for face in edge_faces.get(edge, []) if face not in used_faces]
            if len(candidates) != 1:
                rings[-1]["traceFailure"] = f"edge {edge} has {len(candidates)} unused adjacent faces"
                failed = True
                break
            face_index = candidates[0]
            poly = polygons[face_index]
            if len(poly) != 4:
                rings[-1]["traceFailure"] = f"face {face_index} has {len(poly)} vertices"
                failed = True
                break
            opposite = [index for index in poly if index not in edge]
            if len(opposite) != 2:
                rings[-1]["traceFailure"] = f"face {face_index} opposite vertex count {len(opposite)}"
                failed = True
                break
            next_edges.append(tuple(opposite))
            step_faces.add(face_index)
        if failed:
            break
        used_faces.update(step_faces)
        groups = components(next_edges)
        if len(groups) != 1:
            rings[-1]["traceFailure"] = f"next opposite edges form {len(groups)} components"
            break
        vertices, adjacency = groups[0]
        next_order = ordered_loop(vertices, adjacency)
        if len(next_order) != len(vertices):
            rings[-1]["traceFailure"] = f"next component orders {len(next_order)} of {len(vertices)} vertices"
            break
        current = next_order
    return rings


def eye_bounds(side):
    names = [f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"]
    points = []
    for name in names:
        obj = bpy.data.objects[name]
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return {
        "minimum": list(minimum),
        "maximum": list(maximum),
        "center": list((minimum + maximum) * 0.5),
        "radius": list((maximum - minimum) * 0.5),
    }


def normalize(point, frame):
    center = Vector(frame["center"])
    radius = Vector(frame["radius"])
    return [(point[axis] - center[axis]) / radius[axis] for axis in range(3)]


def denormalize(values, frame):
    center = Vector(frame["center"])
    radius = Vector(frame["radius"])
    return Vector(tuple(center[axis] + values[axis] * radius[axis] for axis in range(3)))


bpy.ops.wm.open_mainfile(filepath=str(OPEN_SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
open_frames = {side: eye_bounds(side) for side in ("L", "R")}
evaluated, mesh, points, edges, polygons = evaluated_snapshot(bpy.data.objects[OPEN_BODY])
boundaries = boundary_edges(edges, polygons)
polygon_size_histogram = {
    str(size): sum(1 for polygon in polygons if len(polygon) == size)
    for size in sorted(set(len(polygon) for polygon in polygons))
}
boundary_set = {tuple(sorted(edge)) for edge in boundaries}
boundary_adjacent_size_histogram = defaultdict(int)
for poly in polygons:
    if any(tuple(sorted((poly[index], poly[(index + 1) % len(poly)]))) in boundary_set for index in range(len(poly))):
        boundary_adjacent_size_histogram[str(len(poly))] += 1
eye_edges = []
for edge in boundaries:
    midpoint = (points[edge[0]] + points[edge[1]]) * 0.5
    for side in ("L", "R"):
        center = Vector(open_frames[side]["center"])
        radius = Vector(open_frames[side]["radius"])
        if (
            abs(midpoint.x - center.x) < radius.x * 1.8
            and abs(midpoint.z - center.z) < radius.z * 1.8
            and abs(midpoint.y - center.y) < max(0.06, radius.y * 4.0)
        ):
            eye_edges.append(edge)
            break

loop_candidates = {"L": [], "R": []}
for vertices, adjacency in components(eye_edges):
    coords = [points[index] for index in vertices]
    side = "L" if sum(point.x for point in coords) / len(coords) > 0.0 else "R"
    degrees = [len([item for item in adjacency[index] if item in set(vertices)]) for index in vertices]
    order = ordered_loop(vertices, adjacency)
    ordered_points = [points[index] for index in order]
    loop_candidates[side].append({
        "closed": all(degree == 2 for degree in degrees) and len(order) == len(vertices),
        "vertexCount": len(vertices),
        "edgeCount": sum(1 for edge in eye_edges if edge[0] in set(vertices) and edge[1] in set(vertices)),
        "meanWorldY": sum(point.y for point in ordered_points) / len(ordered_points),
        "evaluatedVertexIndices": order,
        "worldCoordinates": [list(point) for point in ordered_points],
        "eyeNormalizedCoordinates": [normalize(point, open_frames[side]) for point in ordered_points],
        "bounds": {
            "minimum": [min(point[axis] for point in ordered_points) for axis in range(3)],
            "maximum": [max(point[axis] for point in ordered_points) for axis in range(3)],
        },
    })
open_loops = {
    side: min((loop for loop in candidates if loop["closed"]), key=lambda loop: loop["meanWorldY"])
    for side, candidates in loop_candidates.items()
    if any(loop["closed"] for loop in candidates)
}
topology_rings = {
    side: trace_quad_rings(loop["evaluatedVertexIndices"], polygons, points)
    for side, loop in open_loops.items()
}
evaluated.to_mesh_clear()

bpy.ops.wm.open_mainfile(filepath=str(TARGET_SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
target_frames = {side: eye_bounds(side) for side in ("L", "R")}
target_eval, target_mesh, target_points, _, _ = evaluated_snapshot(bpy.data.objects[TARGET_BODY])

mapping = {}
for side, loop in open_loops.items():
    mapped = [denormalize(values, target_frames[side]) for values in loop["eyeNormalizedCoordinates"]]
    nearest = []
    for point in mapped:
        index, distance = min(
            ((index, (candidate - point).length) for index, candidate in enumerate(target_points)),
            key=lambda item: item[1],
        )
        nearest.append({"targetEvaluatedVertexIndex": index, "distanceM": distance})
    distances = sorted(item["distanceM"] for item in nearest)
    mapping[side] = {
        "mappedWorldCoordinates": [list(point) for point in mapped],
        "nearestTargetVertices": nearest,
        "uniqueNearestTargetVertexCount": len(set(item["targetEvaluatedVertexIndex"] for item in nearest)),
        "distanceM": {
            "minimum": distances[0],
            "median": distances[len(distances) // 2],
            "p95": distances[min(len(distances) - 1, int(len(distances) * 0.95))],
            "maximum": distances[-1],
        },
    }
target_eval.to_mesh_clear()

failures = []
for side in ("L", "R"):
    loop = open_loops.get(side)
    if not loop:
        failures.append(f"{side} open eyelid boundary missing")
    elif not loop["closed"]:
        failures.append(f"{side} boundary is not a simple closed loop")
    if mapping.get(side, {}).get("uniqueNearestTargetVertexCount", 0) < 8:
        failures.append(f"{side} mapping collapses to fewer than eight target vertices")

report = {
    "openSource": str(OPEN_SOURCE),
    "targetSource": str(TARGET_SOURCE),
    "frame": 1,
    "openEyeFrames": open_frames,
    "targetEyeFrames": target_frames,
    "openLoops": open_loops,
    "openLoopCandidateSummary": {
        side: [
            {
                "closed": loop["closed"],
                "vertexCount": loop["vertexCount"],
                "edgeCount": loop["edgeCount"],
                "meanWorldY": loop["meanWorldY"],
                "bounds": loop["bounds"],
            }
            for loop in candidates
        ]
        for side, candidates in loop_candidates.items()
    },
    "topologyRingSummary": {
        side: [
            {key: value for key, value in ring.items() if key not in {"evaluatedVertexIndices", "worldCoordinates"}}
            for ring in rings
        ]
        for side, rings in topology_rings.items()
    },
    "openBodyBoundaryEdgeCount": len(boundaries),
    "openBodyPolygonSizeHistogram": polygon_size_histogram,
    "boundaryAdjacentPolygonSizeHistogram": dict(boundary_adjacent_size_histogram),
    "eyeRegionBoundaryEdgeCount": len(eye_edges),
    "targetMapping": mapping,
    "mappingMethod": "normalize r446 loop in its sclera/cornea bounding frame, then denormalize in the r1001 eye frame",
    "failures": failures,
    "status": "PASS_LOOP_EXTRACTION_MAPPING_REVIEW_REQUIRED" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1011_OPEN_EYELID_LOOP_TRANSFER=" + json.dumps({
    "report": str(REPORT),
    "loopSummary": {side: {"vertices": loop["vertexCount"], "closed": loop["closed"]} for side, loop in open_loops.items()},
    "mappingSummary": {side: data["distanceM"] | {"unique": data["uniqueNearestTargetVertexCount"]} for side, data in mapping.items()},
    "failures": failures,
    "status": report["status"],
}, sort_keys=True))
if failures:
    raise SystemExit(2)
