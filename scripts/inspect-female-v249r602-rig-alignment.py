import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MAINLINE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
FOUNDATION = ASSETS / "aevrynd-female-cc0-fitted-eye-skin-foundation-r602.blend"
REPORT = ASSETS / "female-v249r602-rig-alignment.inspect.json"


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return {
        "min": list(low),
        "max": list(high),
        "dimensions": list(high - low),
        "center": list((low + high) * 0.5),
    }


def group_centers(obj):
    result = {}
    for group in obj.vertex_groups:
        total = Vector()
        weight_sum = 0.0
        count = 0
        for vertex in obj.data.vertices:
            try:
                weight = group.weight(vertex.index)
            except RuntimeError:
                continue
            if weight <= 0.0:
                continue
            total += (obj.matrix_world @ vertex.co) * weight
            weight_sum += weight
            count += 1
        if weight_sum:
            result[group.name] = {"center": list(total / weight_sum), "vertices": count, "weight": weight_sum}
    return result


def find_mesh(preferred):
    obj = bpy.data.objects.get(preferred)
    if obj and obj.type == "MESH":
        return obj
    candidates = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    return max(candidates, key=lambda item: len(item.data.vertices))


def mainline_data():
    bpy.ops.wm.open_mainfile(filepath=str(MAINLINE))
    body = find_mesh("AevryndFemaleBodyBaseV118")
    rig = bpy.data.objects.get("AevryndFemaleRig")
    if rig is None:
        rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
        rig = max(rigs, key=lambda item: len(item.data.bones))
    bones = {
        bone.name: {
            "head": list(rig.matrix_world @ bone.head_local),
            "tail": list(rig.matrix_world @ bone.tail_local),
            "parent": bone.parent.name if bone.parent else None,
        }
        for bone in rig.data.bones
    }
    return {
        "file": str(MAINLINE),
        "body": body.name,
        "bodyBounds": bounds(body),
        "bodyVertexCount": len(body.data.vertices),
        "bodyGroups": group_centers(body),
        "rig": rig.name,
        "rigBounds": bounds(rig),
        "bones": bones,
    }


def foundation_data():
    bpy.ops.wm.open_mainfile(filepath=str(FOUNDATION))
    body = find_mesh("AevryndFemaleCC0Baseline_v259")
    return {
        "file": str(FOUNDATION),
        "body": body.name,
        "bodyBounds": bounds(body),
        "bodyVertexCount": len(body.data.vertices),
        "bodyGroups": group_centers(body),
        "shapeKeys": [key.name for key in body.data.shape_keys.key_blocks] if body.data.shape_keys else [],
    }


mainline = mainline_data()
foundation = foundation_data()
scale = mainline["bodyBounds"]["dimensions"][2] / foundation["bodyBounds"]["dimensions"][2]
common = sorted(set(mainline["bodyGroups"]) & set(foundation["bodyGroups"]))
report = {
    "mainline": mainline,
    "foundation": foundation,
    "uniformHeightScale": scale,
    "commonVertexGroups": common,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R602_RIG_ALIGNMENT=" + json.dumps({
    "mainlineBody": mainline["body"],
    "foundationBody": foundation["body"],
    "scale": scale,
    "commonGroups": len(common),
    "mainlineBones": len(mainline["bones"]),
}, sort_keys=True))
