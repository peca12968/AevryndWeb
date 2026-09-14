import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"
REPORT = ASSETS / "female-v249-mainline-eye-socket-clearance-r525.inspection.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": 0.03453, "R": -0.03444}


def boundary_components(mesh):
    edge_faces = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            second = vertices[(index + 1) % len(vertices)]
            edge_faces[tuple(sorted((first, second)))] += 1
    for (first, second), count in edge_faces.items():
        if count == 1:
            adjacency[first].add(second)
            adjacency[second].add(first)
    result, unseen = [], set(adjacency)
    while unseen:
        start = unseen.pop()
        component, queue = {start}, deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def evaluated_base_points(obj):
    basis = obj.data.shape_keys.key_blocks[0]
    keys = obj.data.shape_keys.key_blocks
    points = []
    for index, point in enumerate(basis.data):
        value = point.co.copy()
        for key in keys[1:]:
            value += (key.data[index].co - basis.data[index].co) * key.value
        points.append(obj.matrix_world @ value)
    return points


def surface_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
points = evaluated_base_points(body)
components = boundary_components(body.data)
result = {}
for side, center_x in EYE_CENTERS.items():
    candidates = []
    for component in components:
        center = sum((points[index] for index in component), Vector()) / len(component)
        if abs(center.x - center_x) < 0.018 and center.y < -0.075 and 1.585 < center.z < 1.630:
            candidates.append(component)
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one {side} eye boundary, found {len(candidates)}")
    optical = {
        part: surface_tree(bpy.data.objects[f"Eye_{side}_{part}"], depsgraph)
        for part in ("Cornea", "Sclera")
    }
    samples = []
    for index in sorted(candidates[0]):
        point = points[index]
        nearest = []
        for part, tree in optical.items():
            hit, normal, polygon, distance = tree.find_nearest(point)
            nearest.append((distance, part, hit, normal, polygon))
        distance, part, hit, normal, polygon = min(nearest, key=lambda item: item[0])
        vector = hit - point
        samples.append(
            {
                "vertex": index,
                "part": part,
                "distanceMm": distance * 1000.0,
                "vectorMm": [component * 1000.0 for component in vector],
                "boundary": list(point),
                "nearest": list(hit),
                "normal": list(normal),
                "polygon": polygon,
            }
        )
    distances = [sample["distanceMm"] for sample in samples]
    result[side] = {
        "boundaryVertices": len(samples),
        "minimumDistanceMm": min(distances),
        "medianDistanceMm": sorted(distances)[len(distances) // 2],
        "maximumDistanceMm": max(distances),
        "samples": samples,
    }

report = {
    "source": str(SOURCE),
    "frame": 1,
    "method": "current mixed base-topology eye boundary to nearest evaluated cornea/sclera surface",
    "eyes": result,
    "status": "MEASURED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(
    "AEVRYND_R525_SOCKET_CLEARANCE="
    + json.dumps(
        {
            side: {key: value for key, value in data.items() if key != "samples"}
            for side, data in result.items()
        },
        sort_keys=True,
    )
)
