import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-smoothed-hair-r232.blend"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"


def socket_value(socket):
    if socket.is_linked:
        return "linked"
    if not hasattr(socket, "default_value"):
        return None
    value = socket.default_value
    try:
        return [float(item) for item in value]
    except TypeError:
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
obj = bpy.data.objects[SCALP]
materials = []
for material in obj.data.materials:
    if material is None:
        continue
    nodes = []
    for node in material.node_tree.nodes if material.use_nodes else ():
        nodes.append({
            "name": node.name,
            "type": node.bl_idname,
            "inputs": {socket.name: socket_value(socket) for socket in node.inputs},
        })
    materials.append({
        "name": material.name,
        "surfaceRenderMethod": getattr(material, "surface_render_method", None),
        "nodes": nodes,
        "links": [
            f"{link.from_node.name}.{link.from_socket.name}->{link.to_node.name}.{link.to_socket.name}"
            for link in material.node_tree.links
        ] if material.use_nodes else [],
    })
print("AEVRYND_V249R232_SCALP_MATERIAL=" + json.dumps({
    "source": str(SOURCE),
    "object": SCALP,
    "materials": materials,
    "attributes": [attribute.name for attribute in obj.data.attributes],
}, sort_keys=True))
