import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-skin-r173.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r173-layered-skin"
OUT.mkdir(parents=True, exist_ok=True)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smooth_noise(x, y, z):
    return (
        0.46 * math.sin(x * 247.0 + z * 173.0 + 0.4)
        + 0.31 * math.sin(x * 109.0 - y * 191.0 + z * 71.0 + 1.7)
        + 0.23 * math.sin(x * 389.0 + y * 131.0 - z * 223.0 + 3.2)
    )


def replace_attribute(mesh, name, data_type):
    old = mesh.color_attributes.get(name) if data_type == "FLOAT_COLOR" else mesh.attributes.get(name)
    if old:
        if data_type == "FLOAT_COLOR":
            mesh.color_attributes.remove(old)
        else:
            mesh.attributes.remove(old)
    if data_type == "FLOAT_COLOR":
        return mesh.color_attributes.new(name=name, type=data_type, domain="POINT")
    return mesh.attributes.new(name=name, type=data_type, domain="POINT")


def build_skin_fields(body):
    complexion = replace_attribute(body.data, "AevryndComplexionV249R173", "FLOAT_COLOR")
    roughness = replace_attribute(body.data, "AevryndRoughnessV249R173", "FLOAT")
    maxima = {"cheek": 0.0, "nose": 0.0, "under_eye": 0.0, "temple": 0.0, "freckle": 0.0}
    for index, vertex in enumerate(body.data.vertices):
        x, y, z = vertex.co
        front = gaussian(y, -0.129, 0.035)
        face = front * gaussian(z, 1.574, 0.115)
        cheek = max(gaussian(x, -0.050, 0.026), gaussian(x, 0.050, 0.026)) * front * gaussian(z, 1.572, 0.032)
        nose = gaussian(x, 0.0, 0.021) * gaussian(y, -0.149, 0.018) * gaussian(z, 1.574, 0.043)
        under_eye = max(gaussian(x, -0.036, 0.021), gaussian(x, 0.036, 0.021)) * front * gaussian(z, 1.607, 0.012)
        temple = max(gaussian(x, -0.071, 0.020), gaussian(x, 0.071, 0.020)) * front * gaussian(z, 1.623, 0.040)
        chin = gaussian(x, 0.0, 0.035) * front * gaussian(z, 1.487, 0.027)
        ear = max(gaussian(x, -0.094, 0.018), gaussian(x, 0.094, 0.018)) * gaussian(z, 1.566, 0.052)
        lip_guard = gaussian(x, 0.0, 0.052) * gaussian(y, -0.144, 0.024) * gaussian(z, 1.525, 0.024)
        noise = smooth_noise(x, y, z) * face * (1.0 - 0.92 * lip_guard)
        freckle = max(0.0, math.sin(x * 701.0 + z * 443.0 + math.sin(y * 317.0) * 2.0) - 0.84) / 0.16
        freckle *= (cheek * 0.72 + nose * 0.45)

        red = 1.0 + 0.075 * cheek + 0.042 * nose + 0.032 * ear + 0.018 * chin - 0.015 * under_eye - 0.012 * temple
        green = 1.0 - 0.035 * cheek - 0.024 * nose - 0.018 * ear - 0.010 * chin - 0.010 * under_eye
        blue = 1.0 - 0.060 * cheek - 0.045 * nose - 0.032 * ear + 0.040 * under_eye - 0.012 * chin
        red += noise * 0.012 - freckle * 0.050
        green += noise * 0.006 - freckle * 0.060
        blue -= noise * 0.005 + freckle * 0.058
        complexion.data[index].color = (red, green, blue, 1.0)

        t_zone = gaussian(x, 0.0, 0.026) * front * gaussian(z, 1.585, 0.090)
        cheek_dry = cheek * 0.75 + temple * 0.35
        roughness.data[index].value = max(0.82, min(1.18, 1.0 - 0.13 * t_zone + 0.11 * cheek_dry + noise * 0.035))
        for name, value in (("cheek", cheek), ("nose", nose), ("under_eye", under_eye), ("temple", temple), ("freckle", freckle)):
            maxima[name] = max(maxima[name], value)
    return complexion, roughness, maxima


def build_material(body, complexion, roughness):
    source = body.active_material
    material = source.copy()
    material.name = "Aevrynd_Skin_Layered_v249r173"
    body.data.materials.clear()
    body.data.materials.append(material)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = nodes.get("Aevrynd Skin Base Atlas v248")
    rough_map = nodes.get("Aevrynd Skin Roughness Atlas v216")
    normal_map = nodes.get("Aevrynd Skin Tangent MicroNormal v190")

    complexion_node = nodes.new("ShaderNodeVertexColor")
    complexion_node.name = "Aevrynd Complexion Field v249r173"
    complexion_node.layer_name = complexion.name
    complexion_mix = nodes.new("ShaderNodeMixRGB")
    complexion_mix.name = "Aevrynd Complexion Multiply v249r173"
    complexion_mix.blend_type = "MULTIPLY"
    complexion_mix.inputs[0].default_value = 1.0
    links.new(base.outputs["Color"], complexion_mix.inputs[1])
    links.new(complexion_node.outputs["Color"], complexion_mix.inputs[2])
    for link in list(shader.inputs["Base Color"].links):
        links.remove(link)
    links.new(complexion_mix.outputs["Color"], shader.inputs["Base Color"])

    roughness_node = nodes.new("ShaderNodeAttribute")
    roughness_node.name = "Aevrynd Roughness Field v249r173"
    roughness_node.attribute_name = roughness.name
    roughness_mix = nodes.new("ShaderNodeMixRGB")
    roughness_mix.name = "Aevrynd Roughness Multiply v249r173"
    roughness_mix.blend_type = "MULTIPLY"
    roughness_mix.inputs[0].default_value = 1.0
    links.new(rough_map.outputs["Color"], roughness_mix.inputs[1])
    links.new(roughness_node.outputs["Fac"], roughness_mix.inputs[2])
    for link in list(shader.inputs["Roughness"].links):
        links.remove(link)
    links.new(roughness_mix.outputs["Color"], shader.inputs["Roughness"])

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "Aevrynd Pore Coordinates v249r173"
    pore = nodes.new("ShaderNodeTexNoise")
    pore.name = "Aevrynd Primary Pores v249r173"
    pore.noise_dimensions = "3D"
    pore.inputs["Scale"].default_value = 410.0
    pore.inputs["Detail"].default_value = 2.6
    pore.inputs["Roughness"].default_value = 0.58
    pore.inputs["Lacunarity"].default_value = 2.15
    pore.inputs["Distortion"].default_value = 0.12
    links.new(texcoord.outputs["Generated"], pore.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Aevrynd Dual Scale Skin Bump v249r173"
    bump.inputs["Strength"].default_value = 0.115
    bump.inputs["Distance"].default_value = 0.000045
    links.new(pore.outputs["Fac"], bump.inputs["Height"])
    if normal_map:
        links.new(normal_map.outputs["Normal"], bump.inputs["Normal"])
    for link in list(shader.inputs["Normal"].links):
        links.remove(link)
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Subsurface Weight"].default_value = 0.038
    shader.inputs["Subsurface Scale"].default_value = 0.0022
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.30, 0.14)
    shader.inputs["Specular IOR Level"].default_value = 0.145
    shader.inputs["Coat Weight"].default_value = 0.008
    shader.inputs["Coat Roughness"].default_value = 0.30
    material["aevrynd_skin_revision"] = "v249r173"
    material["aevrynd_skin_method"] = "owned complexion and roughness vertex fields plus dual-scale procedural pores"
    return material


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
complexion, roughness, maxima = build_skin_fields(body)
material = build_material(body, complexion, roughness)
body["aevrynd_skin_revision"] = "v249r173"
body["aevrynd_skin_layers"] = [complexion.name, roughness.name, "procedural_pores"]

scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
    ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-face-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "material": material.name,
    "geometry_changed": False, "fields": [complexion.name, roughness.name], "zone_maxima": maxima,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(ROOT / "assets-source/aevrynd-character/female-v249-mainline-layered-skin-r173.build-report.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
scene["aevrynd_release_state"] = "LAYERED_SKIN_PENDING_VISUAL_REVIEW"
scene["aevrynd_skin_revision"] = "v249r173"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_LAYERED_SKIN_V249R173=" + json.dumps(report, sort_keys=True))

