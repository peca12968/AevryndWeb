from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-soft-rear-fan-cards-r467.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-balanced-brunette-r468-study.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r468-balanced-brunette-sweep"
FINAL_RENDER_DIR = ASSETS / "reviews/v249r468-runtime-balanced-brunette"
MATERIAL = "Aevrynd_RuntimeHairCards_R467"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_value_control(material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    texture_link = shader.inputs["Base Color"].links[0]
    texture = texture_link.from_node
    links.remove(texture_link)
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.name = "Aevrynd Hair Value Balance R468"
    multiply.label = "Runtime brunette value control"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    links.new(texture.outputs["Color"], multiply.inputs[1])
    links.new(multiply.outputs["Color"], shader.inputs["Base Color"])
    return multiply


def set_multiplier(node, value):
    node.inputs[2].default_value = (value, value * 0.975, value * 0.94, 1.0)


def render(scene, camera, output_dir, label, location=(0.0, -0.72, 1.60), target=(0.0, -0.025, 1.595), lens=88):
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(output_dir / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
FINAL_RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera

material = bpy.data.materials[MATERIAL]
material.name = "Aevrynd_RuntimeHairCards_R468_BalancedBrunette"
material["aevrynd_revision"] = "v249r468"
material["aevrynd_change"] = "material-only brunette value rebalance; geometry, weights and collision envelope inherited from r467"
control = add_value_control(material)

for label, multiplier in (("a-150pct", 1.50), ("b-175pct", 1.75), ("c-200pct", 2.00)):
    set_multiplier(control, multiplier)
    render(scene, camera, RENDER_DIR, label)

# The 2x setting restores readable brown midtones while retaining dark roots.
set_multiplier(control, 2.00)
render(scene, camera, FINAL_RENDER_DIR, "01-front-f01")
render(scene, camera, FINAL_RENDER_DIR, "02-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84)
render(scene, camera, FINAL_RENDER_DIR, "03-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82)
scene["aevrynd_mainline_revision"] = "v249r468-runtime-balanced-brunette-study"
scene["aevrynd_release_state"] = "MATERIAL_VALUE_STUDY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_value_multiplier"] = 2.00
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print(f"AEVRYND_R468_OUTPUT={OUTPUT}")
