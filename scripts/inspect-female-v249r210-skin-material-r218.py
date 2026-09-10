import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-skin-material-r218.inspect.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
material = body.active_material
nodes = material.node_tree.nodes
links = material.node_tree.links
shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")

inputs = {}
for name in (
    "Base Color", "Metallic", "Roughness", "IOR", "Alpha", "Normal",
    "Subsurface Weight", "Subsurface Scale", "Subsurface Radius",
    "Specular IOR Level", "Coat Weight", "Coat Roughness",
):
    socket = shader.inputs.get(name)
    if not socket:
        continue
    value = socket.default_value
    try:
        value = list(value)
    except TypeError:
        value = float(value)
    inputs[name] = {
        "default": value,
        "linkedFrom": [f"{link.from_node.name}.{link.from_socket.name}" for link in socket.links],
    }

interesting = {}
for node in nodes:
    if any(term in node.name.lower() for term in ("skin", "pore", "rough", "bump", "complexion")):
        entry = {"type": node.bl_idname}
        for input_name in ("Strength", "Distance", "Scale", "Detail", "Roughness", "Factor"):
            socket = node.inputs.get(input_name)
            if socket and hasattr(socket, "default_value"):
                try:
                    entry[input_name] = float(socket.default_value)
                except TypeError:
                    pass
        interesting[node.name] = entry

report = {
    "source": str(SOURCE),
    "body": body.name,
    "material": material.name,
    "shader": shader.name,
    "shaderInputs": inputs,
    "interestingNodes": interesting,
    "materialProperties": {key: material[key] for key in material.keys()},
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R218_SKIN_INSPECT=" + json.dumps(report, sort_keys=True))
