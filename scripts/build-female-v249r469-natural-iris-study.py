import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-balanced-brunette-r468-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-iris-r469-study.blend"
REPORT = ASSETS / "female-v249-mainline-natural-iris-r469.build-report.json"
TEXTURE = ASSETS / "textures/aevrynd-iris-hazel-v5.png"
SWEEP_DIR = ROOT.parent / "Temp/female-realism/v249r469-natural-iris-sweep"
REVIEW_DIR = ASSETS / "reviews/v249r469-natural-iris"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, output_dir, name, location, target, lens, size):
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(output_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
SWEEP_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera

source_material = bpy.data.materials["Aevrynd_Eye_Iris_v249r174"]
material = source_material.copy()
material.name = "Aevrynd_Eye_Iris_NaturalHazel_R469"
material["aevrynd_revision"] = "v249r469"
material["aevrynd_layer"] = "eye.iris.stroma_owned_texture"
material["aevrynd_change"] = "lower-frequency owned iris stroma with embedded pupil and limbal falloff"
for obj_name in ("Eye_L_Iris", "Eye_R_Iris"):
    obj = bpy.data.objects[obj_name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_revision"] = "v249r469"

image = bpy.data.images.load(str(TEXTURE), check_existing=True)
image.name = "Aevrynd Iris Hazel Natural R469"
image.pack()
texture_node = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeTexImage")
texture_node.image = image
tone = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeHueSaturation")
tone.inputs["Hue"].default_value = 0.5
tone.inputs["Saturation"].default_value = 0.78

eye_view = ((0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
for label, value in (("a-value-125", 1.25), ("b-value-150", 1.50), ("c-value-175", 1.75)):
    tone.inputs["Value"].default_value = value
    render(scene, camera, SWEEP_DIR, label, *eye_view)

tone.inputs["Value"].default_value = 1.50
render(scene, camera, REVIEW_DIR, "01-eye-close-f01", *eye_view)
render(scene, camera, REVIEW_DIR, "02-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000))
render(scene, camera, REVIEW_DIR, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))

scene["aevrynd_mainline_revision"] = "v249r469-natural-iris-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYE_VISUAL_AND_LAYER_CLEARANCE_REVIEW_REQUIRED"
scene["aevrynd_eye_change"] = "material-only iris texture/tone; eye geometry and all collision layers inherited from r468/r446"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
REPORT.write_text(json.dumps({
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "texture": str(TEXTURE),
    "material": material.name,
    "irisObjects": ["Eye_L_Iris", "Eye_R_Iris"],
    "tone": {"hue": 0.5, "saturation": 0.78, "value": 1.50},
    "geometryChange": False,
    "ownership": "Aevrynd-owned deterministic procedural texture",
    "status": "NATURAL_IRIS_TEXTURE_PASS_CORNEA_DITHER_ARTIFACT_REMAINS",
}, indent=2), encoding="utf-8")
print(f"AEVRYND_R469_OUTPUT={OUTPUT}")
