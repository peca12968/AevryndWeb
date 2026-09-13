import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-multiscale-skin-r426.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r426-multiscale-skin-sweep"
BODY = "AevryndFemaleBody_CC0_R249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R426", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R426", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R426", (0.00, -0.08, 2.28), 22.0, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def hide_large_hair():
    for obj in bpy.data.objects:
        name = obj.name.lower()
        if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
            continue
        materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
        material_names = " ".join(material.name.lower() for material in materials if material)
        if obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            obj.hide_render = True


def socket_by_name(node, name):
    return next(item for item in node.inputs if item.name == name)


def build_variant(source, label, pigment, rough_low, rough_high, pore_strength, micro_strength):
    material = source.copy()
    material.name = f"Aevrynd_Skin_Multiscale_{label}_R426"
    material["aevrynd_revision"] = "v249r426-study"
    material["aevrynd_skin_layers"] = "macro melanin, chromatic mottling, roughness breakup, primary pores, micro pores"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base_input = shader.inputs["Base Color"]
    base_link = base_input.links[0] if base_input.is_linked else None
    base_output = base_link.from_socket if base_link else None
    if base_link:
        links.remove(base_link)

    texcoord = next((node for node in nodes if node.type == "TEX_COORD"), None) or nodes.new("ShaderNodeTexCoord")
    pigment_noise = nodes.new("ShaderNodeTexNoise")
    pigment_noise.name = "Aevrynd chromatic micro-mottle R426"
    pigment_noise.inputs["Scale"].default_value = 92.0
    pigment_noise.inputs["Detail"].default_value = 4.5
    pigment_noise.inputs["Roughness"].default_value = 0.68
    pigment_ramp = nodes.new("ShaderNodeValToRGB")
    pigment_ramp.name = "Aevrynd balanced pigment response R426"
    pigment_ramp.color_ramp.elements[0].position = 0.22
    pigment_ramp.color_ramp.elements[0].color = (0.88, 0.94, 0.91, 1.0)
    pigment_ramp.color_ramp.elements[1].position = 0.78
    pigment_ramp.color_ramp.elements[1].color = (1.12, 1.055, 0.98, 1.0)
    pigment_mix = nodes.new("ShaderNodeMixRGB")
    pigment_mix.name = "Aevrynd pigment strength R426"
    pigment_mix.blend_type = "MULTIPLY"
    pigment_mix.inputs[0].default_value = pigment
    if base_output:
        links.new(base_output, pigment_mix.inputs[1])
    else:
        pigment_mix.inputs[1].default_value = base_input.default_value
    links.new(texcoord.outputs["Object"], pigment_noise.inputs["Vector"])
    links.new(pigment_noise.outputs["Fac"], pigment_ramp.inputs["Fac"])
    links.new(pigment_ramp.outputs["Color"], pigment_mix.inputs[2])
    links.new(pigment_mix.outputs["Color"], base_input)

    rough_noise = nodes.new("ShaderNodeTexNoise")
    rough_noise.name = "Aevrynd sebum-dry roughness breakup R426"
    rough_noise.inputs["Scale"].default_value = 48.0
    rough_noise.inputs["Detail"].default_value = 5.0
    rough_noise.inputs["Roughness"].default_value = 0.72
    rough_ramp = nodes.new("ShaderNodeValToRGB")
    rough_ramp.color_ramp.elements[0].position = 0.18
    rough_ramp.color_ramp.elements[0].color = (rough_low, rough_low, rough_low, 1.0)
    rough_ramp.color_ramp.elements[1].position = 0.82
    rough_ramp.color_ramp.elements[1].color = (rough_high, rough_high, rough_high, 1.0)
    links.new(texcoord.outputs["Object"], rough_noise.inputs["Vector"])
    links.new(rough_noise.outputs["Fac"], rough_ramp.inputs["Fac"])
    links.new(rough_ramp.outputs["Color"], shader.inputs["Roughness"])

    existing_bump = next((node for node in nodes if node.type == "BUMP"), None)
    if existing_bump:
        existing_bump.inputs["Strength"].default_value = pore_strength
        existing_bump.inputs["Distance"].default_value = 0.000055
        normal_link = shader.inputs["Normal"].links[0] if shader.inputs["Normal"].is_linked else None
        if normal_link:
            links.remove(normal_link)
    micro_noise = nodes.new("ShaderNodeTexNoise")
    micro_noise.name = "Aevrynd secondary micro-pore field R426"
    micro_noise.inputs["Scale"].default_value = 2850.0
    micro_noise.inputs["Detail"].default_value = 2.0
    micro_noise.inputs["Roughness"].default_value = 0.58
    micro_bump = nodes.new("ShaderNodeBump")
    micro_bump.name = "Aevrynd secondary micro-pore normal R426"
    micro_bump.inputs["Strength"].default_value = micro_strength
    micro_bump.inputs["Distance"].default_value = 0.000018
    links.new(texcoord.outputs["Object"], micro_noise.inputs["Vector"])
    links.new(micro_noise.outputs["Fac"], micro_bump.inputs["Height"])
    if existing_bump:
        links.new(existing_bump.outputs["Normal"], micro_bump.inputs["Normal"])
    links.new(micro_bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Subsurface Weight"].default_value = 0.040
    shader.inputs["Subsurface Scale"].default_value = 0.0042
    shader.inputs["Coat Weight"].default_value = 0.010
    shader.inputs["Coat Roughness"].default_value = 0.46
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
hide_large_hair()
neutral_lights(scene)
body = bpy.data.objects[BODY]
source_material = body.data.materials[0]
body.data = body.data.copy()

variants = (
    ("a-restrained", 0.35, 0.455, 0.565, 0.095, 0.030),
    ("b-balanced", 0.55, 0.430, 0.585, 0.125, 0.045),
    ("c-strong", 0.75, 0.405, 0.610, 0.155, 0.060),
)
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("face-close", (0.0, -0.52, 1.605), (0.0, -0.035, 1.606), 105, (1200, 1000)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
)
metrics = {}
for label, pigment, rough_low, rough_high, pore_strength, micro_strength in variants:
    material = build_variant(source_material, label, pigment, rough_low, rough_high, pore_strength, micro_strength)
    body.data.materials.clear()
    body.data.materials.append(material)
    metrics[label] = {
        "pigmentMix": pigment, "roughnessRange": [rough_low, rough_high],
        "primaryPoreStrength": pore_strength, "microPoreStrength": micro_strength,
        "subsurfaceWeight": 0.040, "subsurfaceScaleM": 0.0042,
    }
    for view_name, location, target, lens, size in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "method": "Preserve mean inherited melanin while adding balanced chromatic mottling, spatial roughness breakup and chained primary/micro pore normals.",
    "geometryChanged": False, "eyeGeometryChanged": False,
    "status": "VISUAL_AND_LUMINANCE_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R426_MULTISCALE_SKIN_SWEEP=" + json.dumps(report, sort_keys=True))
