import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUTPUT = ROOT / "assets-source/reference/blender-official-hair/LONG-HAIR-SCENE-R124.json"


def bounds(obj):
    if not getattr(obj, "bound_box", None):
        return None
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = []
for obj in bpy.data.objects:
    objects.append({
        "name": obj.name,
        "type": obj.type,
        "hideRender": obj.hide_render,
        "hideViewport": obj.hide_viewport,
        "bounds": bounds(obj),
        "materials": [material.name for material in getattr(getattr(obj, "data", None), "materials", []) if material],
        "modifiers": [{
            "name": modifier.name,
            "type": modifier.type,
            "nodeGroup": modifier.node_group.name if modifier.type == "NODES" and modifier.node_group else None,
        } for modifier in obj.modifiers],
    })

report = {
    "source": str(SOURCE),
    "scene": bpy.context.scene.name,
    "camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
    "objects": objects,
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_LONG_HAIR_SCENE_R124=" + json.dumps(report, sort_keys=True))
