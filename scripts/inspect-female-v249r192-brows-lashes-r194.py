import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brows-lashes-r194.inspect.json"
NAMES = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
)


def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {
        "minimum": [min(point[i] for point in points) for i in range(3)],
        "maximum": [max(point[i] for point in points) for i in range(3)],
    }


def material_report(material):
    result = {"name": material.name, "blendMethod": material.surface_render_method, "nodes": []}
    if not material.use_nodes:
        return result
    for node in material.node_tree.nodes:
        if node.bl_idname not in {"ShaderNodeBsdfPrincipled", "ShaderNodeBsdfHairPrincipled"}:
            continue
        values = {}
        for socket in node.inputs:
            if socket.is_linked or not hasattr(socket, "default_value"):
                continue
            value = socket.default_value
            try:
                value = list(value)
            except TypeError:
                pass
            values[socket.name] = value
        result["nodes"].append({"name": node.name, "type": node.bl_idname, "inputs": values})
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {"source": str(SOURCE), "objects": {}}
for name in NAMES:
    obj = bpy.data.objects[name]
    report["objects"][name] = {
        "type": obj.type,
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
        "boundsWorld": bounds(obj) if obj.type == "MESH" else None,
        "layer": obj.get("aevrynd_layer"),
        "materials": [material_report(material) for material in obj.data.materials],
    }
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R194_BROWS_LASHES_INSPECT=" + json.dumps(report, sort_keys=True))
