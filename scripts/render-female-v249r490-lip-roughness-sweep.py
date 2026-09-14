import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-upper-lip-form-r489.blend"
OUT = ASSETS / "reviews/v249r490-lip-roughness-sweep"
REPORT = ASSETS / "female-v249-mainline-lip-roughness-r490.study.json"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-lip-response-r490.blend"
BODY = "AevryndFemaleBodyBaseV118"
BASE_ROUGHNESS = 0.52
TARGETS = (0.52, 0.46, 0.40, 0.34)
SELECTED_TARGET = 0.46


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def variant(target_roughness):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_LipRoughness_R490_{target_roughness:.2f}"
    body.data.materials.clear()
    body.data.materials.append(material)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")

    upper = nodes.new("ShaderNodeAttribute")
    upper.name = "Aevrynd Lip Roughness Upper Mask R490"
    upper.attribute_name = "AevryndVermilionPlaneR484_c-defined-280"
    lower = nodes.new("ShaderNodeAttribute")
    lower.name = "Aevrynd Lip Roughness Lower Mask R490"
    lower.attribute_name = "AevryndLowerVermilionR475"
    normalize_upper = nodes.new("ShaderNodeMath")
    normalize_upper.name = "Aevrynd Lip Roughness Upper Normalize R490"
    normalize_upper.operation = "MULTIPLY"
    normalize_upper.inputs[1].default_value = 1.0 / 0.34
    normalize_upper.use_clamp = True
    normalize_lower = nodes.new("ShaderNodeMath")
    normalize_lower.name = "Aevrynd Lip Roughness Lower Normalize R490"
    normalize_lower.operation = "MULTIPLY"
    normalize_lower.inputs[1].default_value = 10.0
    normalize_lower.use_clamp = True
    maximum = nodes.new("ShaderNodeMath")
    maximum.name = "Aevrynd Lip Roughness Mask R490"
    maximum.operation = "MAXIMUM"
    maximum.use_clamp = True
    scale = nodes.new("ShaderNodeMath")
    scale.name = "Aevrynd Lip Roughness Delta R490"
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = target_roughness - BASE_ROUGHNESS
    add = nodes.new("ShaderNodeMath")
    add.name = "Aevrynd Lip Roughness R490"
    add.operation = "ADD"
    add.inputs[1].default_value = BASE_ROUGHNESS
    add.use_clamp = True
    links.new(upper.outputs["Color"], normalize_upper.inputs[0])
    links.new(lower.outputs["Color"], normalize_lower.inputs[0])
    links.new(normalize_upper.outputs[0], maximum.inputs[0])
    links.new(normalize_lower.outputs[0], maximum.inputs[1])
    links.new(maximum.outputs[0], scale.inputs[0])
    links.new(scale.outputs[0], add.inputs[0])
    links.new(add.outputs[0], shader.inputs["Roughness"])

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    tag = f"r{target_roughness:.2f}"
    views = (
        ("mouth", (0, -0.405, 1.528), (0, -0.115, 1.528), 135, (1400, 800)),
        ("oblique", (0.235, -0.405, 1.530), (0, -0.112, 1.528), 135, (1400, 800)),
        ("face", (0, -0.560, 1.585), (0, -0.060, 1.585), 108, (1100, 1100)),
    )
    for name, location, target, lens, size in views:
        render(scene, camera, f"{tag}-{name}-f01", location, target, lens, size)
    if target_roughness == SELECTED_TARGET:
        scene.frame_set(1)
        scene["aevrynd_revision"] = "v249r490-lip-response"
        scene["aevrynd_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
        body["aevrynd_lip_roughness"] = target_roughness
        body["aevrynd_lip_roughness_mask"] = "normalized upper/lower vermilion attributes"
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    return {
        "lipRoughness": target_roughness,
        "skinRoughness": BASE_ROUGHNESS,
        "baseColorChanged": False,
        "geometryChanged": False,
    }


OUT.mkdir(parents=True, exist_ok=True)
results = [variant(target) for target in TARGETS]
report = {
    "revision": "v249r490-study",
    "source": str(SOURCE),
    "method": "normalized upper/lower vermilion masks drive localized Principled roughness",
    "variants": results,
    "selectedLipRoughness": SELECTED_TARGET,
    "rejectedTargets": {"0.40": "too glossy in macro view", "0.34": "plastic/wet highlight"},
    "output": str(OUTPUT),
    "reviewDirectory": str(OUT),
    "status": "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R490_LIP_ROUGHNESS=" + json.dumps(report, sort_keys=True))
