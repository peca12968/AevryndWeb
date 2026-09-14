import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-runtime-hair-r499.inspection.json"
REGIONS = ("front", "crown", "rear", "hairline")
POINTS = 24


def statistics(values):
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {"minimum": min(values), "maximum": max(values), "mean": mean, "standardDeviation": math.sqrt(variance)}


def bounds(points):
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
report = {"source": str(SOURCE), "regions": {}, "frames": {}}
for region in REGIONS:
    obj = bpy.data.objects[f"AevryndFemaleRuntimeCards_{region}_R467"]
    cards = int(obj.get("aevrynd_card_count", 0))
    stride = POINTS * 2
    if len(obj.data.vertices) != cards * stride:
        raise RuntimeError(f"Unexpected card layout on {obj.name}")
    roots, mids, tails = [], [], []
    for card in range(cards):
        centers = [
            (obj.data.vertices[card * stride + row * 2].co + obj.data.vertices[card * stride + row * 2 + 1].co) * 0.5
            for row in range(POINTS)
        ]
        roots.append(obj.matrix_world @ centers[0])
        mids.append(obj.matrix_world @ centers[POINTS // 2])
        tails.append(obj.matrix_world @ centers[-1])
    material = obj.active_material
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    report["regions"][region] = {
        "object": obj.name,
        "cards": cards,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "material": material.name if material else None,
        "materialNodes": len(material.node_tree.nodes) if material and material.use_nodes else 0,
        "baseColorLinked": bool(shader and shader.inputs["Base Color"].is_linked),
        "roughness": float(shader.inputs["Roughness"].default_value) if shader else None,
        "rootBounds": bounds(roots),
        "midBounds": bounds(mids),
        "tailBounds": bounds(tails),
        "tailZ": statistics([point.z for point in tails]),
        "tailX": statistics([point.x for point in tails]),
        "tailY": statistics([point.y for point in tails]),
        "vertexGroups": [group.name for group in obj.vertex_groups],
        "modifiers": [{"name": modifier.name, "type": modifier.type, "object": modifier.object.name if getattr(modifier, "object", None) else None} for modifier in obj.modifiers],
    }
for frame in (1, 20, 33, 61):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    report["frames"][str(frame)] = {}
    for region in REGIONS:
        obj = bpy.data.objects[f"AevryndFemaleRuntimeCards_{region}_R467"].evaluated_get(depsgraph)
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        report["frames"][str(frame)][region] = bounds(points)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R499_RUNTIME_HAIR=" + json.dumps({region: {
    "cards": value["cards"],
    "vertices": value["vertices"],
    "tailZStdM": value["tailZ"]["standardDeviation"],
    "tailZRangeM": [value["tailZ"]["minimum"], value["tailZ"]["maximum"]],
} for region, value in report["regions"].items()}, sort_keys=True))
