import json
from collections import defaultdict, deque

import bpy


BODY_NAME = "AevryndFemaleBodyBase"
body = bpy.data.objects[BODY_NAME]
mesh = body.data

# Mesh edge data does not expose adjacent faces directly. Count polygon use.
edge_uses = defaultdict(int)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        edge_uses[tuple(sorted((start, end)))] += 1
boundary_pairs = [edge for edge, uses in edge_uses.items() if uses == 1]

neighbors = defaultdict(set)
for a, b in boundary_pairs:
    neighbors[a].add(b)
    neighbors[b].add(a)

components = []
remaining = set(neighbors)
while remaining:
    start = remaining.pop()
    queue = deque([start])
    component = {start}
    while queue:
        current = queue.popleft()
        for neighbor in neighbors[current]:
            if neighbor not in component:
                component.add(neighbor)
                remaining.discard(neighbor)
                queue.append(neighbor)
    points = [body.matrix_world @ mesh.vertices[index].co for index in component]
    components.append(
        {
            "vertices": len(component),
            "center": [round(sum(point[axis] for point in points) / len(points), 6) for axis in range(3)],
            "min": [round(min(point[axis] for point in points), 6) for axis in range(3)],
            "max": [round(max(point[axis] for point in points), 6) for axis in range(3)],
        }
    )

head_points = [body.matrix_world @ vertex.co for vertex in mesh.vertices if (body.matrix_world @ vertex.co).z > 1.42]
bands = []
for lower_mm in range(1420, 1720, 20):
    lower = lower_mm / 1000
    upper = lower + 0.02
    points = [point for point in head_points if lower <= point.z < upper]
    if points:
        bands.append(
            {
                "z": [round(lower, 3), round(upper, 3)],
                "count": len(points),
                "x": [round(min(p.x for p in points), 4), round(max(p.x for p in points), 4)],
                "y": [round(min(p.y for p in points), 4), round(max(p.y for p in points), 4)],
            }
        )

print("AEVRYND_TOPOLOGY=" + json.dumps({"boundary_components": components, "head_bands": bands}))
