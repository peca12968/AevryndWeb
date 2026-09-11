from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-card-bake-r384.blend"
OUTPUT = ROOT.parent / "Temp/female-realism/v249r384-card-material-sweep"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUTPUT.mkdir(parents=True, exist_ok=True)

camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.72, 1.60)
camera.data.lens = 88
look_at(camera, (0.0, -0.025, 1.595))

material = bpy.data.materials["Aevrynd_RuntimeHairCards_R384"]
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")

variants = (
    ("a-r070-s006-a010", 0.70, 0.06, 0.10),
    ("b-r082-s002-a004", 0.82, 0.02, 0.04),
    ("c-r094-s000-a000", 0.94, 0.00, 0.00),
    ("d-r076-s003-a018", 0.76, 0.03, 0.18),
)
for label, roughness, specular, anisotropic in variants:
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = specular
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = anisotropic
    scene.render.filepath = str(OUTPUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)

# Isolate geometry/alpha quality without any surface specular response.
nodes = material.node_tree.nodes
links = material.node_tree.links
texture = next(node for node in nodes if node.bl_idname == "ShaderNodeTexImage")
output = next(node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial")
for node in list(nodes):
    if node not in (texture, output):
        nodes.remove(node)
diffuse = nodes.new("ShaderNodeBsdfDiffuse")
transparent = nodes.new("ShaderNodeBsdfTransparent")
mix = nodes.new("ShaderNodeMixShader")
links.new(texture.outputs["Color"], diffuse.inputs["Color"])
links.new(texture.outputs["Alpha"], mix.inputs["Fac"])
links.new(transparent.outputs["BSDF"], mix.inputs[1])
links.new(diffuse.outputs["BSDF"], mix.inputs[2])
links.new(mix.outputs["Shader"], output.inputs["Surface"])
scene.render.filepath = str(OUTPUT / "e-diffuse-alpha-isolation.png")
bpy.ops.render.render(write_still=True)

scalp = bpy.data.objects["AevryndFemaleSemanticScalp_R383"]
cards = [obj for obj in bpy.context.scene.objects if obj.name.startswith("AevryndFemaleRuntimeCards_") and obj.name.endswith("_R384")]
scalp.hide_render = True
scene.render.filepath = str(OUTPUT / "f-cards-only.png")
bpy.ops.render.render(write_still=True)
scalp.hide_render = False
for obj in cards:
    obj.hide_render = True
scene.render.filepath = str(OUTPUT / "g-scalp-only.png")
bpy.ops.render.render(write_still=True)

underlayer = bpy.data.objects["AevryndFemaleScalpUnderlayer_R280"]
scalp.hide_render = True
underlayer.hide_render = False
scene.render.filepath = str(OUTPUT / "h-r280-underlayer-only.png")
bpy.ops.render.render(write_still=True)

print(f"AEVRYND_R384_MATERIAL_SWEEP={OUTPUT}")
