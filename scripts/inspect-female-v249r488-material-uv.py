import json
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-lower-lip-r485.blend"
BODY = "AevryndFemaleBodyBaseV118"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
material = body.active_material
principled = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
normal = principled.inputs.get("Normal") if principled else None

report = {
    "source": str(SOURCE),
    "body": BODY,
    "vertices": len(body.data.vertices),
    "loops": len(body.data.loops),
    "polygons": len(body.data.polygons),
    "uvLayers": [u.name for u in body.data.uv_layers],
    "colorAttributes": [
        {
            "name": a.name,
            "domain": a.domain,
            "dataType": a.data_type,
            "min": min((min(item.color) for item in a.data), default=None) if hasattr(a.data[0] if len(a.data) else None, "color") else None,
            "max": max((max(item.color) for item in a.data), default=None) if hasattr(a.data[0] if len(a.data) else None, "color") else None,
            "redQuantiles": [float(value) for value in np.quantile([item.color[0] for item in a.data], [0, 0.5, 0.9, 0.95, 0.99, 0.999, 1])] if len(a.data) and hasattr(a.data[0], "color") else None,
            "redPositive": sum(1 for item in a.data if hasattr(item, "color") and item.color[0] > 0.001),
            "redAboveHalf": sum(1 for item in a.data if hasattr(item, "color") and item.color[0] > 0.5),
        }
        for a in body.data.color_attributes
    ],
    "material": material.name if material else None,
    "nodes": [
        {"name": n.name, "label": n.label, "type": n.bl_idname}
        for n in material.node_tree.nodes
    ] if material and material.use_nodes else [],
    "principledNormal": {
        "linked": bool(normal and normal.is_linked),
        "fromNode": normal.links[0].from_node.name if normal and normal.is_linked else None,
        "fromSocket": normal.links[0].from_socket.name if normal and normal.is_linked else None,
    },
}
print("AEVRYND_R488_INSPECT=" + json.dumps(report, sort_keys=True))
