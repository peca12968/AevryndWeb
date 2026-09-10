import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hair-shader-r190.inspect.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
material = bpy.data.materials["AevryndOwnedLayeredHairMaterial_v249r129"]
group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
tree = group.node_tree
report = {
    "source": str(SOURCE),
    "material": material.name,
    "group": tree.name,
    "groupInputs": {socket.name: repr(socket.default_value) for socket in group.inputs},
    "nodes": [],
    "links": [],
}
for node in tree.nodes:
    item = {"name": node.name, "type": node.bl_idname, "inputs": {}}
    for socket in node.inputs:
        if not socket.is_linked and hasattr(socket, "default_value"):
            value = socket.default_value
            try:
                value = list(value)
            except TypeError:
                pass
            item["inputs"][socket.name] = value
    report["nodes"].append(item)
for link in tree.links:
    report["links"].append({
        "fromNode": link.from_node.name,
        "fromSocket": link.from_socket.name,
        "toNode": link.to_node.name,
        "toSocket": link.to_socket.name,
    })
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R190_SHADER_INSPECT=" + json.dumps(report, sort_keys=True))
