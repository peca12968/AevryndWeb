import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cloth-r35.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-detail-r39.blend"


def principled(material_name):
    material = bpy.data.materials[material_name]
    node = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    return material, node


def set_alpha(material, node, value):
    node.inputs["Alpha"].default_value = value
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
changes = {}
for material_name, alpha in (
    ("Aevrynd_Brow_Hair_v39_Dark", 0.78),
    ("Aevrynd_Brow_Hair_v39_Warm", 0.72),
):
    material, node = principled(material_name)
    set_alpha(material, node, alpha)
    node.inputs["Roughness"].default_value = 0.58
    changes[material_name] = {"alpha": alpha, "roughness": 0.58}

lash_material, lash = principled("Aevrynd_Lash_Hair_v51")
lash.inputs["Roughness"].default_value = 0.43
changes[lash_material.name] = {"alpha": lash.inputs["Alpha"].default_value, "roughness": 0.43}

fold_material, fold = principled("Aevrynd_EyelidFold")
fold.inputs["Base Color"].default_value = (0.105, 0.037, 0.026, 1.0)
fold.inputs["Roughness"].default_value = 0.68
set_alpha(fold_material, fold, 0.24)
changes[fold_material.name] = {"alpha": 0.24, "roughness": 0.68, "base_color": [0.105, 0.037, 0.026, 1.0]}

for name in ("Eye_L_UpperFold", "Eye_R_UpperFold"):
    obj = bpy.data.objects[name]
    obj.hide_render = False
    obj["aevrynd_runtime_exclude"] = False
    obj["aevrynd_eye_detail_revision"] = "v249-mainline-eye-detail-r39"

scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "eye-detail-r39"
scene["aevrynd_release_state"] = "EYE_DETAIL_R39_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"

payload = {"source": str(SOURCE), "output": str(OUTPUT), "changes": changes}
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_EYE_DETAIL_R39=" + json.dumps(payload, sort_keys=True))
