import json
import math
from collections import defaultdict
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-philtrum-r80.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-corners-r82.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}


def bounds(mesh, component):
    points = [mesh.vertices[index].co for index in component]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
        "center": [sum(point[axis] for point in points) / len(points) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
mesh = bpy.data.objects[BODY].data
edge_faces = defaultdict(int)
for polygon in mesh.polygons:
    loop = list(polygon.vertices)
    for position, first in enumerate(loop):
        second = loop[(position + 1) % len(loop)]
        edge_faces[tuple(sorted((first, second)))] += 1
boundary_edges = [edge for edge, count in edge_faces.items() if count == 1]
adjacency = defaultdict(set)
for first, second in boundary_edges:
    adjacency[first].add(second)
    adjacency[second].add(first)
remaining = set(adjacency)
components = []
while remaining:
    seed = remaining.pop()
    component = {seed}
    stack = [seed]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in component:
                component.add(neighbor)
                remaining.discard(neighbor)
                stack.append(neighbor)
    components.append(sorted(component))

report = {"source": str(SOURCE), "boundary_edges": len(boundary_edges), "components": [], "eyes": {}}
for index, component in enumerate(components):
    report["components"].append({"index": index, "vertices": len(component), "bounds": bounds(mesh, component)})
for side, center in EYES.items():
    cx, _cy, cz = center
    candidates = []
    for index, component in enumerate(components):
        info = bounds(mesh, component)
        distance = math.hypot(info["center"][0] - cx, info["center"][2] - cz)
        if distance < 0.020 and info["max"][1] < -0.070:
            candidates.append((distance, index, component, info))
    if not candidates:
        raise RuntimeError(f"No eye boundary for {side}")
    _distance, component_index, component, info = min(candidates)
    inner = min(component, key=lambda i: abs(mesh.vertices[i].co.x) + abs(mesh.vertices[i].co.z - cz) * 0.15)
    outer = max(component, key=lambda i: abs(mesh.vertices[i].co.x) - abs(mesh.vertices[i].co.z - cz) * 0.15)
    upper = max(component, key=lambda i: mesh.vertices[i].co.z)
    lower = min(component, key=lambda i: mesh.vertices[i].co.z)
    report["eyes"][side] = {
        "component": component_index,
        "vertices": len(component),
        "bounds": info,
        "width_mm": (info["max"][0] - info["min"][0]) * 1000.0,
        "height_mm": (info["max"][2] - info["min"][2]) * 1000.0,
        "inner": {"index": inner, "co": list(mesh.vertices[inner].co)},
        "outer": {"index": outer, "co": list(mesh.vertices[outer].co)},
        "upper": {"index": upper, "co": list(mesh.vertices[upper].co)},
        "lower": {"index": lower, "co": list(mesh.vertices[lower].co)},
        "degree_histogram": {
            str(degree): sum(len(adjacency[vertex]) == degree for vertex in component)
            for degree in sorted({len(adjacency[vertex]) for vertex in component})
        },
        "vertex_indices": component,
    }
    lateral = 1.0 if side == "L" else -1.0
    visible = {}
    for label, target_x in (
        ("inner", cx - lateral * 0.01045),
        ("outer", cx + lateral * 0.01045),
    ):
        candidate = min(
            (vertex for vertex in mesh.vertices if vertex.co.y < -0.105),
            key=lambda vertex: (
                (vertex.co.x - target_x) ** 2
                + (vertex.co.z - cz) ** 2
                + 0.08 * (vertex.co.y + 0.128) ** 2
            ),
        )
        visible[label] = {
            "index": candidate.index,
            "co": list(candidate.co),
            "target_xz": [target_x, cz],
        }
    report["eyes"][side]["visible_surface_corners"] = visible
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_EYE_CORNERS_R82=" + json.dumps({
    "boundary_edges": len(boundary_edges),
    "components": len(components),
    "eyes": {side: {key: value[key] for key in ("vertices", "width_mm", "height_mm", "degree_histogram")} for side, value in report["eyes"].items()},
}, sort_keys=True))
