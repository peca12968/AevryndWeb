import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-lashes-r74.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-skin-r75-sweep"
BODY = "AevryndFemaleBodyBaseV118"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def make_variant(original, name, values):
    material = original.copy()
    material.name = f"Aevrynd_Skin_r75_{name}"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Specular IOR Level"].default_value = values["specular"]
    shader.inputs["Subsurface Weight"].default_value = values["subsurface"]
    shader.inputs["Coat Weight"].default_value = values["coat"]
    if not values.get("micro"):
        return material

    existing_normal = shader.inputs["Normal"].links[0].from_socket if shader.inputs["Normal"].is_linked else None
    for link in list(shader.inputs["Normal"].links):
        links.remove(link)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = f"Aevrynd Skin Coordinates r75 {name}"
    primary = nodes.new("ShaderNodeTexNoise")
    primary.name = f"Aevrynd Primary Pores r75 {name}"
    primary.noise_dimensions = "3D"
    primary.inputs["Scale"].default_value = values["scale"]
    primary.inputs["Detail"].default_value = 3.8
    primary.inputs["Roughness"].default_value = 0.68
    primary.inputs["Lacunarity"].default_value = 2.2
    primary.inputs["Distortion"].default_value = 0.08
    bump = nodes.new("ShaderNodeBump")
    bump.name = f"Aevrynd Microrelief r75 {name}"
    bump.inputs["Strength"].default_value = values["strength"]
    bump.inputs["Distance"].default_value = values["distance"]
    links.new(texcoord.outputs["Generated"], primary.inputs["Vector"])
    links.new(primary.outputs["Fac"], bump.inputs["Height"])
    if existing_normal is not None:
        links.new(existing_normal, bump.inputs["Normal"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


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
original = body.data.materials[0]
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True

variants = {
    "a-control": {"specular": 0.16, "subsurface": 0.055, "coat": 0.018, "micro": False},
    "b-balanced": {"specular": 0.28, "subsurface": 0.035, "coat": 0.010, "micro": True, "scale": 1250.0, "strength": 0.080, "distance": 0.000020},
    "c-fine": {"specular": 0.32, "subsurface": 0.030, "coat": 0.008, "micro": True, "scale": 1850.0, "strength": 0.115, "distance": 0.000018},
    "d-crisp": {"specular": 0.38, "subsurface": 0.025, "coat": 0.006, "micro": True, "scale": 2450.0, "strength": 0.155, "distance": 0.000016},
}
for name, values in variants.items():
    body.data.materials[0] = make_variant(original, name, values)
    render(camera, f"{name}-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108)
    render(camera, f"{name}-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    render(camera, f"{name}-skin-close", (0.24, -0.42, 1.60), (0.028, -0.085, 1.59), 118)

body.data.materials[0] = original
(OUT / "report.json").write_text(json.dumps(variants, indent=2), encoding="utf-8")
print("AEVRYND_V249_SKIN_R75_SWEEP=" + json.dumps(variants, sort_keys=True))
