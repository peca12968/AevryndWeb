import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-soft-rear-fan-cards-r467.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r467.eye-stack-inspection.json"
TOKENS = ("eye", "iris", "cornea", "sclera", "pupil", "limbal", "catch", "tear", "caruncle", "lid", "lash", "brow")


def input_value(socket):
    value = getattr(socket, "default_value", None)
    if value is None:
        return None
    try:
        return list(value)
    except TypeError:
        return value


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
records = []
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    searchable = " ".join((obj.name, str(obj.get("aevrynd_layer", "")))).lower()
    if obj.type != "MESH" or not any(token in searchable for token in TOKENS):
        continue
    materials = []
    for material in obj.data.materials:
        if material is None:
            continue
        entry = {"name": material.name, "surfaceRenderMethod": material.surface_render_method}
        if material.use_nodes:
            shaders = []
            textures = []
            for node in material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeBsdfPrincipled":
                    shaders.append({
                        name: input_value(node.inputs[name])
                        for name in ("Base Color", "Roughness", "Specular IOR Level", "Coat Weight", "Transmission Weight", "Alpha")
                        if node.inputs.get(name)
                    })
                elif node.bl_idname == "ShaderNodeTexImage" and node.image:
                    textures.append({"image": node.image.name, "path": bpy.path.abspath(node.image.filepath)})
            entry.update({"principled": shaders, "textures": textures})
        materials.append(entry)
    records.append({
        "object": obj.name,
        "layer": obj.get("aevrynd_layer"),
        "visible": not obj.hide_render,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "materials": materials,
    })

report = {"model": str(MODEL), "objects": records, "objectCount": len(records)}
REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("AEVRYND_R467_EYE_STACK=" + json.dumps(report, sort_keys=True))
