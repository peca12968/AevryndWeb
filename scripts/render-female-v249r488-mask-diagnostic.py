from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-lower-lip-r485.blend"
OUT = ASSETS / "reviews/v249r488-lip-normal-sweep"
BODY = "AevryndFemaleBodyBaseV118"


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
material = body.active_material.copy()
material.name = "Aevrynd_R488_Mask_Diagnostic"
body.data.materials.clear()
body.data.materials.append(material)
nodes = material.node_tree.nodes
nodes.clear()
output = nodes.new("ShaderNodeOutputMaterial")
emission = nodes.new("ShaderNodeEmission")
material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

upper = nodes.new("ShaderNodeAttribute")
upper.attribute_name = "AevryndVermilionPlaneR484_c-defined-280"
lower = nodes.new("ShaderNodeAttribute")
lower.attribute_name = "AevryndLowerVermilionR475"
upper_normalize = nodes.new("ShaderNodeMath")
upper_normalize.operation = "MULTIPLY"
upper_normalize.inputs[1].default_value = 1.0 / 0.34
upper_normalize.use_clamp = True
lower_normalize = nodes.new("ShaderNodeMath")
lower_normalize.operation = "MULTIPLY"
lower_normalize.inputs[1].default_value = 10.0
lower_normalize.use_clamp = True
maximum = nodes.new("ShaderNodeMath")
maximum.operation = "MAXIMUM"
maximum.use_clamp = True
links = material.node_tree.links
links.new(upper.outputs["Color"], upper_normalize.inputs[0])
links.new(lower.outputs["Color"], lower_normalize.inputs[0])
links.new(upper_normalize.outputs[0], maximum.inputs[0])
links.new(lower_normalize.outputs[0], maximum.inputs[1])

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.resolution_x = 1400
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0, -0.405, 1.528)
camera.data.lens = 135
look(camera, (0, -0.115, 1.528))
OUT.mkdir(parents=True, exist_ok=True)

for name, socket in (
    ("mask-upper-raw", upper.outputs["Color"]),
    ("mask-lower-raw", lower.outputs["Color"]),
    ("mask-normalized-max", maximum.outputs[0]),
):
    for link in list(emission.inputs["Color"].links):
        links.remove(link)
    links.new(socket, emission.inputs["Color"])
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("AEVRYND_R488_MASK_DIAGNOSTIC=" + str(OUT))
