import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {}
for object_name in (
    "HairScalp", "HairCoverageTiles_v246", "HairSilhouetteCards_v246",
    "HairDetailFibers_v246", "HairlineNaturalCards_v214",
):
    obj = bpy.data.objects[object_name]
    materials = []
    for material in obj.data.materials:
        shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        values = {}
        if shader:
            for name in ("Base Color", "Roughness", "Specular IOR Level", "Anisotropic IOR Level", "Coat Weight", "Alpha"):
                socket = shader.inputs.get(name)
                if socket:
                    value = socket.default_value
                    values[name] = list(value) if hasattr(value, "__len__") else value
        materials.append({"name": material.name, "surface": material.surface_render_method, "values": values})
    report[object_name] = materials
print("AEVRYND_V249_HAIR_MATERIALS=" + json.dumps(report, sort_keys=True))
