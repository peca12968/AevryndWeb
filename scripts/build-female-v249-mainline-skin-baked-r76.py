import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-r75.blend"
NORMAL = ROOT / "assets-source/aevrynd-character/textures/aevrynd-female-skin-normal-v75.png"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-baked-r76.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-skin-baked-r76"
BODY = "AevryndFemaleBodyBaseV118"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def install_baked_normal(body):
    source = body.data.materials[0]
    material = source.copy()
    material.name = "Aevrynd_Skin_BakedMicrorelief_v249R76"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    for link in list(shader.inputs["Normal"].links):
        links.remove(link)
    for node in list(nodes):
        if node.name in {
            "Aevrynd Skin Coordinates v249R75",
            "Aevrynd Fine Pores v249R75",
            "Aevrynd Skin Microrelief v249R75",
        }:
            nodes.remove(node)
    image = bpy.data.images.load(str(NORMAL), check_existing=True)
    image.name = "aevrynd-female-skin-normal-v75"
    image.colorspace_settings.name = "Non-Color"
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Aevrynd Baked Skin Normal v75"
    texture.label = "Owned combined tangent normal: macro + pores"
    texture.image = image
    texture.interpolation = "Linear"
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "Aevrynd Baked Skin Normal Decode v249R76"
    normal_map.space = "TANGENT"
    normal_map.inputs["Strength"].default_value = 1.0
    links.new(texture.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    image.pack()
    material["aevrynd_skin_revision"] = "v249-mainline-skin-baked-r76"
    material["aevrynd_skin_method"] = "owned 4096x2048 combined tangent normal atlas"
    body.data.materials[0] = material
    body["aevrynd_skin_revision"] = "v249-mainline-skin-baked-r76"
    body["aevrynd_skin_layers"] = [
        "owned base-color atlas v248",
        "owned roughness atlas v216",
        "owned combined tangent normal atlas v75",
    ]
    return {
        "material": material.name,
        "normal_texture": str(NORMAL),
        "normal_resolution": [int(image.size[0]), int(image.size[1])],
        "normal_packed": bool(image.packed_file),
        "specular_ior_level": shader.inputs["Specular IOR Level"].default_value,
        "subsurface_weight": shader.inputs["Subsurface Weight"].default_value,
        "coat_weight": shader.inputs["Coat Weight"].default_value,
        "geometry_changed": False,
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
report = install_baked_normal(body)
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "skin-baked-r76"
scene["aevrynd_release_state"] = "R76_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for obj in hair_objects:
    obj.hide_render = True
render(camera, "01-face-front-face-only", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108)
render(camera, "02-face-three-quarter-face-only", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
render(camera, "03-skin-close-face-only", (0.24, -0.42, 1.60), (0.028, -0.085, 1.59), 118)
for obj in hair_objects:
    obj.hide_render = False
render(camera, "04-face-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
report.update({"source": str(SOURCE), "output": str(OUTPUT)})
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_SKIN_BAKED_R76=" + json.dumps(report, sort_keys=True))
