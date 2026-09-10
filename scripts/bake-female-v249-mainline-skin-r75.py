import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-r75.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/textures/aevrynd-female-skin-normal-v75.png"
REPORT = ROOT / "assets-source/aevrynd-character/textures/aevrynd-female-skin-normal-v75.bake.json"
BODY = "AevryndFemaleBodyBaseV118"
WIDTH = 4096
HEIGHT = 2048


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
body = bpy.data.objects[BODY]
material = body.data.materials[0]
# The source mesh carries a legacy empty second slot. Cycles reports it as a
# missing bake target even though the skin uses slot zero, so remove empty slots
# in this temporary bake scene before selecting the target image.
for slot_index in range(len(body.data.materials) - 1, -1, -1):
    if body.data.materials[slot_index] is None:
        body.data.materials.pop(index=slot_index)
image = bpy.data.images.get("aevrynd-female-skin-normal-v75")
if image is not None:
    bpy.data.images.remove(image)
image = bpy.data.images.new(
    "aevrynd-female-skin-normal-v75",
    width=WIDTH,
    height=HEIGHT,
    alpha=False,
    float_buffer=False,
)
image.colorspace_settings.name = "Non-Color"
image.file_format = "PNG"
image.filepath_raw = str(OUTPUT)
target = material.node_tree.nodes.new("ShaderNodeTexImage")
target.name = "Aevrynd Skin Normal Bake Target v75"
target.image = image
for node in material.node_tree.nodes:
    node.select = False
target.select = True
material.node_tree.nodes.active = target
for obj in bpy.context.selected_objects:
    obj.select_set(False)
body.select_set(True)
bpy.context.view_layer.objects.active = body
scene.render.bake.margin = 20
scene.render.bake.use_clear = True
bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
image.save()
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "width": WIDTH,
    "height": HEIGHT,
    "color_space": "Non-Color",
    "normal_space": "TANGENT",
    "margin_px": 20,
    "contains": ["owned tangent normal atlas v219", "procedural fine-pore microrelief r75"],
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_SKIN_R75_BAKE=" + json.dumps(report, sort_keys=True))
