import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-lower-lashes-r498.blend"
REPORT = ASSETS / "female-v249-mainline-tear-film-r498.inspection.json"


def socket(shader, name):
    value = shader.inputs.get(name)
    if value is None:
        return None
    default = value.default_value
    try:
        return [float(item) for item in default]
    except TypeError:
        return float(default)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {"source": str(SOURCE), "layers": {}}
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_TearMeniscus"]
    material = obj.active_material
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    report["layers"][obj.name] = {
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "hideRender": obj.hide_render,
        "material": material.name,
        "surfaceRenderMethod": getattr(material, "surface_render_method", None),
        "useSurfaceRefraction": getattr(material, "use_transparency_overlap", None),
        "sockets": {
            name: socket(shader, name)
            for name in (
                "Base Color", "Metallic", "Roughness", "IOR", "Alpha",
                "Specular IOR Level", "Transmission Weight", "Coat Weight", "Coat Roughness",
            )
        },
        "nodeCount": len(material.node_tree.nodes),
        "linkCount": len(material.node_tree.links),
    }
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R498_TEAR_FILM=" + json.dumps(report, sort_keys=True))
