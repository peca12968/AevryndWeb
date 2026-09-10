import json
from collections import defaultdict, deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-topology.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}


def bounds(vertices, indices):
    values = [vertices[index].co for index in indices]
    return {
        "min": [min(point[axis] for point in values) for axis in range(3)],
        "max": [max(point[axis] for point in values) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
mesh = bpy.data.objects[BODY].data
edge_faces = defaultdict(list)
adjacency = defaultdict(set)
for polygon in mesh.polygons:
    loop = list(polygon.vertices)
    for position, first in enumerate(loop):
        second = loop[(position + 1) % len(loop)]
        edge = tuple(sorted((first, second)))
        edge_faces[edge].append(polygon.index)
        adjacency[first].add(second)
        adjacency[second].add(first)

boundary_edges = [edge for edge, faces in edge_faces.items() if len(faces) == 1]
boundary_adjacency = defaultdict(set)
for first, second in boundary_edges:
    boundary_adjacency[first].add(second)
    boundary_adjacency[second].add(first)

components = []
remaining = set(boundary_adjacency)
while remaining:
    start = remaining.pop()
    component = {start}
    queue = [start]
    while queue:
        current = queue.pop()
        for neighbor in boundary_adjacency[current]:
            if neighbor not in component:
                component.add(neighbor)
                remaining.discard(neighbor)
                queue.append(neighbor)
    components.append(sorted(component))

report = {
    "source": str(SOURCE),
    "body": BODY,
    "vertices": len(mesh.vertices),
    "polygons": len(mesh.polygons),
    "boundary_edges": len(boundary_edges),
    "boundary_components": [],
    "eyes": {},
}

for component_index, component in enumerate(components):
    component_bounds = bounds(mesh.vertices, component)
    report["boundary_components"].append({
        "index": component_index,
        "vertices": len(component),
        "bounds": component_bounds,
    })

for side, center in EYE_CENTERS.items():
    cx, cy, cz = center
    nearby_components = []
    for component_index, component in enumerate(components):
        selected = [
            index for index in component
            if abs(mesh.vertices[index].co.x - cx) < 0.032
            and abs(mesh.vertices[index].co.z - cz) < 0.024
            and mesh.vertices[index].co.y < -0.088
        ]
        if selected:
            nearby_components.append((component_index, selected))

    seed = set(index for _, selected in nearby_components for index in selected)
    rings = []
    visited = set(seed)
    frontier = set(seed)
    for distance in range(5):
        rings.append(sorted(frontier))
        next_frontier = set()
        for vertex in frontier:
            next_frontier.update(adjacency[vertex])
        next_frontier -= visited
        visited.update(next_frontier)
        frontier = next_frontier

    report["eyes"][side] = {
        "center": center,
        "boundary_components": [index for index, _ in nearby_components],
        "boundary_vertices": sorted(seed),
        "boundary_vertex_count": len(seed),
        "boundary_bounds": bounds(mesh.vertices, seed) if seed else None,
        "topology_rings": [
            {
                "distance": distance,
                "count": len(ring),
                "vertices": ring,
                "bounds": bounds(mesh.vertices, ring) if ring else None,
            }
            for distance, ring in enumerate(rings)
        ],
    }

OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_EYE_TOPOLOGY=" + json.dumps({
    "boundary_components": len(components),
    "eyes": {
        side: {
            "boundary_vertices": values["boundary_vertex_count"],
            "rings": [ring["count"] for ring in values["topology_rings"]],
        }
        for side, values in report["eyes"].items()
    },
}, sort_keys=True))
