import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-lashes-r74.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-r75.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-skin-r75"
BODY = "AevryndFemaleBodyBaseV118"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def build_skin(body):
    source = body.data.materials[0]
    material = source.copy()
    material.name = "Aevrynd_Skin_Microrelief_v249R75"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Specular IOR Level"].default_value = 0.32
    shader.inputs["Subsurface Weight"].default_value = 0.030
    shader.inputs["Coat Weight"].default_value = 0.008
    existing_normal = shader.inputs["Normal"].links[0].from_socket if shader.inputs["Normal"].is_linked else None
    for link in list(shader.inputs["Normal"].links):
        links.remove(link)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "Aevrynd Skin Coordinates v249R75"
    pore = nodes.new("ShaderNodeTexNoise")
    pore.name = "Aevrynd Fine Pores v249R75"
    pore.noise_dimensions = "3D"
    pore.inputs["Scale"].default_value = 1850.0
    pore.inputs["Detail"].default_value = 3.8
    pore.inputs["Roughness"].default_value = 0.68
    pore.inputs["Lacunarity"].default_value = 2.2
    pore.inputs["Distortion"].default_value = 0.08
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Aevrynd Skin Microrelief v249R75"
    bump.inputs["Strength"].default_value = 0.115
    bump.inputs["Distance"].default_value = 0.000018
    links.new(texcoord.outputs["Generated"], pore.inputs["Vector"])
    links.new(pore.outputs["Fac"], bump.inputs["Height"])
    if existing_normal is not None:
        links.new(existing_normal, bump.inputs["Normal"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    material["aevrynd_skin_revision"] = "v249-mainline-skin-r75"
    material["aevrynd_skin_method"] = "owned atlases plus bakeable 1850-scale microrelief"
    body.data.materials[0] = material
    body["aevrynd_skin_revision"] = "v249-mainline-skin-r75"
    body["aevrynd_skin_layers"] = [
        "owned base-color atlas v248",
        "owned roughness atlas v216",
        "owned tangent normal atlas v219",
        "procedural fine-pore microrelief r75",
    ]
    return {
        "material": material.name,
        "specular_ior_level": 0.32,
        "subsurface_weight": 0.030,
        "coat_weight": 0.008,
        "pore_scale": 1850.0,
        "bump_strength": 0.115,
        "bump_distance_mm": 0.018,
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
report = build_skin(body)
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "skin-r75"
scene["aevrynd_release_state"] = "R75_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
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
print("AEVRYND_V249_SKIN_R75=" + json.dumps(report, sort_keys=True))
