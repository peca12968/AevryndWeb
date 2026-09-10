import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v249.blend"


def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    return {
        "min": [round(value, 6) for value in minimum],
        "max": [round(value, 6) for value in maximum],
        "size": [round(maximum[axis] - minimum[axis], 6) for axis in range(3)],
        "center": [round((minimum[axis] + maximum[axis]) * 0.5, 6) for axis in range(3)],
    }


def principled(material):
    if not material or not material.use_nodes:
        return None
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if not shader:
        return None
    names = ("Base Color", "Roughness", "IOR", "Alpha", "Transmission Weight", "Coat Weight", "Subsurface Weight")
    result = {}
    for name in names:
        socket = shader.inputs.get(name)
        if socket is None:
            continue
        value = socket.default_value
        result[name] = [round(component, 6) for component in value] if hasattr(value, "__len__") else round(value, 6)
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
result = {}
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type != "MESH" or not obj.name.startswith("Eye_"):
        continue
    result[obj.name] = {
        "role": obj.get("aevrynd_role"),
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "bounds": bounds(obj),
        "materials": [{"name": material.name, "principled": principled(material)} for material in obj.data.materials if material],
        "scale": [round(value, 6) for value in obj.scale],
        "parent_bone": obj.parent_bone,
    }

print("AEVRYND_EYE_PROPORTIONS_V249=" + json.dumps(result))

