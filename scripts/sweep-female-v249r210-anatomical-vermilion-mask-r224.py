import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r224-anatomical-vermilion-mask-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-vermilion-mask-r224.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
TARGET_COLOR = (0.42, 0.105, 0.085, 1.0)
VARIANTS = (("a-control", 0.0), ("b-natural", 0.24), ("c-balanced", 0.38), ("d-strong", 0.58))


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def anatomical_mask(p):
    ax = abs(p.x)
    if ax >= 0.046 or p.y >= -0.104 or not (1.516 < p.z < 1.544):
        return 0.0, "none"
    width = 1.0 - smoothstep(0.030, 0.045, ax)
    front = 1.0 - smoothstep(-0.120, -0.104, p.y)
    slit = 1.5295
    corner = smoothstep(0.026, 0.044, ax)
    cupid_peak = 0.0015 * gaussian(ax, 0.0115, 0.0052)
    center_notch = 0.00065 * gaussian(ax, 0.0, 0.0048)
    upper_top = (1.5370 + cupid_peak - center_notch) * (1.0 - corner) + 1.5302 * corner
    lower_bottom = 1.5200 * (1.0 - corner) + 1.5283 * corner
    upper = smoothstep(slit - 0.0003, slit + 0.0009, p.z) * (1.0 - smoothstep(upper_top - 0.0012, upper_top + 0.0004, p.z))
    lower = smoothstep(lower_bottom - 0.0005, lower_bottom + 0.0012, p.z) * (1.0 - smoothstep(slit - 0.0008, slit + 0.0003, p.z))
    if upper >= lower:
        return width * front * upper, "upper"
    return width * front * lower, "lower"


def build_field(body, strength):
    name = "AevryndAnatomicalVermilionMaskR224"
    old = body.data.color_attributes.get(name)
    if old:
        body.data.color_attributes.remove(old)
    field = body.data.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    counts = {"upper": 0, "lower": 0}
    maxima = {"upper": 0.0, "lower": 0.0}
    for index, vertex in enumerate(mesh.vertices):
        p = evaluated.matrix_world @ vertex.co
        mask, region = anatomical_mask(p)
        factor = mask * strength
        field.data[index].color = (factor, factor, factor, 1.0)
        if region != "none" and factor > 0.002:
            counts[region] += 1
            maxima[region] = max(maxima[region], factor)
    evaluated.to_mesh_clear()
    return field, {"verticesTinted": counts, "maximumMixFactor": maxima}


def tune_material(body, strength, label):
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_AnatomicalVermilion_R224_{label}"
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
    color.name = "Aevrynd Anatomical Vermilion Field R224"
    color.layer_name = field.name
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Anatomical Vermilion Mix R224"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = TARGET_COLOR
    links.new(color.outputs["Color"], mix.inputs[0])
    links.new(source, mix.inputs[1])
    links.new(mix.outputs["Color"], base)
    material["aevrynd_skin_revision"] = "v249r224-sweep"
    material["aevrynd_vermilion_variant"] = label
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
report = {"source": str(SOURCE), "targetColorLinear": TARGET_COLOR, "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
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
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R224_ANATOMICAL_VERMILION=" + json.dumps(report, sort_keys=True))
