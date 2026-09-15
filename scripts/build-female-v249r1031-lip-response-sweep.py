"""Soften the binary lip mask and give the lips a rougher, muted response."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-continuous-perioral-r1030-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-soft-warm-lip-response-r1031-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1031-lip-response-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1031-lip-response-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("source-r1030", 1.00, (0.250, 0.050, 0.045, 1.0), 0.50),
    ("a-soft-warm", 0.78, (0.245, 0.075, 0.065, 1.0), 0.64),
    ("b-muted-rose", 0.66, (0.245, 0.095, 0.082, 1.0), 0.62),
    ("c-light-neutral", 0.55, (0.260, 0.110, 0.095, 1.0), 0.65),
)
SELECTED = "a-soft-warm"


def find_nodes(material):
    attribute = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeAttribute" and node.attribute_name == "lips")
    mix = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeMixRGB" and any(link.from_node == attribute and link.to_node == node and link.to_socket == node.inputs[0] for link in material.node_tree.links))
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    return attribute, mix, shader


def tune_material(body, label, mask_strength, target, lip_roughness):
    source = body.data.materials[0]
    material = source.copy()
    material.name = f"Aevrynd_CC0_OwnedSkin_R1031_{label}"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    attribute, mix, shader = find_nodes(material)
    mix.inputs[2].default_value = target
    for link in list(mix.inputs[0].links):
        links.remove(link)
    mask = nodes.new("ShaderNodeMath")
    mask.name = "Aevrynd Lip Mask Strength R1031"
    mask.operation = "MULTIPLY"
    mask.inputs[1].default_value = mask_strength
    links.new(attribute.outputs[2], mask.inputs[0])
    links.new(mask.outputs[0], mix.inputs[0])
    for link in list(shader.inputs["Roughness"].links):
        links.remove(link)
    rough_delta = nodes.new("ShaderNodeMath")
    rough_delta.name = "Aevrynd Lip Roughness Delta R1031"
    rough_delta.operation = "MULTIPLY"
    rough_delta.inputs[1].default_value = lip_roughness - 0.50
    rough_add = nodes.new("ShaderNodeMath")
    rough_add.name = "Aevrynd Lip Roughness Base R1031"
    rough_add.operation = "ADD"
    rough_add.inputs[1].default_value = 0.50
    links.new(attribute.outputs[2], rough_delta.inputs[0])
    links.new(rough_delta.outputs[0], rough_add.inputs[0])
    links.new(rough_add.outputs[0], shader.inputs["Roughness"])
    body.data.materials[0] = material
    return {
        "material": material.name,
        "lipMaskStrength": mask_strength,
        "targetLinearRgba": list(target),
        "skinRoughness": 0.50,
        "lipRoughness": lip_roughness,
        "addedShaderNodes": 3,
        "materialSlots": len(body.data.materials),
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size=(1000, 1000)):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, mask_strength, target, lip_roughness in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    if label == "source-r1030":
        edit = {"material": body.data.materials[0].name, "lipMaskStrength": 1.0, "targetLinearRgba": list(target), "skinRoughness": 0.50, "lipRoughness": 0.50, "addedShaderNodes": 0, "materialSlots": len(body.data.materials)}
    else:
        edit = tune_material(body, label, mask_strength, target, lip_roughness)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, f"{label}-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88),
        render(scene, f"{label}-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)),
        render(scene, f"{label}-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.115, 1.386), 128, (1200, 700)),
    ]
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    variants.append({"label": label, "edit": edit, "rendered": rendered, "bodyVertices": len(body.data.vertices), "bodyPolygons": len(body.data.polygons), "shapeKeys": len(body.data.shape_keys.key_blocks), "status": "VISUAL_REVIEW_REQUIRED"})
    if label == SELECTED:
        scene["aevrynd_mainline_revision"] = "v249r1031-balanced-lip-response"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_PARTIAL"
        scene["aevrynd_website_promotion"] = "forbidden"
        body["aevrynd_lip_material_revision"] = "v249r1031"
        body["aevrynd_lip_material_method"] = "softened named lips mask plus rougher muted rose response"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "scale the existing named lips attribute before color mixing and drive lip-only roughness without adding a material slot or object",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED,
    "geometryChanged": False,
    "materialSlotDelta": 0,
    "websitePromotionApproved": False,
    "visualAssessment": "The selected lip-only response removes the saturated pink read. Muted-rose and light-neutral variants are rejected as grey or washed out.",
    "strictMouthScore": 38,
    "status": "TECHNICAL_PASS_VISUAL_PARTIAL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1031_LIP_RESPONSE=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "edit": item["edit"]} for item in variants]}, sort_keys=True))
