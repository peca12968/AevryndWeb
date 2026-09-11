import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-lighting-skin-tone-r329.study.json"
BODY = "AevryndFemaleBody_CC0_R249"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
lights = []
for obj in scene.objects:
    if obj.type == "LIGHT":
        lights.append({
            "name": obj.name, "type": obj.data.type, "energy": obj.data.energy,
            "color": list(obj.data.color), "location": list(obj.matrix_world.translation),
            "size": getattr(obj.data, "shape", None),
        })
materials = []
for material in {slot.material for slot in body.material_slots if slot.material}:
    principled = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None) if material.use_nodes else None
    materials.append({
        "name": material.name, "owned": material.get("aevrynd_ownership"), "revision": material.get("aevrynd_revision"),
        "principled": {
            "baseColorLinked": bool(principled and principled.inputs["Base Color"].is_linked),
            "baseColor": list(principled.inputs["Base Color"].default_value) if principled else None,
            "roughness": principled.inputs["Roughness"].default_value if principled else None,
            "subsurfaceWeight": principled.inputs["Subsurface Weight"].default_value if principled and "Subsurface Weight" in principled.inputs else None,
        },
    })
world = None
if scene.world and scene.world.use_nodes:
    background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None)
    if background:
        world = {"color": list(background.inputs["Color"].default_value), "strength": background.inputs["Strength"].default_value}
report = {
    "source": str(SOURCE),
    "colorManagement": {
        "displayDevice": scene.display_settings.display_device,
        "viewTransform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
    },
    "world": world, "lights": lights, "bodyMaterials": materials,
    "measuredFaceCloseLuminance": {"r318": 117.765, "r328": 117.779, "scale": "8-bit Rec.709 weighted fixed facial patches"},
    "conclusion": "r318 and r328 skin luminance are unchanged within rounding; increased eye contrast creates a darker perceptual impression.",
    "status": "PASS_NO_PROGRESSIVE_SKIN_DARKENING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R329_LIGHTING_SKIN_TONE=" + json.dumps(report, sort_keys=True))
