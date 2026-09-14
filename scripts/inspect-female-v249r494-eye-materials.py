import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clipped-optical-fronts-r493.blend"
REPORT = ASSETS / "female-v249-mainline-eye-materials-r494.inspection.json"
PARTS = ("Caruncle", "Sclera", "TearMeniscus")


def value(socket):
    raw = getattr(socket, "default_value", None)
    if raw is None:
        return None
    try:
        return [float(item) for item in raw]
    except TypeError:
        return float(raw)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = {}
for side in ("L", "R"):
    for part in PARTS:
        obj = bpy.data.objects[f"Eye_{side}_{part}"]
        materials = []
        for material in obj.data.materials:
            entry = {"name": material.name, "surfaceRenderMethod": material.surface_render_method}
            if material.use_nodes:
                entry["nodes"] = []
                for node in material.node_tree.nodes:
                    if node.bl_idname == "ShaderNodeBsdfPrincipled":
                        entry["nodes"].append({
                            "name": node.name,
                            "inputs": {
                                name: {"linked": node.inputs[name].is_linked, "value": value(node.inputs[name])}
                                for name in ("Base Color", "Roughness", "Specular IOR Level", "Subsurface Weight", "Coat Weight", "Coat Roughness", "Alpha")
                                if node.inputs.get(name)
                            },
                        })
                    elif node.bl_idname == "ShaderNodeTexImage" and node.image:
                        entry["nodes"].append({"name": node.name, "image": node.image.name, "path": bpy.path.abspath(node.image.filepath)})
            materials.append(entry)
        objects[obj.name] = {
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": materials,
        }

report = {"source": str(SOURCE), "objects": objects, "status": "PASS"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R494_EYE_MATERIALS=" + json.dumps(report, sort_keys=True))
