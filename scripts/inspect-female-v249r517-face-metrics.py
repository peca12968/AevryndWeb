import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
REPORT = ASSETS / "female-v249-mainline-layered-front-locks-r517.face-metrics.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.03453, 1.60780), "R": (-0.03444, 1.60780)}


def boundary_components(mesh):
    counts = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        verts = list(polygon.vertices)
        for index, first in enumerate(verts):
            second = verts[(index + 1) % len(verts)]
            counts[tuple(sorted((first, second)))] += 1
    for (first, second), count in counts.items():
        if count == 1:
            adjacency[first].add(second)
            adjacency[second].add(first)
    components, unseen = [], set(adjacency)
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
        components.append(component)
    return components


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()

metrics = {}
for side, (cx, cz) in EYES.items():
    matches = []
    for component in boundary_components(body.data):
        center = sum((points[index] for index in component), Vector()) / len(component)
        if abs(center.x - cx) < 0.018 and center.y < -0.075 and abs(center.z - cz) < 0.020:
            matches.append(component)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {side} eye boundary, found {len(matches)}")
    eye_points = [points[index] for index in matches[0]]
    width = max(p.x for p in eye_points) - min(p.x for p in eye_points)
    height = max(p.z for p in eye_points) - min(p.z for p in eye_points)
    metrics[side] = {
        "vertices": len(matches[0]),
        "indices": sorted(matches[0]),
        "widthMm": width * 1000.0,
        "heightMm": height * 1000.0,
        "aspect": width / height,
        "center": list(sum(eye_points, Vector()) / len(eye_points)),
    }

report = {
    "source": str(SOURCE),
    "sceneRevision": scene.get("aevrynd_mainline_revision"),
    "sceneParent": scene.get("aevrynd_mainline_parent"),
    "bodyShapeKeys": [key.name for key in body.data.shape_keys.key_blocks],
    "bodyVertices": len(body.data.vertices),
    "bodyPolygons": len(body.data.polygons),
    "eyes": metrics,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R517_FACE_METRICS=" + json.dumps(report, sort_keys=True))
