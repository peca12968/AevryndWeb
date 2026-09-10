import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r223-integrated-lip-mix-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-lip-mix-r223.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
TARGET_COLOR = (0.35, 0.055, 0.045, 1.0)
VARIANTS = (
    ("a-control", 0.0),
    ("b-natural", 0.35),
    ("c-balanced", 0.55),
    ("d-strong", 0.80),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def build_field(body, strength):
    name = "AevryndIntegratedLipMixR223"
    old = body.data.color_attributes.get(name)
    if old:
        body.data.color_attributes.remove(old)
    field = body.data.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    changed = 0
    maximum = 0.0
    for index, vertex in enumerate(mesh.vertices):
        p = evaluated.matrix_world @ vertex.co
        ax = abs(p.x)
        front = gaussian(p.y, -0.130, 0.0105)
        width = gaussian(ax, 0.0, 0.030)
        upper = gaussian(p.z, 1.5330, 0.0046)
        lower = gaussian(p.z, 1.5243, 0.0049)
        anatomical_mask = width * front * max(upper, lower)
        anatomical_mask = max(0.0, min(1.0, (anatomical_mask - 0.14) / 0.68))
        factor = anatomical_mask * strength
        field.data[index].color = (factor, factor, factor, 1.0)
        if factor > 0.002:
            changed += 1
            maximum = max(maximum, factor)
    evaluated.to_mesh_clear()
    return field, {"verticesTinted": changed, "maximumMixFactor": maximum}


def tune_material(body, strength, label):
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_IntegratedLipMix_R223_{label}"
    body.data.materials.clear()
    body.data.materials.append(material)
    field, metrics = build_field(body, strength)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    source = base.links[0].from_socket
    for link in list(base.links):
        links.remove(link)
    color = nodes.new("ShaderNodeVertexColor")
    color.name = "Aevrynd Integrated Lip Mix Field R223"
    color.layer_name = field.name
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Integrated Lip Target Mix R223"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = TARGET_COLOR
    links.new(color.outputs["Color"], mix.inputs[0])
    links.new(source, mix.inputs[1])
    links.new(mix.outputs["Color"], base)
    material["aevrynd_skin_revision"] = "v249r223-sweep"
    material["aevrynd_lip_mix_variant"] = label
    return material.name, metrics


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {
    "source": str(SOURCE),
    "targetColorLinear": TARGET_COLOR,
    "variants": {},
    "status": "VISUAL_SELECTION_PENDING",
}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    body = bpy.data.objects[BODY]
    metrics = {"mixStrength": strength, "material": body.active_material.name}
    if strength:
        metrics["material"], field_metrics = tune_material(body, strength, label)
        metrics.update(field_metrics)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
        ("02-mouth-close", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760)),
        ("03-three-quarter", (0.45, -0.62, 1.58), (0.0, -0.015, 1.565), 92, (1000, 1000)),
        ("04-profile", (0.70, -0.03, 1.57), (0.0, -0.010, 1.555), 96, (1000, 1000)),
    )
    for view_name, location, aim, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, aim, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R223_INTEGRATED_LIP_MIX=" + json.dumps(report, sort_keys=True))
