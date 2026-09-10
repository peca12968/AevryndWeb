import json
from collections import deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brow-components-r211.inspect.json"
BROWS = ("Brow_L", "Brow_R")


def components(mesh):
    adjacency = [set() for _ in mesh.vertices]
    for edge in mesh.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    unseen = set(range(len(mesh.vertices)))
    result = []
    while unseen:
        seed = min(unseen)
        queue = deque([seed])
        unseen.remove(seed)
        group = []
        while queue:
            current = queue.popleft()
            group.append(current)
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(group))
    return result


def component_metrics(obj, indices):
    points = [obj.matrix_world @ obj.data.vertices[index].co for index in indices]
    ordered_y = sorted(points, key=lambda point: point.y, reverse=True)
    sample = max(1, min(5, len(points) // 4))
    root = sum(ordered_y[:sample], ordered_y[0] * 0.0) / sample
    tip = sum(ordered_y[-sample:], ordered_y[0] * 0.0) / sample
    direction = tip - root
    return {
        "vertices": len(indices),
        "indices": indices,
        "root": list(root),
        "tip": list(tip),
        "lengthMm": direction.length * 1000.0,
        "direction": list(direction.normalized()) if direction.length else [0.0, 0.0, 0.0],
        "bounds": {
            "min": [min(point[axis] for point in points) for axis in range(3)],
            "max": [max(point[axis] for point in points) for axis in range(3)],
        },
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {"source": str(SOURCE), "brows": {}}
for name in BROWS:
    obj = bpy.data.objects[name]
    groups = components(obj.data)
    metrics = [component_metrics(obj, group) for group in groups]
    report["brows"][name] = {
        "componentCount": len(groups),
        "componentVertexCounts": sorted(set(len(group) for group in groups)),
        "lengthMm": {
            "min": min(item["lengthMm"] for item in metrics),
            "mean": sum(item["lengthMm"] for item in metrics) / len(metrics),
            "max": max(item["lengthMm"] for item in metrics),
        },
        "components": metrics,
    }
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R211_BROW_COMPONENTS=" + json.dumps({
    name: {
        "components": data["componentCount"],
        "vertexCounts": data["componentVertexCounts"],
        "lengthMm": data["lengthMm"],
    }
    for name, data in report["brows"].items()
}, sort_keys=True))
