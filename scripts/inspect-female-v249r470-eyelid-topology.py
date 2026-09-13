import json
from collections import defaultdict, deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clean-cornea-r470.blend"
REPORT = ASSETS / "female-v249-mainline-r470.eyelid-topology-inspection.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": 0.03453, "R": -0.03444}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
edge_faces = defaultdict(int)
adjacency = defaultdict(set)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for index, first in enumerate(vertices):
        second = vertices[(index + 1) % len(vertices)]
        key = tuple(sorted((first, second)))
        edge_faces[key] += 1
for first, second in (edge for edge, count in edge_faces.items() if count == 1):
    adjacency[first].add(second)
    adjacency[second].add(first)

components = []
unvisited = set(adjacency)
while unvisited:
    start = unvisited.pop()
    component = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in component:
                component.add(neighbor)
                unvisited.discard(neighbor)
                queue.append(neighbor)
    components.append(component)

eye_components = {}
for side, center_x in EYE_CENTERS.items():
    matches = []
    for component in components:
        points = [body.matrix_world @ mesh.vertices[index].co for index in component]
        center = sum(points, points[0] * 0.0) / len(points)
        if abs(center.x - center_x) < 0.018 and center.y < -0.075 and 1.585 < center.z < 1.630:
            matches.append((component, points, center))
    eye_components[side] = [{
        "vertices": len(component),
        "center": list(center),
        "bounds": {
            "x": [min(point.x for point in points), max(point.x for point in points)],
            "y": [min(point.y for point in points), max(point.y for point in points)],
            "z": [min(point.z for point in points), max(point.z for point in points)],
        },
        "vertexIndices": sorted(component),
    } for component, points, center in matches]

shape_keys = []
if mesh.shape_keys:
    for block in mesh.shape_keys.key_blocks:
        shape_keys.append({"name": block.name, "vertices": len(block.data), "value": block.value})
report = {
    "source": str(SOURCE),
    "body": BODY,
    "vertices": len(mesh.vertices),
    "polygons": len(mesh.polygons),
    "boundaryComponents": len(components),
    "eyeBoundaryComponents": eye_components,
    "shapeKeys": shape_keys,
    "candidateMethod": "preserve the existing open aperture and tarsal wall; apply identical local relief deltas to every shape key in narrow upper/lower lid bands",
    "status": "PASS_OPEN_EYE_BOUNDARIES_FOUND" if all(len(eye_components[side]) == 1 for side in EYE_CENTERS) else "FAIL_AMBIGUOUS_BOUNDARIES",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R470_EYELID_TOPOLOGY=" + json.dumps({
    "status": report["status"],
    "boundaryComponents": len(components),
    "eyeComponents": {side: [item["vertices"] for item in values] for side, values in eye_components.items()},
    "shapeKeys": len(shape_keys),
}, sort_keys=True))
if report["status"].startswith("FAIL"):
    raise SystemExit(2)
