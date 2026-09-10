import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-skin-r173.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-material-r174.blend"
IRIS_TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-iris-hazel-v61.png"
OUT = ROOT.parent / "Temp/female-realism/v249r174-natural-eye-material"
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def assign_copy(source_name, target_name, object_names):
    material = bpy.data.materials[source_name].copy()
    material.name = target_name
    for object_name in object_names:
        obj = bpy.data.objects[object_name]
        for index, slot in enumerate(obj.material_slots):
            if slot.material and slot.material.name == source_name:
                obj.material_slots[index].material = material
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

iris = assign_copy(
    "Aevrynd_Eye_Iris",
    "Aevrynd_Eye_Iris_v249r174",
    ["Eye_L_Iris", "Eye_R_Iris"],
)
iris_image = bpy.data.images.load(str(IRIS_TEXTURE), check_existing=True)
iris_image.colorspace_settings.name = "sRGB"
iris_node = iris.node_tree.nodes["Aevrynd Iris Texture"]
iris_node.image = iris_image
tone = iris.node_tree.nodes["Aevrynd Iris Tone Revision 5"]
tone.name = "Aevrynd Iris Tone Revision 61 v249r174"
tone.inputs["Saturation"].default_value = 0.86
tone.inputs["Value"].default_value = 1.14
iris_shader = next(node for node in iris.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
iris_shader.inputs["Roughness"].default_value = 0.42
iris_shader.inputs["Specular IOR Level"].default_value = 0.20
iris["aevrynd_eye_material_revision"] = "v249r174"
iris["aevrynd_iris_texture"] = "owned aevrynd-iris-hazel-v61.png"

hidden = []
for side in ("L", "R"):
    catchlight = bpy.data.objects[f"Eye_{side}_Catchlight"]
    catchlight.hide_render = True
    catchlight["aevrynd_eye_material_revision"] = "v249r174"
    catchlight["aevrynd_catchlight_method"] = "disabled; use physically generated corneal highlights"
    hidden.append(catchlight.name)

scene = bpy.context.scene
scene["aevrynd_face_revision"] = "v249r174"
scene["aevrynd_release_state"] = "NATURAL_EYE_MATERIAL_PENDING_VISUAL_REVIEW"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.frame_set(1)
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("04-face-profile", (0.70, -0.02, 1.61), (0.0, -0.015, 1.595), 92),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "geometry_changed": False,
    "iris_texture": str(IRIS_TEXTURE),
    "hidden_artificial_catchlights": hidden,
    "limbal_method": "owned iris texture supplies the edge variation; this mainline has no separate limbal mesh",
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-eye-material-r174.build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R174_NATURAL_EYE_MATERIAL=" + json.dumps(report, sort_keys=True))

