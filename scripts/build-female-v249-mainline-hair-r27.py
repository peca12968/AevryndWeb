import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r25.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r27.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r27"
OUT.mkdir(parents=True, exist_ok=True)
HAIR_OBJECTS = (
    "AevryndFemaleGuideBob_v249r25",
    "AevryndFemaleNapeFiberFill_v249r17",
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def build_hair_material():
    material = bpy.data.materials.get("AevryndFemaleHairMaterial_v249r27")
    if material is None:
        material = bpy.data.materials.new("AevryndFemaleHairMaterial_v249r27")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (360, 0)
    shader = nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.location = (30, 0)
    shader.parametrization = "MELANIN"
    shader.inputs["Melanin"].default_value = 0.72
    shader.inputs["Melanin Redness"].default_value = 0.34
    shader.inputs["Tint"].default_value = (0.115, 0.028, 0.012, 1.0)
    shader.inputs["Roughness"].default_value = 0.31
    shader.inputs["Radial Roughness"].default_value = 0.43
    shader.inputs["Coat"].default_value = 0.12
    shader.inputs["IOR"].default_value = 1.55
    shader.inputs["Random Color"].default_value = 0.18
    shader.inputs["Random Roughness"].default_value = 0.12
    if shader.inputs.get("Weight"):
        shader.inputs["Weight"].default_value = 1.0

    hair_info = nodes.new("ShaderNodeHairInfo")
    hair_info.location = (-260, -120)
    material.node_tree.links.new(hair_info.outputs["Random"], shader.inputs["Random"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.028, 0.006, 0.002, 1.0)
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
material = build_hair_material()
assignments = []
for name in HAIR_OBJECTS:
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_hair_shader"] = "principled-hair-melanin-v249r27"
    assignments.append(name)

scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r27"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86, (900, 900)),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (900, 900)),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78, (900, 900)),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
)
for name, location, target, lens, resolution in views:
    scene.frame_set(1)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "material": material.name,
    "objects": assignments,
    "shader": {
        "type": "Principled Hair BSDF",
        "parametrization": "MELANIN",
        "melanin": 0.72,
        "melanin_redness": 0.34,
        "roughness": 0.31,
        "radial_roughness": 0.43,
        "coat": 0.12,
        "random_color": 0.18,
        "random_roughness": 0.12,
    },
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R27=" + json.dumps(report, sort_keys=True))
