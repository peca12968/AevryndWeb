"""Build a restrained regional skin-response sweep on the collision-qualified r1081 model."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-graded-hairline-r1081-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-regional-skin-r1082-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1082-regional-skin-sweep.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1082-regional-skin"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
VARIANTS = (
    ("a-control", 0.00, 0.00, 0.045, 0.000, 34.0, 1.00, 0.000),
    ("b-restrained", 0.45, 0.55, 0.052, 0.018, 72.0, 0.70, 0.006),
    ("c-balanced", 0.65, 0.75, 0.058, 0.026, 84.0, 0.58, 0.009),
    ("d-strong", 0.90, 1.00, 0.070, 0.038, 96.0, 0.42, 0.013),
)
SELECTED = "c-balanced"


def clamp(value):
    return max(0.0, min(1.0, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value):
    return math.exp(-0.5 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create_region_attributes(body, color_strength, rough_strength):
    color = body.data.attributes.get("aevrynd_skin_color_r1082") or body.data.attributes.new("aevrynd_skin_color_r1082", "FLOAT_COLOR", "POINT")
    rough = body.data.attributes.get("aevrynd_skin_roughness_r1082") or body.data.attributes.new("aevrynd_skin_roughness_r1082", "FLOAT", "POINT")
    samples = {"colorMin": [99.0, 99.0, 99.0], "colorMax": [-99.0, -99.0, -99.0], "roughnessMin": 99.0, "roughnessMax": -99.0, "affectedVertices": 0}
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        head = smoothstep((z - 1.245) / 0.11) * smoothstep((1.710 - z) / 0.10)
        front = smoothstep((-y - 0.005) / 0.105)
        face = head * front
        cheek_l = gaussian(((x + 0.055) / 0.036) ** 2 + ((y + 0.104) / 0.055) ** 2 + ((z - 1.445) / 0.060) ** 2)
        cheek_r = gaussian(((x - 0.055) / 0.036) ** 2 + ((y + 0.104) / 0.055) ** 2 + ((z - 1.445) / 0.060) ** 2)
        cheeks = max(cheek_l, cheek_r) * face
        nose = gaussian((x / 0.026) ** 2 + ((y + 0.132) / 0.045) ** 2 + ((z - 1.452) / 0.092) ** 2) * face
        forehead = gaussian((x / 0.052) ** 2 + ((y + 0.085) / 0.065) ** 2 + ((z - 1.570) / 0.085) ** 2) * face
        chin = gaussian((x / 0.045) ** 2 + ((y + 0.105) / 0.050) ** 2 + ((z - 1.335) / 0.055) ** 2) * face
        temples = gaussian(((abs(x) - 0.078) / 0.030) ** 2 + ((y + 0.055) / 0.070) ** 2 + ((z - 1.535) / 0.085) ** 2) * face
        under_eye = max(
            gaussian(((x + 0.045) / 0.034) ** 2 + ((y + 0.115) / 0.045) ** 2 + ((z - 1.490) / 0.030) ** 2),
            gaussian(((x - 0.045) / 0.034) ** 2 + ((y + 0.115) / 0.045) ** 2 + ((z - 1.490) / 0.030) ** 2),
        ) * face
        warm = clamp(0.72 * cheeks + 0.34 * nose + 0.18 * chin)
        cool = clamp(0.34 * temples + 0.16 * under_eye)
        asymmetry = 0.5 + 0.5 * math.sin(x * 91.0 + z * 47.0)
        red = 1.0 + color_strength * face * (0.022 * warm - 0.008 * cool + 0.003 * (asymmetry - 0.5))
        green = 1.0 + color_strength * face * (-0.010 * warm + 0.004 * cool - 0.001 * (asymmetry - 0.5))
        blue = 1.0 + color_strength * face * (-0.014 * warm + 0.012 * cool)
        color.data[vertex.index].color = (red, green, blue, 1.0)
        t_zone = clamp(0.72 * nose + 0.48 * forehead + 0.28 * chin)
        delta = rough_strength * face * (-0.052 * t_zone + 0.046 * cheeks + 0.020 * temples + 0.012 * under_eye)
        rough.data[vertex.index].value = delta
        if face > 0.02:
            samples["affectedVertices"] += 1
        for index, value in enumerate((red, green, blue)):
            samples["colorMin"][index] = min(samples["colorMin"][index], value)
            samples["colorMax"][index] = max(samples["colorMax"][index], value)
        samples["roughnessMin"] = min(samples["roughnessMin"], delta)
        samples["roughnessMax"] = max(samples["roughnessMax"], delta)
    return samples


def tune_material(body, label, color_strength, rough_strength, pore_strength, micro_strength, fine_scale, macro_contrast, fine_contrast):
    source = body.data.materials[0]
    material = source.copy()
    material.name = f"Aevrynd_CC0_RegionalSkin_R1082_{label}"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    macro_noise = next(node for node in nodes if node.type == "TEX_NOISE" and abs(node.inputs["Scale"].default_value - 34.0) < 0.01)
    macro_ramp = next(node for node in nodes if node.type == "VALTORGB")
    macro_noise.inputs["Scale"].default_value = 34.0
    macro_noise.inputs["Detail"].default_value = 3.2
    macro_noise.inputs["Roughness"].default_value = 0.62
    macro_noise.inputs["Distortion"].default_value = 0.03
    original = [list(element.color) for element in macro_ramp.color_ramp.elements]
    midpoint = [(original[0][channel] + original[1][channel]) * 0.5 for channel in range(3)]
    for element, source_color in zip(macro_ramp.color_ramp.elements, original):
        element.color = tuple(midpoint[channel] + (source_color[channel] - midpoint[channel]) * macro_contrast for channel in range(3)) + (1.0,)
    coords = next(node for node in nodes if node.type == "TEX_COORD")
    base_input = shader.inputs["Base Color"]
    base_link = base_input.links[0] if base_input.is_linked else None
    base_output = base_link.from_socket if base_link else None
    if base_link:
        links.remove(base_link)
    color_attribute = nodes.new("ShaderNodeAttribute")
    color_attribute.name = "Aevrynd Regional Complexion R1082"
    color_attribute.attribute_name = "aevrynd_skin_color_r1082"
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.name = "Aevrynd Regional Complexion Multiply R1082"
    color_mix.blend_type = "MULTIPLY"
    color_mix.inputs[0].default_value = 1.0
    fine_noise = nodes.new("ShaderNodeTexNoise")
    fine_noise.name = "Aevrynd Fine Chromatic Mottle R1082"
    fine_noise.noise_dimensions = "3D"
    fine_noise.inputs["Scale"].default_value = fine_scale
    fine_noise.inputs["Detail"].default_value = 3.5
    fine_noise.inputs["Roughness"].default_value = 0.60
    fine_ramp = nodes.new("ShaderNodeValToRGB")
    fine_ramp.name = "Aevrynd Fine Mottle Balanced Ramp R1082"
    fine_ramp.color_ramp.elements[0].position = 0.18
    fine_ramp.color_ramp.elements[0].color = (1.0 - fine_contrast, 1.0 - fine_contrast * 0.55, 1.0, 1.0)
    fine_ramp.color_ramp.elements[1].position = 0.82
    fine_ramp.color_ramp.elements[1].color = (1.0 + fine_contrast, 1.0 + fine_contrast * 0.35, 1.0 - fine_contrast * 0.45, 1.0)
    fine_mix = nodes.new("ShaderNodeMixRGB")
    fine_mix.name = "Aevrynd Fine Mottle Multiply R1082"
    fine_mix.blend_type = "MULTIPLY"
    fine_mix.inputs[0].default_value = 1.0
    if base_output:
        links.new(base_output, fine_mix.inputs[1])
    else:
        fine_mix.inputs[1].default_value = base_input.default_value
    links.new(coords.outputs["Object"], fine_noise.inputs["Vector"])
    links.new(fine_noise.outputs["Fac"], fine_ramp.inputs["Fac"])
    links.new(fine_ramp.outputs["Color"], fine_mix.inputs[2])
    links.new(fine_mix.outputs[0], color_mix.inputs[1])
    links.new(color_attribute.outputs["Color"], color_mix.inputs[2])
    links.new(color_mix.outputs[0], base_input)

    rough_input = shader.inputs["Roughness"]
    rough_link = rough_input.links[0] if rough_input.is_linked else None
    rough_output = rough_link.from_socket if rough_link else None
    if rough_link:
        links.remove(rough_link)
    rough_attribute = nodes.new("ShaderNodeAttribute")
    rough_attribute.name = "Aevrynd TZone Cheek Roughness R1082"
    rough_attribute.attribute_name = "aevrynd_skin_roughness_r1082"
    rough_add = nodes.new("ShaderNodeMath")
    rough_add.name = "Aevrynd Regional Roughness Add R1082"
    rough_add.operation = "ADD"
    rough_add.use_clamp = True
    if rough_output:
        links.new(rough_output, rough_add.inputs[0])
    else:
        rough_add.inputs[0].default_value = rough_input.default_value
    links.new(rough_attribute.outputs["Fac"], rough_add.inputs[1])
    links.new(rough_add.outputs[0], rough_input)

    existing_bump = next(node for node in nodes if node.type == "BUMP")
    existing_bump.inputs["Strength"].default_value = pore_strength
    normal_link = shader.inputs["Normal"].links[0] if shader.inputs["Normal"].is_linked else None
    if normal_link:
        links.remove(normal_link)
    micro_noise = nodes.new("ShaderNodeTexNoise")
    micro_noise.name = "Aevrynd Secondary Micro Pore Field R1082"
    micro_noise.noise_dimensions = "3D"
    micro_noise.inputs["Scale"].default_value = 2350.0
    micro_noise.inputs["Detail"].default_value = 2.2
    micro_noise.inputs["Roughness"].default_value = 0.56
    micro_noise.inputs["Distortion"].default_value = 0.025
    micro_bump = nodes.new("ShaderNodeBump")
    micro_bump.name = "Aevrynd Secondary Micro Pore Normal R1082"
    micro_bump.inputs["Strength"].default_value = micro_strength
    micro_bump.inputs["Distance"].default_value = 0.000014
    links.new(coords.outputs["Object"], micro_noise.inputs["Vector"])
    links.new(micro_noise.outputs["Fac"], micro_bump.inputs["Height"])
    links.new(existing_bump.outputs["Normal"], micro_bump.inputs["Normal"])
    links.new(micro_bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Subsurface Weight"].default_value = 0.050
    shader.inputs["Subsurface Scale"].default_value = 0.0042
    shader.inputs["Coat Roughness"].default_value = 0.45
    material["aevrynd_revision"] = "v249r1082-regional-skin"
    material["aevrynd_layers"] = "regional complexion | t-zone/cheek roughness | primary pores | secondary micro pores"
    body.data.materials[0] = material
    return {"material": material.name, "nodeCount": len(nodes), "macroMottleScale": 34.0, "macroMottleContrast": macro_contrast, "fineMottleScale": fine_scale, "fineMottleContrast": fine_contrast, "primaryPoreStrength": pore_strength, "microPoreStrength": micro_strength, "subsurfaceWeight": 0.05, "subsurfaceScaleM": 0.0042}


def large_hair(scene, hidden):
    for obj in scene.objects:
        name = obj.name.lower()
        is_hair = obj.type == "CURVES" or any(token in name for token in ("gradedhairlinegroom", "targetscalp", "haircard", "hairfiber"))
        is_face_fiber = "brow" in name or "lash" in name
        if is_hair and not is_face_fiber:
            obj.hide_render = hidden


def render(scene, label, view):
    camera = scene.camera
    if view == "head-front":
        large_hair(scene, False); camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.035, 1.445), 88, (1000, 1000)
    elif view == "head-three-quarter":
        large_hair(scene, False); camera.location, target, camera.data.lens, size = (0.44, -0.62, 1.46), (0.0, -0.025, 1.445), 88, (1000, 1000)
    elif view == "skin-front":
        large_hair(scene, True); camera.location, target, camera.data.lens, size = (0.0, -0.52, 1.455), (0.0, -0.075, 1.455), 112, (1200, 1000)
    elif view == "skin-oblique":
        large_hair(scene, True); camera.location, target, camera.data.lens, size = (0.30, -0.48, 1.47), (0.0, -0.055, 1.455), 108, (1200, 1000)
    else:
        large_hair(scene, True); camera.location, target, camera.data.lens, size = (-0.30, -0.48, 1.47), (0.0, -0.055, 1.455), 108, (1200, 1000)
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, color_strength, rough_strength, pore_strength, micro_strength, fine_scale, macro_contrast, fine_contrast in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    body = bpy.data.objects[BODY]
    before = {"objects": len(bpy.data.objects), "materialSlots": len(body.data.materials), "vertices": len(body.data.vertices), "faces": len(body.data.polygons), "shapeKeys": len(body.data.shape_keys.key_blocks), "nodes": len(body.data.materials[0].node_tree.nodes)}
    if label == "a-control":
        attributes = None
        material = {"material": body.data.materials[0].name, "nodeCount": before["nodes"], "macroMottleScale": 34.0, "macroMottleContrast": macro_contrast, "fineMottleScale": fine_scale, "fineMottleContrast": fine_contrast, "primaryPoreStrength": 0.045, "microPoreStrength": 0.0, "subsurfaceWeight": 0.045, "subsurfaceScaleM": 0.0045}
    else:
        attributes = create_region_attributes(body, color_strength, rough_strength)
        material = tune_material(body, label, color_strength, rough_strength, pore_strength, micro_strength, fine_scale, macro_contrast, fine_contrast)
    renders = [render(scene, label, view) for view in ("head-front", "head-three-quarter", "skin-front", "skin-oblique", "skin-opposite")]
    large_hair(scene, False)
    after = {"objects": len(bpy.data.objects), "materialSlots": len(body.data.materials), "vertices": len(body.data.vertices), "faces": len(body.data.polygons), "shapeKeys": len(body.data.shape_keys.key_blocks), "nodes": len(body.data.materials[0].node_tree.nodes)}
    variants.append({"label": label, "colorStrength": color_strength, "roughnessStrength": rough_strength, "attributes": attributes, "material": material, "before": before, "after": after, "renders": renders, "status": "VISUAL_REVIEW_REQUIRED"})
    if label == SELECTED:
        body["aevrynd_skin_revision"] = "v249r1082-regional-skin"
        body["aevrynd_skin_layers"] = "regional complexion | t-zone/cheek roughness | primary pores | secondary micro pores"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1082-regional-skin-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "preserve the r1074 lip/commissure chain, then add explicit point-domain complexion and regional roughness layers plus a chained second micro-pore normal inside the existing skin material",
    "variants": variants,
    "selectedVariant": SELECTED,
    "geometryChanged": False,
    "newObjects": 0,
    "materialSlotDelta": 0,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1082_REGIONAL_SKIN=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "attributes": item["attributes"], "material": item["material"]} for item in variants]}, sort_keys=True))
