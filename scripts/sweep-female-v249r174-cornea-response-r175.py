import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-material-r174.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r175-cornea-response-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cornea-response-r175.sweep-report.json"
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
camera.location = (0.0, -0.47, 1.610)
camera.data.lens = 112
look_at(camera, (0.0, -0.065, 1.608))

material = bpy.data.materials["Aevrynd_Eye_Cornea"]
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
variants = (
    ("01-alpha08-coat15", 0.08, 0.15, 0.025),
    ("02-alpha16-coat35", 0.16, 0.35, 0.035),
    ("03-alpha28-coat55", 0.28, 0.55, 0.045),
)
results = []
for name, alpha, coat, roughness in variants:
    shader.inputs["Alpha"].default_value = alpha
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = roughness
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    results.append({"name": name, "alpha": alpha, "coatWeight": coat, "coatRoughness": roughness})

report = {"source": str(SOURCE), "variants": results, "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R175_CORNEA_SWEEP=" + json.dumps(report, sort_keys=True))
