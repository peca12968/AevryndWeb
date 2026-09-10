import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-material-r174.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cornea-response-r175.build-report.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
material = bpy.data.materials["Aevrynd_Eye_Cornea"].copy()
material.name = "Aevrynd_Eye_Cornea_v249r175"
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
shader.inputs["Alpha"].default_value = 0.14
shader.inputs["IOR"].default_value = 1.376
shader.inputs["Roughness"].default_value = 0.024
shader.inputs["Coat Weight"].default_value = 0.28
shader.inputs["Coat Roughness"].default_value = 0.028
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_Cornea"]
    obj.data = obj.data.copy()
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = "face.eye.cornea"
    obj["aevrynd_revision"] = "v249r175"
material["aevrynd_eye_material_revision"] = "v249r175"
material["aevrynd_method"] = "physical corneal transmission and coat response; no fixed catchlight mesh"
scene = bpy.context.scene
scene["aevrynd_face_revision"] = "v249r175"
scene["aevrynd_candidate_status"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "geometryChanged": False,
    "alpha": 0.14, "ior": 1.376, "roughness": 0.024,
    "coatWeight": 0.28, "coatRoughness": 0.028,
    "fixedCatchlights": False, "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R175_CORNEA=" + json.dumps(report, sort_keys=True))
