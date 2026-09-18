"""Inspect the r1078 outer aperture loops before r1079 canthus editing."""
import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1079-canthus-topology.inspection.json"
BODY = "AevryndFemaleCC0EyelidInnerWall_R1078"
ORIGINAL_VERTEX_COUNT = 13817


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or block.name in ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030") or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def ordered_loop(edges):
    adjacency = defaultdict(list)
    for a, b in edges:
        adjacency[a].append(b); adjacency[b].append(a)
    assert all(len(values) == 2 for values in adjacency.values())
    start = min(adjacency)
    loop, previous, current = [start], None, start
    while True:
        following = adjacency[current][0] if adjacency[current][0] != previous else adjacency[current][1]
        if following == start:
            break
        loop.append(following); previous, current = current, following
    return loop


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
points = active_coordinates(body)
outer_edges = []
# The appended first-wall faces are the only polygons containing two old and two new vertices.
for polygon in body.data.polygons:
    old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
    new = [index for index in polygon.vertices if index >= ORIGINAL_VERTEX_COUNT]
    if len(old) == 2 and len(new) == 2:
        outer_edges.append(tuple(old))

loops = []
unused = set(tuple(sorted(edge)) for edge in outer_edges)
while unused:
    seed = next(iter(unused)); component, frontier = set(seed), list(seed)
    while frontier:
        vertex = frontier.pop()
        for edge in list(unused):
            if vertex in edge:
                unused.remove(edge)
                for item in edge:
                    if item not in component: component.add(item); frontier.append(item)
    component_edges = [edge for edge in outer_edges if edge[0] in component and edge[1] in component]
    loops.append(ordered_loop(component_edges))

result = {}
for loop in loops:
    side = "L" if sum(points[index].x for index in loop) > 0 else "R"
    center_x = sum(points[index].x for index in loop) / len(loop)
    center_z = sum(points[index].z for index in loop) / len(loop)
    ordered = sorted(loop, key=lambda index: (points[index].x if side == "L" else -points[index].x))
    medial = ordered[:5]
    lateral = ordered[-5:]
    medial_tip = min(loop, key=lambda index: points[index].x if side == "L" else -points[index].x)
    lateral_tip = max(loop, key=lambda index: points[index].x if side == "L" else -points[index].x)
    start = loop.index(medial_tip); rotated = loop[start:] + loop[:start]
    split = rotated.index(lateral_tip)
    path_a, path_b = rotated[:split + 1], [rotated[0]] + list(reversed(rotated[split:]))
    upper, lower = sorted((path_a, path_b), key=lambda path: sum(points[index].z for index in path) / len(path), reverse=True)
    result[side] = {
        "count": len(loop), "center": [center_x, center_z],
        "bounds": {axis: [min(getattr(points[index], axis) for index in loop), max(getattr(points[index], axis) for index in loop)] for axis in ("x", "y", "z")},
        "medialFive": [{"index": index, "xyz": list(points[index])} for index in medial],
        "lateralFive": [{"index": index, "xyz": list(points[index])} for index in lateral],
        "upperPath": [{"index": index, "xyz": list(points[index])} for index in upper],
        "lowerPath": [{"index": index, "xyz": list(points[index])} for index in lower],
        "allByX": [{"index": index, "xyz": list(points[index]), "zOffsetMm": 1000.0 * (points[index].z-center_z)} for index in ordered],
    }

report = {"revision": "v249r1079-canthus-topology-inspection", "source": str(SOURCE), "body": BODY, "originalVertexCount": ORIGINAL_VERTEX_COUNT, "loops": result}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1079_CANTHUS_TOPOLOGY=" + json.dumps({side: {"count": item["count"], "bounds": item["bounds"], "medial": item["medialFive"], "lateral": item["lateralFive"]} for side,item in result.items()}, sort_keys=True))
