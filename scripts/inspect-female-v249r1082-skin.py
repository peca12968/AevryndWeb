"""Inspect the retained r1081 body material before the r1082 skin sweep."""
import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-graded-hairline-r1081-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1082-skin.inspection.json"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
materials = []
for material in body.data.materials:
    nodes = []
    links = []
    if material and material.use_nodes:
        for node in material.node_tree.nodes:
            item = {"name": node.name, "type": node.bl_idname}
            if node.type == "BSDF_PRINCIPLED":
                item["principled"] = {
                    socket.name: socket.default_value[:] if hasattr(socket.default_value, "__len__") else socket.default_value
                    for socket in node.inputs
                    if socket.name in {"Base Color", "Roughness", "IOR", "Alpha", "Subsurface Weight", "Subsurface Scale", "Specular IOR Level", "Coat Weight", "Coat Roughness"}
                }
            if node.type == "TEX_NOISE":
                item["noise"] = {
                    socket.name: socket.default_value
                    for socket in node.inputs
                    if socket.name in {"Scale", "Detail", "Roughness", "Lacunarity", "Distortion"}
                }
            if node.type == "ATTRIBUTE":
                item["attributeName"] = node.attribute_name
            if node.type == "VALTORGB":
                item["ramp"] = [{"position": element.position, "color": list(element.color)} for element in node.color_ramp.elements]
            if node.type == "BUMP":
                item["bump"] = {socket.name: socket.default_value for socket in node.inputs if socket.name in {"Strength", "Distance", "Invert"}}
            if node.type == "MATH":
                item["math"] = {"operation": node.operation, "inputs": [socket.default_value for socket in node.inputs]}
            nodes.append(item)
        links = [f"{link.from_node.name}.{link.from_socket.name}->{link.to_node.name}.{link.to_socket.name}" for link in material.node_tree.links]
    materials.append({"name": material.name if material else None, "nodes": nodes, "links": links})

report = {
    "revision": "v249r1082-skin-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "vertices": len(body.data.vertices),
    "faces": len(body.data.polygons),
    "shapeKeys": [block.name for block in body.data.shape_keys.key_blocks],
    "uvLayers": [layer.name for layer in body.data.uv_layers],
    "attributes": [{"name": item.name, "dataType": item.data_type, "domain": item.domain} for item in body.data.attributes],
    "vertexGroups": [group.name for group in body.vertex_groups],
    "materialSlots": len(body.data.materials),
    "materials": materials,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1082_SKIN_INSPECTION=" + json.dumps({"materialSlots": report["materialSlots"], "uvLayers": report["uvLayers"], "attributes": len(report["attributes"]), "vertexGroups": report["vertexGroups"], "materials": [item["name"] for item in materials]}, sort_keys=True))
