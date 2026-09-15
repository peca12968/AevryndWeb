"""Record topology and transform facts needed to combine female character branches."""

import json
import os
from pathlib import Path

import bpy


def world_bounds(obj):
    corners = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(point[axis] for point in corners), 6) for axis in range(3)],
        "max": [round(max(point[axis] for point in corners), 6) for axis in range(3)],
    }


def mesh_record(obj):
    data = obj.data
    modifiers = []
    for modifier in obj.modifiers:
        record = {"name": modifier.name, "type": modifier.type}
        if modifier.type == "ARMATURE":
            record["object"] = modifier.object.name if modifier.object else None
        modifiers.append(record)
    return {
        "name": obj.name,
        "vertices": len(data.vertices),
        "edges": len(data.edges),
        "polygons": len(data.polygons),
        "shapeKeys": len(data.shape_keys.key_blocks) if data.shape_keys else 0,
        "vertexGroups": len(obj.vertex_groups),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "parent": obj.parent.name if obj.parent else None,
        "parentType": obj.parent_type,
        "parentBone": obj.parent_bone or None,
        "hiddenViewport": obj.hide_get(),
        "hiddenRender": obj.hide_render,
        "modifiers": modifiers,
        "location": [round(value, 6) for value in obj.location],
        "rotationEuler": [round(value, 6) for value in obj.rotation_euler],
        "scale": [round(value, 6) for value in obj.scale],
        "worldBounds": world_bounds(obj),
        "headRegionBounds": regional_bounds(obj),
    }


def regional_bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    if not points:
        return None
    z_min = min(point.z for point in points)
    z_max = max(point.z for point in points)
    cutoff = z_min + (z_max - z_min) * 0.82
    selected = [point for point in points if point.z >= cutoff]
    return {
        "cutoff": round(cutoff, 6),
        "min": [round(min(point[axis] for point in selected), 6) for axis in range(3)],
        "max": [round(max(point[axis] for point in selected), 6) for axis in range(3)],
    }


def is_hair_like(obj):
    labels = [obj.name]
    labels.extend(slot.material.name for slot in obj.material_slots if slot.material)
    joined = " ".join(labels).lower()
    return any(token in joined for token in ("hair", "scalp", "brow", "lash", "flyaway", "groom"))


meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
largest = sorted(meshes, key=lambda obj: len(obj.data.vertices), reverse=True)
report = {
    "blend": bpy.data.filepath,
    "sceneRevision": {
        key: value
        for key, value in bpy.context.scene.items()
        if isinstance(key, str) and key.startswith("aevrynd_")
    },
    "counts": {
        "objects": len(bpy.data.objects),
        "meshes": len(meshes),
        "materials": len(bpy.data.materials),
        "armatures": len(armatures),
    },
    "largestMeshes": [mesh_record(obj) for obj in largest[:8]],
    "hairMeshes": [mesh_record(obj) for obj in meshes if is_hair_like(obj)],
    "featureMeshes": [
        mesh_record(obj)
        for obj in meshes
        if any(token in obj.name.lower() for token in ("eye_", "body", "head", "mouth", "lip"))
    ],
    "armatures": [
        {
            "name": obj.name,
            "bones": len(obj.data.bones),
            "location": [round(value, 6) for value in obj.location],
            "rotationEuler": [round(value, 6) for value in obj.rotation_euler],
            "scale": [round(value, 6) for value in obj.scale],
            "worldBounds": world_bounds(obj),
        }
        for obj in armatures
    ],
}

output = Path(os.environ["AEVRYND_INSPECTION_OUTPUT"])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"AEVRYND_INSPECTION_OUTPUT={output}")
