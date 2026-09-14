import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-skin-r491.blend"
REPORT = ASSETS / "female-v249-mainline-eye-aperture-r492.inspection.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": 0.03453, "R": -0.03444}


def boundary_components(mesh):
    counts = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            second = vertices[(index + 1) % len(vertices)]
            counts[tuple(sorted((first, second)))] += 1
    for (first, second), count in counts.items():
        if count == 1:
            adjacency[first].add(second)
            adjacency[second].add(first)
    result = []
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
        result.append(component)
    return result


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
        "center": [sum(point[axis] for point in points) / len(points) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
evaluated.to_mesh_clear()

components = boundary_components(body.data)
eyes = {}
for side, center_x in EYE_CENTERS.items():
    matches = []
    for component in components:
        points = [world_points[index] for index in component]
        center = sum(points, Vector()) / len(points)
        if abs(center.x - center_x) < 0.018 and center.y < -0.075 and 1.585 < center.z < 1.630:
            matches.append((component, points, center))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {side} aperture, found {len(matches)}")
    component, points, center = matches[0]
    x_min, x_max = min(point.x for point in points), max(point.x for point in points)
    z_min, z_max = min(point.z for point in points), max(point.z for point in points)
    ordered = sorted(
        ({"index": index, "point": list(world_points[index])} for index in component),
        key=lambda item: item["point"][0],
    )
    eyes[side] = {
        "vertices": len(component),
        "indices": sorted(component),
        "center": list(center),
        "bounds": {"x": [x_min, x_max], "y": [min(point.y for point in points), max(point.y for point in points)], "z": [z_min, z_max]},
        "widthMm": (x_max - x_min) * 1000.0,
        "heightMm": (z_max - z_min) * 1000.0,
        "aspect": (x_max - x_min) / (z_max - z_min),
        "orderedBoundary": ordered,
    }

eye_objects = {}
for obj in bpy.data.objects:
    if obj.name.startswith("Eye_L_") or obj.name.startswith("Eye_R_"):
        eye_objects[obj.name] = {
            "type": obj.type,
            "hiddenRender": obj.hide_render,
            "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
            "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
            "modifiers": [{"name": modifier.name, "type": modifier.type, "showRender": modifier.show_render} for modifier in obj.modifiers],
            "bounds": world_bounds(obj) if obj.type in {"MESH", "CURVE"} else None,
        }

report = {
    "source": str(SOURCE),
    "frame": 1,
    "body": BODY,
    "bodyVertices": len(body.data.vertices),
    "boundaryComponents": len(components),
    "eyes": eyes,
    "eyeObjects": eye_objects,
    "status": "PASS",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R492_EYE_APERTURE=" + json.dumps({
    "status": report["status"],
    "eyes": {side: {key: data[key] for key in ("vertices", "widthMm", "heightMm", "aspect")} for side, data in eyes.items()},
    "eyeObjects": sorted(eye_objects),
}, sort_keys=True))
