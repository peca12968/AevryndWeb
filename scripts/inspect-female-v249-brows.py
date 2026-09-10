import bpy
import json
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"


def components(mesh):
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(adjacency)
    result = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        result.append(sorted(group))
    return result


def world_tree(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(points, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
body_tree = world_tree(body)
report = {}
for name in ("Brow_L", "Brow_R", "Brow_L_Density", "Brow_R_Density"):
    obj = bpy.data.objects[name]
    groups = components(obj.data)
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    distances = [body_tree.find_nearest(point)[3] * 1000.0 for point in points]
    centers = []
    spans = []
    for group in groups:
        group_points = [obj.matrix_world @ obj.data.vertices[index].co for index in group]
        centers.append(sum(group_points, group_points[0] * 0.0) / len(group_points))
        spans.append(max((a - b).length for a in group_points for b in group_points) * 1000.0)
    report[name] = {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "components": len(groups),
        "span_mm": [min(spans), sum(spans) / len(spans), max(spans)],
        "distance_mm": [min(distances), sum(distances) / len(distances), max(distances)],
        "bounds": [[min(point[i] for point in points), max(point[i] for point in points)] for i in range(3)],
        "materials": [material.name for material in obj.data.materials if material],
        "custom": {key: obj[key] for key in obj.keys() if key.startswith("aevrynd")},
    }
print("AEVRYND_V249_BROWS=" + json.dumps(report, sort_keys=True))
